"""ORCA Language Server Protocol implementation"""

import asyncio
import re
from typing import List, Optional, Any

from pygls.server import LanguageServer
from lsprotocol.types import (
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    CompletionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
    TextEdit,
    CodeAction,
    CodeActionKind,
    CodeActionParams,
    Command,
    WorkspaceEdit,
)

from .parser import ORCAParser
from .keywords import (
    DFT_FUNCTIONALS,
    WAVEFUNCTION_METHODS,
    BASIS_SETS,
    JOB_TYPES,
    PERCENT_BLOCKS,
    ELEMENTS,
)


class ORCALanguageServer(LanguageServer):
    """ORCA Language Server"""
    
    def __init__(self):
        super().__init__("orca-lsp", "0.1.0")
        self.parser = ORCAParser()
        self._setup_features()
    
    def _setup_features(self):
        """Setup LSP features"""
        self.feature("textDocument/completion")(self._on_completion)
        self.feature("textDocument/hover")(self._on_hover)
        self.feature("textDocument/diagnostic")(self._on_diagnostic)
        self.feature("textDocument/codeAction")(self._on_code_action)
        self.feature("textDocument/didOpen")(self._on_did_open)
        self.feature("textDocument/didChange")(self._on_did_change)
    
    def _on_completion(self, params: CompletionParams) -> Optional[CompletionList]:
        """Handle completion requests"""
        document = self.workspace.get_text_document(params.text_document.uri)
        line = document.lines[params.position.line]
        
        # Determine context
        completions = self._get_completions(line, params.position)
        
        return CompletionList(
            is_incomplete=False,
            items=completions
        )
    
    def _get_completions(self, line: str, position: Position) -> List[CompletionItem]:
        """Get completions based on context"""
        completions = []
        
        stripped = line[:position.character].strip()
        
        # % block completion
        if stripped.startswith('%'):
            completions.extend(self._get_percent_completions(stripped))
        
        # Simple input line completion
        elif stripped.startswith('!'):
            completions.extend(self._get_method_completions())
            completions.extend(self._get_basis_completions())
            completions.extend(self._get_job_completions())
        
        # Geometry section - element completion
        elif self._in_geometry_section(line):
            completions.extend(self._get_element_completions())
        
        return completions
    
    def _get_percent_completions(self, line: str) -> List[CompletionItem]:
        """Get % block completions"""
        completions = []
        
        # Check if we're completing the block name
        match = re.match(r'%\s*(\w*)$', line)
        if match:
            for name, info in PERCENT_BLOCKS.items():
                completions.append(CompletionItem(
                    label=name,
                    kind=CompletionItemKind.Keyword,
                    detail=info.get('description', ''),
                    documentation=f"Example: {info.get('example', '')}",
                    insert_text=f"{name} ",
                ))
        
        # Check if we're in a specific block
        for name in PERCENT_BLOCKS.keys():
            if f'%{name}' in line.lower():
                completions.extend(self._get_block_specific_completions(name))
        
        return completions
    
    def _get_block_specific_completions(self, block_name: str) -> List[CompletionItem]:
        """Get completions for specific % block parameters"""
        completions = []
        
        if block_name == 'maxcore':
            for mem in ['1000', '2000', '4000', '8000', '16000']:
                completions.append(CompletionItem(
                    label=f"{mem} MB",
                    kind=CompletionItemKind.Value,
                    insert_text=mem,
                ))
        
        elif block_name == 'pal':
            completions.append(CompletionItem(
                label="nprocs",
                kind=CompletionItemKind.Property,
                insert_text="nprocs ",
            ))
        
        elif block_name == 'method':
            for disp in ['D3', 'D3BJ', 'D4']:
                completions.append(CompletionItem(
                    label=disp,
                    kind=CompletionItemKind.Value,
                    insert_text=disp,
                ))
        
        elif block_name == 'scf':
            for opt in ['maxiter', 'convergence', 'NRMaxIt']:
                completions.append(CompletionItem(
                    label=opt,
                    kind=CompletionItemKind.Property,
                    insert_text=f"{opt} ",
                ))
        
        return completions
    
    def _get_method_completions(self) -> List[CompletionItem]:
        """Get method completions"""
        completions = []
        
        # DFT functionals
        for name, info in DFT_FUNCTIONALS.items():
            completions.append(CompletionItem(
                label=name,
                kind=CompletionItemKind.Function,
                detail=f"DFT: {info.get('type', '')}",
                documentation=info.get('description', ''),
            ))
        
        # Wavefunction methods
        for name, info in WAVEFUNCTION_METHODS.items():
            completions.append(CompletionItem(
                label=name,
                kind=CompletionItemKind.Method,
                detail="Wavefunction method",
                documentation=info.get('description', ''),
            ))
        
        return completions
    
    def _get_basis_completions(self) -> List[CompletionItem]:
        """Get basis set completions"""
        completions = []
        
        for name, info in BASIS_SETS.items():
            completions.append(CompletionItem(
                label=name,
                kind=CompletionItemKind.Class,
                detail=info.get('type', ''),
                documentation=info.get('description', ''),
            ))
        
        return completions
    
    def _get_job_completions(self) -> List[CompletionItem]:
        """Get job type completions"""
        completions = []
        
        for name, info in JOB_TYPES.items():
            completions.append(CompletionItem(
                label=name,
                kind=CompletionItemKind.Event,
                detail="Job type",
                documentation=info.get('description', ''),
            ))
        
        return completions
    
    def _get_element_completions(self) -> List[CompletionItem]:
        """Get element symbol completions for geometry"""
        completions = []
        
        for element in sorted(ELEMENTS):
            completions.append(CompletionItem(
                label=element,
                kind=CompletionItemKind.EnumMember,
                detail=f"Element {element}",
            ))
        
        return completions
    
    def _in_geometry_section(self, line: str) -> bool:
        """Check if we're in a geometry section"""
        # This is a simplified check
        return bool(re.match(r'^[A-Z][a-z]?\s+[-\d\.]', line.strip()))
    
    def _on_hover(self, params: HoverParams) -> Optional[Hover]:
        """Handle hover requests"""
        document = self.workspace.get_text_document(params.text_document.uri)
        position = params.position
        
        # Get word at position
        word = self._get_word_at_position(document, position)
        if not word:
            return None
        
        # Look up documentation
        word_upper = word.upper()
        
        # Check methods
        if word_upper in DFT_FUNCTIONALS:
            info = DFT_FUNCTIONALS[word_upper]
            return Hover(contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=f"**{word}**\n\n{info.get('description', '')}\n\nType: {info.get('type', 'N/A')}"
            ))
        
        if word_upper in WAVEFUNCTION_METHODS:
            info = WAVEFUNCTION_METHODS[word_upper]
            return Hover(contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=f"**{word}**\n\n{info.get('description', '')}"
            ))
        
        # Check basis sets
        if word_upper in BASIS_SETS:
            info = BASIS_SETS[word_upper]
            return Hover(contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=f"**{word}**\n\n{info.get('description', '')}\n\nType: {info.get('type', 'N/A')}"
            ))
        
        # Check job types
        if word_upper in JOB_TYPES:
            info = JOB_TYPES[word_upper]
            return Hover(contents=MarkupContent(
                kind=MarkupKind.Markdown,
                value=f"**{word}**\n\n{info.get('description', '')}"
            ))
        
        return None
    
    def _get_word_at_position(self, document, position: Position) -> str:
        """Get the word at the given position"""
        line = document.lines[position.line]
        
        # Find word boundaries
        start = position.character
        while start > 0 and line[start - 1].isalnum():
            start -= 1
        
        end = position.character
        while end < len(line) and line[end].isalnum():
            end += 1
        
        return line[start:end]
    
    def _on_diagnostic(self, params) -> List[Diagnostic]:
        """Handle diagnostic requests"""
        # Diagnostics are handled via didOpen/didChange
        return []
    
    def _validate_document(self, uri: str):
        """Validate a document and publish diagnostics"""
        document = self.workspace.get_text_document(uri)
        content = document.source
        
        # Parse the document
        result = self.parser.parse(content)
        
        # Convert to LSP diagnostics
        diagnostics = []
        
        for error in result.errors:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=error.get('line', 0), character=0),
                    end=Position(line=error.get('line', 0), character=100)
                ),
                message=error.get('message', ''),
                severity=DiagnosticSeverity.Error,
                source="orca-lsp"
            ))
        
        for warning in result.warnings:
            diagnostics.append(Diagnostic(
                range=Range(
                    start=Position(line=warning.get('line', 0), character=0),
                    end=Position(line=warning.get('line', 0), character=100)
                ),
                message=warning.get('message', ''),
                severity=DiagnosticSeverity.Warning,
                source="orca-lsp"
            ))
        
        # Publish diagnostics
        self.publish_diagnostics(uri, diagnostics)
    
    def _on_code_action(self, params: CodeActionParams) -> List[CodeAction]:
        """Handle code action requests"""
        actions = []
        document = self.workspace.get_text_document(params.text_document.uri)
        
        # Get diagnostics at this range
        for diagnostic in params.context.diagnostics:
            # Add maxcore quick fix
            if "Missing %maxcore" in diagnostic.message:
                action = CodeAction(
                    title="Add %maxcore 4000",
                    kind=CodeActionKind.QuickFix,
                    edit=WorkspaceEdit(
                        changes={
                            params.text_document.uri: [
                                TextEdit(
                                    range=Range(
                                        start=Position(line=1, character=0),
                                        end=Position(line=1, character=0)
                                    ),
                                    new_text="%maxcore 4000\n"
                                )
                            ]
                        }
                    )
                )
                actions.append(action)
        
        return actions
    
    def _on_did_open(self, params: DidOpenTextDocumentParams):
        """Handle document open"""
        self._validate_document(params.text_document.uri)
    
    def _on_did_change(self, params: DidChangeTextDocumentParams):
        """Handle document change"""
        self._validate_document(params.text_document.uri)


def main():
    """Main entry point"""
    server = ORCALanguageServer()
    server.start_io()


if __name__ == "__main__":
    main()
