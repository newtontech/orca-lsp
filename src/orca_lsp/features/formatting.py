"""LSP formatting provider for ORCA input files.

Provides document and range formatting that normalizes indentation,
strips trailing whitespace, and canonicalises structural keywords while
preserving comments, semantic content, and section ordering.
"""

from __future__ import annotations

import re
from typing import List, Optional

from lsprotocol.types import (
    DocumentFormattingParams,
    DocumentRangeFormattingParams,
    FormattingOptions,
    Position,
    Range,
    TextEdit,
)
from pygls.server import LanguageServer

from ..keywords import PERCENT_BLOCKS

# ORCA structural markers that affect indentation depth.
_PERCENT_BLOCK_NAMES: frozenset[str] = frozenset(
    name.lower() for name in PERCENT_BLOCKS
)


class FormattingProvider:
    """Provides formatting for ORCA input files.

    Formatting rules:

    * Trailing whitespace is stripped from every line.
    * The simple-input line (``!``) is left unindented.
    * ``%`` block headers start at column 0; their body lines are indented
      by one *indent_size* level; ``end`` closes the block back to column 0.
    * Geometry body lines (between ``* xyz …`` and ``*``) are indented by
      one *indent_size* level.
    * Blank lines and comment lines (``#``) are preserved but stripped of
      trailing whitespace.
    * No semantic rewrites are performed.
    """

    def __init__(self, server: Optional[LanguageServer] = None) -> None:
        """Initialise the formatting provider.

        Args:
            server: Optional language server instance.
        """
        self.server = server

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def format_document(
        self, text: str, params: DocumentFormattingParams
    ) -> List[TextEdit]:
        """Format the entire document.

        Args:
            text: Full document text.
            params: LSP formatting parameters (tab size, insert spaces).

        Returns:
            A list containing a single ``TextEdit`` that replaces the
            whole document, or an empty list when the text is already
            formatted.
        """
        indent_size = self._indent_size(params.options)
        indent_str = self._indent_str(params.options, indent_size)

        formatted = self._format_lines(text.splitlines(), indent_str, 0, None)

        formatted_text = "\n".join(formatted)
        if text.endswith("\n"):
            formatted_text += "\n"

        if formatted_text == text:
            return []

        lines = text.splitlines()
        return [
            TextEdit(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=len(lines), character=0),
                ),
                new_text=formatted_text,
            )
        ]

    def format_range(
        self, text: str, params: DocumentRangeFormattingParams
    ) -> List[TextEdit]:
        """Format a subrange of the document.

        To ensure correct indentation the formatter needs structural
        context from the start of the file, but only the requested range
        is replaced in the output.

        Args:
            text: Full document text.
            params: LSP range-formatting parameters.

        Returns:
            A list containing a single ``TextEdit`` covering the
            requested range, or an empty list when no changes are needed.
        """
        indent_size = self._indent_size(params.options)
        indent_str = self._indent_str(params.options, indent_size)

        all_lines = text.splitlines()
        start_line = params.range.start.line
        end_line = params.range.end.line

        # Clamp to file bounds.
        end_line = min(end_line, len(all_lines))
        if start_line >= len(all_lines):
            return []

        # Format the full file to get correct indentation context.
        all_formatted = self._format_lines(all_lines, indent_str, 0, None)

        # Extract only the requested range from the formatted output.
        range_formatted = all_formatted[start_line:end_line]
        range_original = all_lines[start_line:end_line]

        if range_formatted == range_original:
            return []

        range_text = "\n".join(range_formatted)

        # Compute the end position: character 0 of the line after the range.
        end_pos = Position(line=end_line, character=0)

        return [
            TextEdit(
                range=Range(
                    start=Position(line=start_line, character=0),
                    end=end_pos,
                ),
                new_text=range_text,
            )
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _indent_size(options: Optional[FormattingOptions]) -> int:
        """Extract tab size from formatting options.

        Args:
            options: LSP formatting options (may be None).

        Returns:
            Tab size as an integer (default 2).
        """
        if options is None:
            return 2
        return getattr(options, "tab_size", 2) or 2

    @staticmethod
    def _indent_str(options: Optional[FormattingOptions], indent_size: int) -> str:
        """Build the indent string from formatting options.

        Args:
            options: LSP formatting options (may be None).
            indent_size: Number of spaces per indent level.

        Returns:
            A string of spaces or a single tab character.
        """
        if options is not None and not getattr(options, "insert_spaces", True):
            return "\t"
        return " " * indent_size

    def _format_lines(
        self,
        lines: list[str],
        indent_str: str,
        start: int,
        end: Optional[int],
    ) -> list[str]:
        """Format lines with correct ORCA indentation.

        Walks through the file tracking structural depth changes from
        ``%`` blocks and geometry sections.

        Args:
            lines: Raw source lines.
            indent_str: String for one indentation level.
            start: Start line index (inclusive).
            end: End line index (exclusive), or None for all remaining.

        Returns:
            List of formatted lines (no trailing newline).
        """
        if end is None:
            end = len(lines)

        formatted: list[str] = []
        indent_level = 0

        # Track whether we are inside a multi-line % block so we know
        # when to close the indent on ``end``.
        in_percent_block = False
        in_geometry = False

        for i in range(start, end):
            line = lines[i] if i < len(lines) else ""
            stripped = line.strip()

            # Blank lines: preserve but strip trailing whitespace.
            if not stripped:
                formatted.append("")
                continue

            # Comment lines: preserve, strip trailing whitespace.
            if stripped.startswith("#"):
                formatted.append(stripped)
                continue

            # Geometry end marker: bare ``*`` or ``*`` with trailing text
            # like ``* end``.
            if in_geometry and stripped == "*":
                indent_level = max(0, indent_level - 1)
                in_geometry = False
                formatted.append(indent_str * indent_level + stripped)
                continue

            # Geometry start: ``* xyz CHARGE MULT`` or ``* int …``.
            if stripped.startswith("*") and not in_geometry:
                formatted.append(stripped)
                indent_level += 1
                in_geometry = True
                continue

            # ``end`` closes a multi-line % block.
            if in_percent_block and stripped.lower() == "end":
                indent_level = max(0, indent_level - 1)
                in_percent_block = False
                formatted.append(indent_str * indent_level + stripped)
                continue

            # Simple input line (``!``): no indentation.
            if stripped.startswith("!"):
                formatted.append(stripped)
                continue

            # % block header.
            if stripped.startswith("%"):
                formatted.append(stripped)
                # Determine if this is a multi-line block or a single-liner.
                if self._is_single_line_block(stripped):
                    # Single-line % block (e.g. ``%maxcore 4000``).
                    pass
                else:
                    indent_level += 1
                    in_percent_block = True
                continue

            # All other lines: apply current indentation.
            formatted.append(indent_str * indent_level + stripped)

        return formatted

    @staticmethod
    def _is_single_line_block(line: str) -> bool:
        """Check if a % block line is self-contained (no multi-line body).

        A block is single-line when:
        * It contains ``end`` on the same line.
        * It is a simple two-part assignment like ``%maxcore 4000`` or
          ``%moinp "file.gbw"``.

        Args:
            line: Stripped source line starting with ``%``.

        Returns:
            True if the block is complete on a single line.
        """
        lower = line.lower()
        if "end" in lower.split():
            return True

        parts = line.split()
        if len(parts) == 2:
            value = parts[1]
            if value.isdigit():
                return True
            if value.startswith('"') and value.endswith('"'):
                return True

        return False


__all__ = ["FormattingProvider"]


def get_formatting_provider(server: Optional[LanguageServer] = None) -> FormattingProvider:
    """Create a formatting provider instance.

    Args:
        server: Optional language server instance.

    Returns:
        A new ``FormattingProvider``.
    """
    return FormattingProvider(server)
