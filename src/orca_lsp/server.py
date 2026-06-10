"""ORCA Language Server Protocol implementation"""

import re
from typing import TYPE_CHECKING, List, Optional

from lsprotocol.types import (
    CodeAction,
    CodeActionParams,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    DefinitionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    DocumentFormattingParams,
    DocumentRangeFormattingParams,
    Hover,
    HoverParams,
    Location,
    Position,
    Range,
    ReferenceParams,
    TextEdit,
)
from pygls.server import LanguageServer

if TYPE_CHECKING:
    from pygls.workspace import TextDocument

from . import __version__
from .features.code_actions import CodeActionProvider
from .features.diagnostic import DiagnosticProvider
from .features.formatting import FormattingProvider
from .features.lint import LintProvider
from .features.navigation import (
    DefinitionProvider,
    HoverProvider,
    ReferencesProvider,
)
from .features.typecheck import TypecheckProvider
from .keywords import (
    BASIS_SETS,
    DFT_FUNCTIONALS,
    ELEMENTS,
    JOB_TYPES,
    PERCENT_BLOCKS,
    WAVEFUNCTION_METHODS,
)
from .parser import ORCAParser

# Pre-sorted elements for completions (avoid sorting on every request)
_SORTED_ELEMENTS = tuple(sorted(ELEMENTS))

# Named constants for diagnostic ranges (replaces magic numbers)
_DIAGNOSTIC_LINE_START_CHARACTER = 0
_DIAGNOSTIC_LINE_END_CHARACTER = 100

# Regex for extracting %block name from a line (O(1) lookup vs O(n*m) loop)
_PERCENT_BLOCK_NAME_RE = re.compile(r"%\s*(\w+)", re.IGNORECASE)


class ORCALanguageServer(LanguageServer):
    """ORCA Language Server"""

    def __init__(self, parser: Optional[ORCAParser] = None) -> None:
        super().__init__("orca-lsp", __version__)
        self.parser = parser if parser is not None else ORCAParser()
        self.diagnostic_provider = DiagnosticProvider(self.parser)
        self.formatting_provider = FormattingProvider(self)
        self.lint_provider = LintProvider(self.parser)
        self.code_action_provider = CodeActionProvider(self.parser)
        self.definition_provider = DefinitionProvider(self.parser)
        self.hover_provider = HoverProvider(self.parser)
        self.references_provider = ReferencesProvider(self.parser)
        self.typecheck_provider = TypecheckProvider(self.parser)
        self._setup_features()

    def _setup_features(self) -> None:
        """Setup LSP features"""

        @self.feature("textDocument/completion")
        def on_completion(params: CompletionParams) -> Optional[CompletionList]:
            return self._on_completion(params)  # pragma: no cover

        @self.feature("textDocument/hover")
        def on_hover(params: HoverParams) -> Optional[Hover]:
            return self._on_hover(params)  # pragma: no cover

        @self.feature("textDocument/definition")
        def on_definition(params: DefinitionParams) -> Optional[Location]:
            return self._on_definition(params)  # pragma: no cover

        @self.feature("textDocument/references")
        def on_references(params: ReferenceParams) -> List[Location]:
            return self._on_references(params)  # pragma: no cover

        @self.feature("textDocument/codeAction")
        def on_code_action(params: CodeActionParams) -> List[CodeAction]:
            return self._on_code_action(params)  # pragma: no cover

        @self.feature("textDocument/didOpen")
        def on_did_open(params: DidOpenTextDocumentParams) -> None:
            self._on_did_open(params)  # pragma: no cover

        @self.feature("textDocument/didChange")
        def on_did_change(params: DidChangeTextDocumentParams) -> None:
            self._on_did_change(params)  # pragma: no cover

        @self.feature("textDocument/formatting")
        def on_formatting(params: DocumentFormattingParams) -> List[TextEdit]:
            return self._on_formatting(params)  # pragma: no cover

        @self.feature("textDocument/rangeFormatting")
        def on_range_formatting(
            params: DocumentRangeFormattingParams,
        ) -> List[TextEdit]:
            return self._on_range_formatting(params)  # pragma: no cover

    def _on_completion(self, params: CompletionParams) -> Optional[CompletionList]:
        """Handle completion requests"""
        document = self.workspace.get_text_document(params.text_document.uri)
        line = document.lines[params.position.line]

        # Determine context
        completions = self._get_completions(line, params.position)

        return CompletionList(is_incomplete=False, items=completions)

    def _get_completions(self, line: str, position: Position) -> List[CompletionItem]:
        """Get completions based on context"""
        completions: List[CompletionItem] = []

        stripped = line[: position.character].strip()

        # % block completion
        if stripped.startswith("%"):
            completions.extend(self._get_percent_completions(stripped))

        # Simple input line completion
        elif stripped.startswith("!"):
            completions.extend(self._get_method_completions())
            completions.extend(self._get_basis_completions())
            completions.extend(self._get_job_completions())

        # Geometry section - element completion
        elif self._in_geometry_section(line):
            completions.extend(self._get_element_completions())

        return completions

    def _get_percent_completions(self, line: str) -> List[CompletionItem]:
        """Get % block completions"""
        completions: List[CompletionItem] = []

        # Check if we're completing the block name
        match = re.match(r"%\s*(\w*)$", line)
        if match:
            for name, info in PERCENT_BLOCKS.items():
                completions.append(
                    CompletionItem(
                        label=name,
                        kind=CompletionItemKind.Keyword,
                        detail=info.get("description", ""),
                        documentation=f"Example: {info.get('example', '')}",
                        insert_text=f"{name} ",
                    )
                )

        # Check if we're in a specific block - use regex to extract block name directly
        # More efficient than looping through all block names
        match = _PERCENT_BLOCK_NAME_RE.match(line)
        if match:
            block_name = match.group(1).lower()
            if block_name in PERCENT_BLOCKS:
                completions.extend(self._get_block_specific_completions(block_name))

        return completions

    def _get_block_specific_completions(self, block_name: str) -> List[CompletionItem]:
        """Get completions for specific % block parameters"""
        completions: List[CompletionItem] = []

        if block_name == "maxcore":
            for mem in ["1000", "2000", "4000", "8000", "16000"]:
                completions.append(
                    CompletionItem(
                        label=f"{mem} MB",
                        kind=CompletionItemKind.Value,
                        insert_text=mem,
                    )
                )

        elif block_name == "pal":
            completions.append(
                CompletionItem(
                    label="nprocs",
                    kind=CompletionItemKind.Property,
                    insert_text="nprocs ",
                )
            )

        elif block_name == "method":
            for disp in ["D3", "D3BJ", "D4"]:
                completions.append(
                    CompletionItem(
                        label=disp,
                        kind=CompletionItemKind.Value,
                        insert_text=disp,
                    )
                )

        elif block_name == "scf":
            for opt in ["maxiter", "convergence", "NRMaxIt"]:
                completions.append(
                    CompletionItem(
                        label=opt,
                        kind=CompletionItemKind.Property,
                        insert_text=f"{opt} ",
                    )
                )

        return completions

    @staticmethod
    def _create_completions(
        items: dict, kind: CompletionItemKind, detail_key: str
    ) -> List[CompletionItem]:
        """Create completion items from a keyword dictionary.

        Args:
            items: Mapping of keyword name to info dict.
            kind: The CompletionItemKind for all items.
            detail_key: Key in the info dict for the detail text, or a literal
                        string used when the info dict has no such key.
        """
        completions: List[CompletionItem] = []
        for name, info in items.items():
            detail = info.get(detail_key, detail_key)
            completions.append(
                CompletionItem(
                    label=name,
                    kind=kind,
                    detail=detail,
                    documentation=info.get("description", ""),
                )
            )
        return completions

    def _get_method_completions(self) -> List[CompletionItem]:
        """Get method completions"""
        completions = self._create_completions(DFT_FUNCTIONALS, CompletionItemKind.Function, "type")
        # Prefix DFT details for clarity
        for item in completions:
            if item.detail:
                item.detail = f"DFT: {item.detail}"
        completions.extend(
            self._create_completions(WAVEFUNCTION_METHODS, CompletionItemKind.Method, "type")
        )
        # Wavefunction methods get a fixed detail label
        wavefunction_start = len(completions) - len(WAVEFUNCTION_METHODS)
        for item in completions[wavefunction_start:]:
            item.detail = "Wavefunction method"
        return completions

    def _get_basis_completions(self) -> List[CompletionItem]:
        """Get basis set completions"""
        return self._create_completions(BASIS_SETS, CompletionItemKind.Class, "type")

    def _get_job_completions(self) -> List[CompletionItem]:
        """Get job type completions"""
        return self._create_completions(JOB_TYPES, CompletionItemKind.Event, "type")

    def _get_element_completions(self) -> List[CompletionItem]:
        """Get element symbol completions for geometry"""
        return [
            CompletionItem(
                label=element,
                kind=CompletionItemKind.EnumMember,
                detail=f"Element {element}",
            )
            for element in _SORTED_ELEMENTS
        ]

    def _in_geometry_section(self, line: str) -> bool:
        """Check if we're in a geometry section"""
        # This is a simplified check
        return bool(re.match(r"^[A-Z][a-z]?\s+[-\d\.]", line.strip()))

    def _on_hover(self, params: HoverParams) -> Optional[Hover]:
        """Handle hover requests via the shared HoverProvider."""
        document = self.workspace.get_text_document(params.text_document.uri)
        return self.hover_provider.get_hover(document.source, params.position)

    def _on_definition(self, params: DefinitionParams) -> Optional[Location]:
        """Handle go-to-definition requests via the shared DefinitionProvider."""
        document = self.workspace.get_text_document(params.text_document.uri)
        return self.definition_provider.get_definition(document.source, params.position)

    def _on_references(self, params: ReferenceParams) -> List[Location]:
        """Handle find-references requests via the shared ReferencesProvider."""
        document = self.workspace.get_text_document(params.text_document.uri)
        return self.references_provider.get_references(
            document.source,
            params.text_document.uri,
            params.position,
            include_declaration=params.context.include_declaration,
        )

    def _get_word_at_position(self, document: "TextDocument", position: Position) -> str:
        """Get the word at the given position"""
        line = document.lines[position.line]

        # Find word boundaries
        start = position.character
        while start > 0 and line[start - 1].isalnum():
            start -= 1

        end = position.character
        while end < len(line) and line[end].isalnum():
            end += 1

        return str(line[start:end])

    @staticmethod
    def _create_diagnostic(item: dict, severity: DiagnosticSeverity) -> Diagnostic:
        """Create an LSP Diagnostic from a parsed error/warning item."""
        line = item.get("line", 0)
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=_DIAGNOSTIC_LINE_START_CHARACTER),
                end=Position(line=line, character=_DIAGNOSTIC_LINE_END_CHARACTER),
            ),
            message=item.get("message", ""),
            severity=severity,
            source="orca-lsp",
        )

    def _validate_document(self, uri: str) -> None:
        """Validate a document and publish diagnostics"""
        document = self.workspace.get_text_document(uri)
        content = document.source

        # Use the DiagnosticProvider for consistent diagnostics
        diagnostics = self.diagnostic_provider.get_diagnostics(content)

        # Merge lint diagnostics (schema-aware static checks)
        diagnostics.extend(self.lint_provider.lint(content))

        # Merge typecheck diagnostics (value types, enums, units, required sections)
        diagnostics.extend(self.typecheck_provider.typecheck(content))

        # Publish diagnostics
        self.publish_diagnostics(uri, diagnostics)

    def _on_code_action(self, params: CodeActionParams) -> List[CodeAction]:
        """Handle code action requests"""
        document = self.workspace.get_text_document(params.text_document.uri)
        source = document.source

        # Delegate to the CodeActionProvider
        actions = self.code_action_provider.get_code_actions(
            source,
            params.context.diagnostics,
        )

        # Rewrite document URI into workspace edit changes (the provider uses
        # the placeholder key "document" for testability).
        uri = params.text_document.uri
        for action in actions:
            if action.edit and action.edit.changes:
                new_changes: dict = {}
                for change_uri, edits in action.edit.changes.items():
                    target_uri = uri if change_uri == "document" else change_uri
                    new_changes[target_uri] = edits
                action.edit.changes = new_changes

        return actions

    def _on_formatting(self, params: DocumentFormattingParams) -> List[TextEdit]:
        """Handle document formatting requests."""
        document = self.workspace.get_text_document(params.text_document.uri)
        return self.formatting_provider.format_document(document.source, params)

    def _on_range_formatting(self, params: DocumentRangeFormattingParams) -> List[TextEdit]:
        """Handle range formatting requests."""
        document = self.workspace.get_text_document(params.text_document.uri)
        return self.formatting_provider.format_range(document.source, params)

    def _on_did_open(self, params: DidOpenTextDocumentParams) -> None:
        """Handle document open"""
        self._validate_document(params.text_document.uri)

    def _on_did_change(self, params: DidChangeTextDocumentParams) -> None:
        """Handle document change"""
        self._validate_document(params.text_document.uri)


def main() -> None:
    """Main entry point"""
    server = ORCALanguageServer()
    server.start_io()


if __name__ == "__main__":
    main()
