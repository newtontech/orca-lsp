"""LSP diagnostic provider for ORCA input files.

Exposes live diagnostics snapshots for agent feedback loops and LSP clients.
Reuses the existing ORCAParser + ORCAValidator pipeline so diagnostics,
completion, hover, and formatting stay consistent.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)

from ..parser import ORCAParser, ParseResult

# Canonical severity mapping from internal strings to LSP DiagnosticSeverity.
_SEVERITY_MAP: Dict[str, DiagnosticSeverity] = {
    "error": DiagnosticSeverity.Error,
    "warning": DiagnosticSeverity.Warning,
    "information": DiagnosticSeverity.Information,
    "hint": DiagnosticSeverity.Hint,
}

# Line-end character constant for full-line diagnostics.
_LINE_END_CHARACTER = 100


class DiagnosticProvider:
    """Provider for ORCA diagnostics.

    Parses an ORCA input file, validates it, and returns LSP ``Diagnostic``
    objects.  Also exposes a CLI/agent-friendly method that returns a
    JSON-serializable snapshot of current diagnostics.
    """

    def __init__(self, parser: Optional[ORCAParser] = None) -> None:
        """Initialize diagnostic provider.

        Args:
            parser: Optional ORCAParser instance.  A fresh one is created
                when *None* is passed.
        """
        self.parser = parser if parser is not None else ORCAParser()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_diagnostics(self, text: str) -> List[Diagnostic]:
        """Return LSP diagnostics for *text*.

        Args:
            text: Full document text.

        Returns:
            List of ``Diagnostic`` instances.
        """
        result = self._parse(text)
        return self._result_to_diagnostics(result)

    def get_diagnostics_snapshot(self, text: str) -> List[Dict[str, Any]]:
        """Return a JSON-serializable diagnostics snapshot for *text*.

        Each entry contains ``line``, ``character``, ``end_line``,
        ``end_character``, ``severity``, ``source``, and ``message``.
        The list is deterministically ordered by (line, character, severity).

        Args:
            text: Full document text.

        Returns:
            A list of dicts suitable for ``json.dumps``.
        """
        diagnostics = self.get_diagnostics(text)
        snapshot: List[Dict[str, Any]] = []
        for diag in diagnostics:
            snapshot.append(
                {
                    "line": diag.range.start.line,
                    "character": diag.range.start.character,
                    "end_line": diag.range.end.line,
                    "end_character": diag.range.end.character,
                    "severity": self._severity_to_str(diag.severity),
                    "source": diag.source or "orca-lsp",
                    "message": diag.message,
                }
            )
        # Deterministic ordering.
        snapshot.sort(key=lambda d: (d["line"], d["character"], d["severity"]))
        return snapshot

    def get_diagnostics_json(self, text: str) -> str:
        """Return diagnostics as a JSON string.

        Convenience wrapper around :meth:`get_diagnostics_snapshot`.

        Args:
            text: Full document text.

        Returns:
            JSON-encoded diagnostics list.
        """
        return json.dumps(self.get_diagnostics_snapshot(text), indent=2)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse(self, text: str) -> ParseResult:
        """Parse text, catching unexpected parser errors.

        Args:
            text: Document text.

        Returns:
            ParseResult with errors/warnings populated.
        """
        try:
            return self.parser.parse(text)
        except Exception as exc:
            result = ParseResult()
            result.errors.append(
                {
                    "message": f"Parser error: {exc}",
                    "line": 0,
                    "severity": "error",
                }
            )
            return result

    def _result_to_diagnostics(self, result: ParseResult) -> List[Diagnostic]:
        """Convert ParseResult errors/warnings into LSP Diagnostics.

        Args:
            result: Parsed result with errors and warnings.

        Returns:
            List of LSP Diagnostic objects.
        """
        diagnostics: List[Diagnostic] = []

        for item in result.errors:
            diagnostics.append(self._item_to_diagnostic(item, DiagnosticSeverity.Error))

        for item in result.warnings:
            diagnostics.append(
                self._item_to_diagnostic(item, DiagnosticSeverity.Warning)
            )

        return diagnostics

    @staticmethod
    def _item_to_diagnostic(
        item: Dict[str, Any],
        severity: DiagnosticSeverity,
    ) -> Diagnostic:
        """Create an LSP Diagnostic from a parsed error/warning item.

        Args:
            item: Dict with ``message`` and ``line`` keys.
            severity: Diagnostic severity level.

        Returns:
            An LSP Diagnostic.
        """
        line = item.get("line", 0)
        return Diagnostic(
            range=Range(
                start=Position(line=line, character=0),
                end=Position(line=line, character=_LINE_END_CHARACTER),
            ),
            message=item.get("message", ""),
            severity=severity,
            source="orca-lsp",
        )

    @staticmethod
    def _severity_to_str(severity: Optional[int]) -> str:
        """Map LSP DiagnosticSeverity enum value to a human-readable string.

        Args:
            severity: DiagnosticSeverity value (may be None).

        Returns:
            Lowercase severity name.
        """
        mapping = {
            DiagnosticSeverity.Error: "error",
            DiagnosticSeverity.Warning: "warning",
            DiagnosticSeverity.Information: "information",
            DiagnosticSeverity.Hint: "hint",
        }
        if severity is None:
            return "error"
        return mapping.get(severity, "error")


__all__ = ["DiagnosticProvider"]
