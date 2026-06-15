"""Code actions provider for ORCA LSP.

Provides quick fixes for common ORCA input file errors.  Each code action
is tied to a diagnostic through stable rule codes produced by the lint and
typecheck providers.

Supported quick fixes
---------------------
- Replace misspelled token with closest valid keyword (ORCA-E001, TC-E002)
- Replace unknown % block name with closest valid block (ORCA-E002)
- Add 'end' to close unclosed % block (ORCA-E003)
- Remove duplicate % block (ORCA-E004)
- Add %maxcore with recommended default value (ORCA-W001)
- Remove duplicate token in simple input (ORCA-W003)
- Add missing simple input line (TC-W001)
- Add missing geometry section stub (TC-W001)
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional

from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    Diagnostic,
    Position,
    Range,
    TextEdit,
    WorkspaceEdit,
)

from ..keywords import (
    ALL_KEYWORDS,
    PERCENT_BLOCKS,
)
from ..parser import ORCAParser
from .lint import (
    RULE_DUPLICATE_BLOCK,
    RULE_DUPLICATE_TOKEN,
    RULE_MALFORMED_MAXCORE,
    RULE_MALFORMED_PAL,
    RULE_MISSING_COORD_TERMINATOR,
    RULE_MISSING_MAXCORE,
    RULE_MISSING_METHOD_BASIS,
    RULE_UNCLOSED_BLOCK,
    RULE_UNKNOWN_BLOCK,
    RULE_UNKNOWN_TOKEN,
)

# Rule codes from the typecheck provider.  Defined locally to avoid
# requiring the typecheck module at import time (it may not yet be
# installed when code_actions is loaded first).
_RULE_INVALID_ENUM = "TC-E002"
_RULE_MISSING_SECTION = "TC-W001"

# Typo mapping for common ORCA misspellings.  Keys are lowercase; values
# are the canonical keyword as it appears in the keyword dictionaries.
_COMMON_TYPOS: Dict[str, str] = {
    # DFT functionals
    "b3ly": "B3LYP",
    "b3lyo": "B3LYP",
    "b3lypp": "B3LYP",
    "b3ly0": "B3LYP",
    "pbe0o": "PBE0",
    "pbeo": "PBE0",
    "pbep": "PBE0",
    "b3lypz": "B3LYP",
    "bp86": "BP86",
    "bp68": "BP86",
    "blyp": "BLYP",
    "blypp": "BLYP",
    "tpss": "TPSS",
    "tpss0": "TPSS0",
    "pbe": "PBE",
    "m062x": "M06-2X",
    "m06-2": "M06-2X",
    "m062": "M06-2X",
    "cam-b3lyp": "CAM-B3LYP",
    "camb3lyp": "CAM-B3LYP",
    "wb97xd": "ωB97X-D",
    "wb97x-d": "ωB97X-D",
    "wb97x": "ωB97X-V",
    # Wavefunction methods
    "mp2": "MP2",
    "mp3": "MP3",
    "mp1": "MP2",
    "ccsd": "CCSD",
    "ccsdt": "CCSD(T)",
    "casscf": "CASSCF",
    "hf": "HF",
    # Basis sets
    "def2svp": "def2-SVP",
    "def2-tzp": "def2-TZVP",
    "def2tzv": "def2-TZVP",
    "def2tzvp": "def2-TZVP",
    "def2qzvp": "def2-QZVP",
    "6-31g": "6-31G",
    "6-31gs": "6-31G*",
    "6-311g": "6-311G",
    "cc-pvdz": "cc-pVDZ",
    "cc-pvtz": "cc-pVTZ",
    "sto-3g": "STO-3G",
    # Job types
    "opt": "OPT",
    "freq": "FREQ",
    "sp": "SP",
    "ts": "TS",
    "optfreq": "OPT FREQ",
    "opt freq": "OPT FREQ",
}

# Default %maxcore value recommended for most calculations
_DEFAULT_MAXCORE = 4000

# Regex for extracting block name from "Unknown % block: '%name'" messages.
_BLOCK_NAME_RE = re.compile(r"'%?(\w+)'", re.IGNORECASE)

# Regex for extracting the unknown token from diagnostic messages.
_UNKNOWN_TOKEN_RE = re.compile(r"'([^']+)'", re.IGNORECASE)


class CodeActionProvider:
    """Provides code actions (quick fixes) for ORCA input files.

    Each quick fix is attached to a diagnostic through its ``code`` field.
    The provider examines diagnostics from lint and typecheck providers and
    returns ``list[CodeAction]`` with minimal workspace edits.
    """

    def __init__(self, parser: Optional[ORCAParser] = None) -> None:
        """Initialize code actions provider.

        Args:
            parser: Optional ORCAParser instance.  A fresh one is created
                when *None* is passed.
        """
        self.parser = parser if parser is not None else ORCAParser()

        # Pre-compute valid keyword set for typo matching
        self._valid_keywords: Dict[str, str] = {}
        for name in ALL_KEYWORDS:
            self._valid_keywords[name.upper()] = name

        # Pre-compute valid block names for block suggestion
        self._valid_block_names: Dict[str, str] = {}
        for name in PERCENT_BLOCKS:
            self._valid_block_names[name.lower()] = name

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_code_actions(
        self,
        source: str,
        diagnostics: List[Diagnostic],
    ) -> List[CodeAction]:
        """Return code actions for the given diagnostics.

        Args:
            source: Full document text.
            diagnostics: List of diagnostics from lint/typecheck providers.

        Returns:
            List of ``CodeAction`` instances with quick-fix edits.
        """
        actions: List[CodeAction] = []

        for diagnostic in diagnostics:
            rule_code = str(diagnostic.code) if diagnostic.code else ""
            action = self._get_action_for_diagnostic(source, diagnostic, rule_code)
            if action is not None:
                actions.append(action)

        # Add general actions not tied to a specific diagnostic
        actions.extend(self._get_general_actions(source))

        return actions

    # ------------------------------------------------------------------
    # Per-diagnostic action dispatch
    # ------------------------------------------------------------------

    def _get_action_for_diagnostic(
        self,
        source: str,
        diagnostic: Diagnostic,
        rule_code: str,
    ) -> Optional[CodeAction]:
        """Dispatch to the appropriate fix handler based on rule code."""
        handler = {
            RULE_UNKNOWN_TOKEN: self._fix_unknown_token,
            _RULE_INVALID_ENUM: self._fix_unknown_token,
            RULE_UNKNOWN_BLOCK: self._fix_unknown_block,
            RULE_UNCLOSED_BLOCK: self._fix_unclosed_block,
            RULE_MISSING_COORD_TERMINATOR: self._fix_missing_coord_terminator,
            RULE_DUPLICATE_BLOCK: self._fix_duplicate_block,
            RULE_MISSING_MAXCORE: self._fix_missing_maxcore,
            RULE_DUPLICATE_TOKEN: self._fix_duplicate_token,
            RULE_MISSING_METHOD_BASIS: self._fix_missing_method_basis,
            RULE_MALFORMED_PAL: self._fix_malformed_pal,
            RULE_MALFORMED_MAXCORE: self._fix_malformed_maxcore,
            _RULE_MISSING_SECTION: self._fix_missing_section,
        }.get(rule_code)

        if handler is None:
            return None

        return handler(source, diagnostic)

    # ------------------------------------------------------------------
    # Individual fix handlers
    # ------------------------------------------------------------------

    def _fix_unknown_token(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Suggest replacement for unknown token in simple input."""
        unknown = self._extract_quoted_token(diagnostic.message)
        if not unknown:
            return None

        suggestion = self._find_closest_keyword(unknown)
        if not suggestion:
            return None

        diag_range = diagnostic.range
        line_num = diag_range.start.line
        col_start = diag_range.start.character
        col_end = diag_range.end.character

        if col_end - col_start <= 1:
            col_end = col_start + len(unknown)

        return CodeAction(
            title=f"Replace '{unknown}' with '{suggestion}'",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(
                                start=Position(line=line_num, character=col_start),
                                end=Position(line=line_num, character=col_end),
                            ),
                            new_text=suggestion,
                        )
                    ]
                }
            ),
        )

    def _fix_unknown_block(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Suggest replacement for unknown % block name."""
        block_name = self._extract_block_name(diagnostic.message)
        if not block_name:
            return None

        suggestion = self._find_closest_block(block_name)
        if not suggestion:
            return None

        diag_range = diagnostic.range
        line_num = diag_range.start.line
        col_start = diag_range.start.character
        col_end = diag_range.end.character

        return CodeAction(
            title=f"Replace '%{block_name}' with '%{suggestion}'",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(
                                start=Position(line=line_num, character=col_start),
                                end=Position(line=line_num, character=col_end),
                            ),
                            new_text=f"%{suggestion}",
                        )
                    ]
                }
            ),
        )

    def _fix_unclosed_block(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Add 'end' to close an unclosed % block."""
        lines = source.split("\n")
        diag_range = diagnostic.range
        block_start_line = diag_range.start.line

        block_name = self._extract_block_name(diagnostic.message)

        insert_line = block_start_line + 1
        while insert_line < len(lines) and lines[insert_line].strip():
            insert_line += 1

        if insert_line >= len(lines):
            last_line_idx = len(lines) - 1
            insert_pos = Position(
                line=last_line_idx,
                character=len(lines[last_line_idx]),
            )
            new_text = "\nend"
        else:
            insert_pos = Position(line=insert_line, character=0)
            new_text = "end\n"

        block_label = f" '%{block_name}'" if block_name else ""
        return CodeAction(
            title=f"Add 'end' to close{block_label} block",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(start=insert_pos, end=insert_pos),
                            new_text=new_text,
                        )
                    ]
                }
            ),
        )

    def _fix_missing_coord_terminator(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Append a closing '*' line to terminate a coordinate block."""
        lines = source.split("\n")
        insert_line = len(lines)
        while insert_line > 0 and not lines[insert_line - 1].strip():
            insert_line -= 1
        insert_pos = Position(line=insert_line, character=0)
        new_text = "*\n" if insert_line < len(lines) else "\n*\n"
        return CodeAction(
            title="Add '*' to terminate coordinate block",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(start=insert_pos, end=insert_pos),
                            new_text=new_text,
                        )
                    ]
                }
            ),
        )

    def _fix_duplicate_block(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Remove a duplicate % block."""
        lines = source.split("\n")
        diag_range = diagnostic.range
        start_line = diag_range.start.line

        end_line = start_line + 1
        while end_line < len(lines):
            stripped = lines[end_line].strip().lower()
            if stripped == "end":
                end_line += 1
                break
            if stripped.startswith("%") and end_line > start_line + 1:
                break
            if not stripped:
                break
            end_line += 1

        if end_line < len(lines) and not lines[end_line].strip():
            end_line += 1

        start_pos = Position(line=start_line, character=0)
        end_pos = Position(line=end_line, character=0)

        block_name = self._extract_block_name(diagnostic.message)
        label = f" '%{block_name}'" if block_name else ""

        return CodeAction(
            title=f"Remove duplicate{label} block",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(start=start_pos, end=end_pos),
                            new_text="",
                        )
                    ]
                }
            ),
        )

    def _fix_missing_maxcore(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Add %maxcore with a recommended default value."""
        lines = source.split("\n")

        insert_line = 1
        for i, line in enumerate(lines):
            if line.strip().startswith("!"):
                insert_line = i + 1
                break

        insert_pos = Position(line=insert_line, character=0)

        return CodeAction(
            title=f"Add '%maxcore {_DEFAULT_MAXCORE}'",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(start=insert_pos, end=insert_pos),
                            new_text=f"%maxcore {_DEFAULT_MAXCORE}\n",
                        )
                    ]
                }
            ),
        )

    def _fix_duplicate_token(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Remove a duplicate token in the simple input line."""
        diag_range = diagnostic.range
        line_num = diag_range.start.line
        col_start = diag_range.start.character
        col_end = diag_range.end.character

        lines = source.split("\n")
        if line_num >= len(lines):
            return None

        line = lines[line_num]

        while col_end < len(line) and line[col_end] == " ":
            col_end += 1

        token = self._extract_quoted_token(diagnostic.message)
        label = f" '{token}'" if token else ""

        return CodeAction(
            title=f"Remove duplicate{label} token",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(
                                start=Position(line=line_num, character=col_start),
                                end=Position(line=line_num, character=col_end),
                            ),
                            new_text="",
                        )
                    ]
                }
            ),
        )

    def _fix_missing_method_basis(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Append a default basis set when the route line is missing one."""
        message = diagnostic.message.lower()
        if "basis" not in message:
            return None

        lines = source.split("\n")
        line_num = diagnostic.range.start.line
        if line_num >= len(lines):
            return None

        line = lines[line_num].rstrip()
        insert_pos = Position(line=line_num, character=len(line))
        return CodeAction(
            title="Append basis set 'def2-SVP' to route line",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(start=insert_pos, end=insert_pos),
                            new_text=" def2-SVP",
                        )
                    ]
                }
            ),
        )

    def _fix_malformed_pal(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Insert a default nprocs line into a malformed %pal block."""
        lines = source.split("\n")
        block_start = diagnostic.range.start.line
        insert_line = block_start + 1
        while insert_line < len(lines) and lines[insert_line].strip().lower() == "end":
            break
        insert_pos = Position(line=insert_line, character=0)
        return CodeAction(
            title="Add 'nprocs 4' to %pal block",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(start=insert_pos, end=insert_pos),
                            new_text="  nprocs 4\n",
                        )
                    ]
                }
            ),
        )

    def _fix_malformed_maxcore(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Replace a non-numeric %maxcore value with the recommended default."""
        diag_range = diagnostic.range
        return CodeAction(
            title=f"Replace %maxcore value with '{_DEFAULT_MAXCORE}'",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(
                                start=Position(
                                    line=diag_range.start.line,
                                    character=diag_range.start.character,
                                ),
                                end=Position(
                                    line=diag_range.end.line,
                                    character=diag_range.end.character,
                                ),
                            ),
                            new_text=str(_DEFAULT_MAXCORE),
                        )
                    ]
                }
            ),
        )

    def _fix_missing_section(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> Optional[CodeAction]:
        """Add a missing section stub (simple input or geometry)."""
        message = diagnostic.message.lower()

        if "simple input" in message:
            return self._add_simple_input_stub(source, diagnostic)

        if "geometry section" in message or "geometry" in message:
            return self._add_geometry_stub(source, diagnostic)

        return None

    def _add_simple_input_stub(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> CodeAction:
        """Add a simple input line stub."""
        insert_pos = Position(line=0, character=0)
        return CodeAction(
            title="Add simple input line '! B3LYP def2-SVP OPT'",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(start=insert_pos, end=insert_pos),
                            new_text="! B3LYP def2-SVP OPT\n\n",
                        )
                    ]
                }
            ),
        )

    def _add_geometry_stub(
        self,
        source: str,
        diagnostic: Diagnostic,
    ) -> CodeAction:
        """Add a geometry section stub."""
        lines = source.split("\n")
        last_line = max(0, len(lines) - 1)
        last_len = len(lines[-1]) if lines else 0
        insert_pos = Position(line=last_line, character=last_len)

        return CodeAction(
            title="Add geometry section '* xyz 0 1'",
            kind=CodeActionKind.QuickFix,
            diagnostics=[diagnostic],
            edit=WorkspaceEdit(
                changes={
                    "document": [
                        TextEdit(
                            range=Range(start=insert_pos, end=insert_pos),
                            new_text="\n\n* xyz 0 1\n  H 0.0 0.0 0.0\n  H 0.0 0.0 0.74\n*\n",
                        )
                    ]
                }
            ),
        )

    # ------------------------------------------------------------------
    # General (non-diagnostic) actions
    # ------------------------------------------------------------------

    def _get_general_actions(self, source: str) -> List[CodeAction]:
        """Return general code actions not tied to specific diagnostics."""
        actions: List[CodeAction] = []

        has_maxcore = False
        for line in source.split("\n"):
            if line.strip().lower().startswith("%maxcore"):
                has_maxcore = True
                break

        if not has_maxcore:
            insert_line = 1
            lines = source.split("\n")
            for i, line in enumerate(lines):
                if line.strip().startswith("!"):
                    insert_line = i + 1
                    break

            insert_pos = Position(line=insert_line, character=0)
            actions.append(
                CodeAction(
                    title=f"Add '%maxcore {_DEFAULT_MAXCORE}'",
                    kind=CodeActionKind.QuickFix,
                    edit=WorkspaceEdit(
                        changes={
                            "document": [
                                TextEdit(
                                    range=Range(start=insert_pos, end=insert_pos),
                                    new_text=f"%maxcore {_DEFAULT_MAXCORE}\n",
                                )
                            ]
                        }
                    ),
                )
            )

        return actions

    # ------------------------------------------------------------------
    # Keyword / block matching helpers
    # ------------------------------------------------------------------

    def _find_closest_keyword(self, unknown: str) -> Optional[str]:
        """Find the closest matching valid keyword."""
        if len(unknown) < 2:
            return None

        canonical = _COMMON_TYPOS.get(unknown.lower())
        if canonical:
            return canonical

        upper = unknown.upper()
        if upper in self._valid_keywords:
            return self._valid_keywords[upper]

        best_match: Optional[str] = None
        best_score = 0.0

        for kw in self._valid_keywords.values():
            score = self._similarity_score(unknown.lower(), kw.lower())
            if score > best_score and score > 0.6:
                best_score = score
                best_match = kw

        return best_match

    def _find_closest_block(self, block_name: str) -> Optional[str]:
        """Find the closest matching valid % block name."""
        lower = block_name.lower()

        if lower in self._valid_block_names:
            return self._valid_block_names[lower]

        best_match: Optional[str] = None
        best_score = 0.0

        for name in self._valid_block_names.values():
            score = self._similarity_score(lower, name.lower())
            if score > best_score and score > 0.3:
                best_score = score
                best_match = name

        return best_match

    @staticmethod
    def _similarity_score(s1: str, s2: str) -> float:
        """Calculate similarity score between two strings (0-1)."""
        if len(s1) > len(s2):
            s1, s2 = s2, s1

        if len(s2) == 0:
            return 1.0 if len(s1) == 0 else 0.0

        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        return 1.0 - (distance / max_len)

    # ------------------------------------------------------------------
    # Message parsing helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_quoted_token(message: str) -> str:
        """Extract the token between single quotes from a diagnostic message."""
        match = _UNKNOWN_TOKEN_RE.search(message)
        if match:
            return match.group(1)
        return ""

    @staticmethod
    def _extract_block_name(message: str) -> str:
        """Extract the block name from a diagnostic message."""
        match = _BLOCK_NAME_RE.search(message)
        if match:
            return match.group(1).lower()
        return ""


__all__ = ["CodeActionProvider"]
