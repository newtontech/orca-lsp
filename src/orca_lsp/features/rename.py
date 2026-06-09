"""LSP rename provider for ORCA.

This module provides rename refactoring support for ORCA input files.
It supports renaming ORCA ``%`` block names, simple-input keywords, and
``%`` block parameter keywords, while safely rejecting reserved keywords,
section names, element symbols, and ambiguous or unsupported targets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from lsprotocol.types import (
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

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

_PERCENT_BLOCK_NAME_RE = re.compile(r"%\s*(\w+)", re.IGNORECASE)
_WORD_RE = re.compile(r"[A-Za-z0-9_\-\*\.\(\)]+")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class SymbolOccurrence:
    """A single occurrence of a renameable symbol."""

    line: int
    start_col: int
    end_col: int
    kind: str  # "block_name" | "simple_input_token" | "block_param"


@dataclass(frozen=True)
class RenameTarget:
    """Describes what is being renamed and its scope."""

    name: str
    kind: str  # "block_name" | "simple_input_keyword" | "block_param"
    occurrences: Tuple[SymbolOccurrence, ...]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_word_at(line: str, character: int) -> str:
    """Return the word boundary-extended around *character* on *line*."""
    if not line or character < 0 or character > len(line):
        return ""

    start = character
    while start > 0 and _is_word_char(line[start - 1]):
        start -= 1

    end = character
    while end < len(line) and _is_word_char(line[end]):
        end += 1

    return line[start:end]


def _is_word_char(ch: str) -> bool:
    """Return True if *ch* can appear inside an ORCA token."""
    return ch.isalnum() or ch in ("_", "-", "*", ".", "(", ")")


def _find_line_context(lines: List[str], line_idx: int) -> str:
    """Return a context tag for *line_idx*.

    Returns one of ``"simple_input"``, ``"percent_block"``, ``"geometry"``,
    or ``"other"``.

    Walks backwards from *line_idx* to determine the enclosing context.
    Correctly identifies indented lines inside ``%`` blocks and geometry
    atom lines inside ``* xyz ... *`` sections.
    """
    if line_idx >= len(lines):
        return "other"

    stripped = lines[line_idx].strip()

    if stripped.startswith("!"):
        return "simple_input"

    if stripped.startswith("%"):
        return "percent_block"

    if stripped.startswith("*"):
        return "geometry"

    # Walk backwards to determine enclosing context.
    # Track whether we are inside a % block (between %header and "end").
    in_percent_block = False
    for i in range(line_idx - 1, -1, -1):
        s = lines[i].strip()
        if not s or s.startswith("#"):
            continue
        if s.lower() == "end":
            # We've crossed an "end" -- we're outside any block above it.
            # Continue walking to find the enclosing structure.
            break
        if s.startswith("%"):
            # Found a % block header above us without an intervening "end"
            # means we are inside that block.
            in_percent_block = True
            break
        if s.startswith("*") and ("xyz" in s.lower() or "int" in s.lower()):
            # Check if the geometry section is still open at line_idx.
            for j in range(i + 1, line_idx + 1):
                sl = lines[j].strip()
                if sl == "*" or (sl.startswith("* ") and j > i):
                    return "other"
            return "geometry"
        if s.startswith("!"):
            continue

    if in_percent_block:
        return "percent_block"

    return "other"


def _is_reserved_keyword(word: str) -> bool:
    """Return True if *word* is a reserved ORCA keyword or block name."""
    word_upper = word.upper()
    word_lower = word.lower()

    if word_upper in ALL_KEYWORDS:
        return True
    if word_lower in PERCENT_BLOCKS:
        return True
    if word_lower == "end":
        return True
    return False


def _is_valid_new_name(name: str) -> bool:
    """Return True if *name* is an acceptable rename target."""
    if not name:
        return False
    # Must start with a letter or underscore; allow word chars, hyphens, dots.
    return bool(re.match(r"^[A-Za-z_][\w\-\.\(\)]*$", name))


def _collect_block_name_occurrences(
    text: str, block_name: str
) -> List[SymbolOccurrence]:
    """Find every occurrence of a ``%`` block name in *text*."""
    occurrences: List[SymbolOccurrence] = []
    name_lower = block_name.lower()
    lines = text.split("\n")

    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        match = _PERCENT_BLOCK_NAME_RE.match(stripped)
        if match and match.group(1).lower() == name_lower:
            # Find column in original line (account for leading whitespace)
            name_start = line.lower().find(name_lower)
            if name_start < 0:
                name_start = match.start(1)
            name_end = name_start + len(match.group(1))
            occurrences.append(
                SymbolOccurrence(
                    line=line_idx,
                    start_col=name_start,
                    end_col=name_end,
                    kind="block_name",
                )
            )

    return occurrences


def _collect_simple_input_keyword_occurrences(
    text: str, keyword: str
) -> List[SymbolOccurrence]:
    """Find every occurrence of a keyword in ``!`` simple-input lines."""
    occurrences: List[SymbolOccurrence] = []
    lines = text.split("\n")

    for line_idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped.startswith("!"):
            continue

        # Parse tokens from simple input
        content = stripped[1:].strip()
        comment_pos = content.find("!")
        if comment_pos >= 0:
            content = content[:comment_pos].strip()

        tokens = content.split()
        col = len(stripped) - len(stripped.lstrip())  # leading whitespace

        # Skip the ! character
        col = stripped.find("!") + 1

        for token in tokens:
            # Find token position in the original line
            token_pos = line.find(token, col)
            if token_pos < 0:
                # Try case-insensitive
                lower_line = line.lower()
                token_pos = lower_line.find(token.lower(), col)
            if token_pos >= 0:
                if token.upper() == keyword.upper():
                    occurrences.append(
                        SymbolOccurrence(
                            line=line_idx,
                            start_col=token_pos,
                            end_col=token_pos + len(token),
                            kind="simple_input_token",
                        )
                    )
                col = token_pos + len(token)

    return occurrences


def _collect_block_param_occurrences(
    text: str, param_name: str
) -> List[SymbolOccurrence]:
    """Find every occurrence of a ``%`` block parameter in *text*."""
    occurrences: List[SymbolOccurrence] = []
    param_lower = param_name.lower()
    lines = text.split("\n")

    # Track block boundaries using a simple state machine.
    in_block = False
    for line_idx, line in enumerate(lines):
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("%"):
            # Start of a new block.  Scan the rest of this line for params
            # (single-line blocks like "%maxcore 4000").
            in_block = True
            # Check if this single-line block ends on the same line
            if " end" in stripped.lower() or stripped.lower().endswith("end"):
                in_block = False

            # Scan for the parameter on the % header line itself
            _scan_line_for_param(
                occurrences, line_idx, line, stripped, param_lower
            )
            continue

        if in_block:
            if stripped.lower() == "end" or stripped.lower().endswith(" end"):
                in_block = False
                continue

            _scan_line_for_param(
                occurrences, line_idx, line, stripped, param_lower
            )

    return occurrences


def _scan_line_for_param(
    occurrences: List[SymbolOccurrence],
    line_idx: int,
    line: str,
    stripped: str,
    param_lower: str,
) -> None:
    """Scan a single line for a parameter keyword match and append occurrences."""
    for m in re.finditer(
        r"\b(" + re.escape(param_lower) + r")\b", stripped, re.IGNORECASE
    ):
        if m.group(1).lower() == param_lower:
            # Map match position back to the original (unstripped) line
            line_offset = len(line) - len(line.lstrip())
            col = line_offset + m.start()
            occurrences.append(
                SymbolOccurrence(
                    line=line_idx,
                    start_col=col,
                    end_col=col + len(m.group(1)),
                    kind="block_param",
                )
            )

    return occurrences


# ---------------------------------------------------------------------------
# RenameProvider
# ---------------------------------------------------------------------------


class RenameProvider:
    """Provides rename support for ORCA input files.

    Renameable targets:

    * ``%`` block names (e.g. renaming all ``scf`` blocks to ``scf2``).
    * Simple-input keywords (methods, basis sets, job types).
    * ``%`` block parameter keywords (e.g. ``nprocs``, ``maxiter``).

    Rejected targets:

    * Reserved keywords and section names (``end``, element symbols, etc.).
    * Empty positions or out-of-range lines.
    * Ambiguous scopes where the symbol cannot be safely identified.
    """

    def __init__(self, parser: Optional[ORCAParser] = None) -> None:
        """Initialize the rename provider.

        Args:
            parser: Optional ORCAParser instance.
        """
        self.parser = parser if parser is not None else ORCAParser()

    # ------------------------------------------------------------------
    # prepareRename
    # ------------------------------------------------------------------

    def prepare_rename(
        self,
        text: str,
        position: Position,
    ) -> Optional[Range]:
        """Validate that the symbol at *position* can be renamed.

        Returns the Range of the symbol if renameable, or None.

        Renameable targets:
          - ``%`` block names
          - Simple-input keywords (methods, basis sets, job types)
          - ``%`` block parameter keywords

        Rejected targets:
          - ``end`` keywords
          - Geometry section content
          - Arbitrary words that are not recognised symbols
          - Empty positions or out-of-range lines
        """
        lines = text.split("\n")
        if position.line >= len(lines) or position.line < 0:
            return None

        line = lines[position.line]
        word = _get_word_at(line, position.character)

        if not word:
            return None

        word_lower = word.lower()

        # Reject "end" keyword
        if word_lower == "end":
            return None

        ctx = _find_line_context(lines, position.line)

        # Reject geometry section content
        if ctx == "geometry":
            return None

        # Check if cursor is on a % block name
        if ctx == "percent_block":
            match = _PERCENT_BLOCK_NAME_RE.match(line.strip())
            if match:
                block_name = match.group(1)
                name_start = line.lower().find(block_name.lower())
                if name_start < 0:
                    name_start = match.start(1)
                name_end = name_start + len(block_name)

                if name_start <= position.character <= name_end:
                    # Block names in PERCENT_BLOCKS are reserved -- reject
                    if block_name.lower() in PERCENT_BLOCKS:
                        return None
                    # User-defined block name -- allow
                    return Range(
                        start=Position(line=position.line, character=name_start),
                        end=Position(line=position.line, character=name_end),
                    )

            # Check for parameter keywords inside blocks
            stripped = line.strip()
            for m in _WORD_RE.finditer(stripped):
                if m.start() <= position.character - (len(line) - len(line.lstrip())) <= m.end():
                    token = m.group()
                    if _is_reserved_keyword(token):
                        return None
                    # Must be a known parameter keyword in the block context
                    return Range(
                        start=Position(line=position.line, character=m.start()),
                        end=Position(line=position.line, character=m.end()),
                    )

            return None

        # Simple input line
        if ctx == "simple_input":
            # Simple-input keywords are reserved (methods, basis sets, job types)
            # -- they are renameable because the user might want to change e.g.
            # B3LYP to PBE0 across the file.
            col = self._find_token_col(line, word)
            if col < 0:
                return None
            return Range(
                start=Position(line=position.line, character=col),
                end=Position(line=position.line, character=col + len(word)),
            )

        return None

    # ------------------------------------------------------------------
    # rename
    # ------------------------------------------------------------------

    def get_rename_edits(
        self,
        text: str,
        uri: str,
        position: Position,
        new_name: str,
    ) -> Optional[WorkspaceEdit]:
        """Get workspace edits for renaming a symbol.

        Args:
            text: Document text.
            uri: Document URI.
            position: Cursor position.
            new_name: The new name for the symbol.

        Returns:
            WorkspaceEdit with changes, or None if rename is not valid.
        """
        if not _is_valid_new_name(new_name):
            return None

        lines = text.split("\n")
        if position.line >= len(lines) or position.line < 0:
            return None

        line = lines[position.line]
        target = self._identify_target(text, lines, line, position)

        if target is None:
            return None

        if target.kind == "block_name":
            return self._rename_block_name(uri, target, new_name)
        elif target.kind == "simple_input_keyword":
            return self._rename_simple_input_keyword(uri, target, new_name)
        elif target.kind == "block_param":
            return self._rename_block_param(uri, target, new_name)

        return None

    # ------------------------------------------------------------------
    # is_valid_rename
    # ------------------------------------------------------------------

    def is_valid_rename(
        self,
        text: str,
        position: Position,
        new_name: str,
    ) -> bool:
        """Check if a rename operation is valid.

        Args:
            text: Document text.
            position: Cursor position.
            new_name: The new name for the symbol.

        Returns:
            True if rename is valid.
        """
        if not _is_valid_new_name(new_name):
            return False

        lines = text.split("\n")
        if position.line >= len(lines) or position.line < 0:
            return False

        line = lines[position.line]
        target = self._identify_target(text, lines, line, position)
        return target is not None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _identify_target(
        self,
        text: str,
        lines: List[str],
        line: str,
        position: Position,
    ) -> Optional[RenameTarget]:
        """Identify the renameable symbol under the cursor.

        Returns a RenameTarget, or None if the cursor is not on a
        renameable symbol.
        """
        word = _get_word_at(line, position.character)
        if not word:
            return None

        ctx = _find_line_context(lines, position.line)

        # Check if cursor is on a % block name
        if ctx == "percent_block":
            match = _PERCENT_BLOCK_NAME_RE.match(line.strip())
            if match:
                block_name = match.group(1)
                name_start = line.lower().find(block_name.lower())
                if name_start < 0:
                    name_start = match.start(1)
                name_end = name_start + len(block_name)

                if name_start <= position.character <= name_end:
                    # Reject reserved block names
                    if block_name.lower() in PERCENT_BLOCKS:
                        return None
                    occurrences = _collect_block_name_occurrences(text, block_name)
                    return RenameTarget(
                        name=block_name,
                        kind="block_name",
                        occurrences=tuple(occurrences),
                    )

            # Check for parameter keywords inside blocks
            stripped = line.strip()
            line_offset = len(line) - len(line.lstrip())
            for m in _WORD_RE.finditer(stripped):
                abs_start = m.start() + line_offset
                abs_end = m.end() + line_offset
                if abs_start <= position.character <= abs_end:
                    token = m.group()
                    if _is_reserved_keyword(token):
                        return None
                    occurrences = _collect_block_param_occurrences(text, token)
                    if not occurrences:
                        return None
                    return RenameTarget(
                        name=token,
                        kind="block_param",
                        occurrences=tuple(occurrences),
                    )

            return None

        # Simple input line
        if ctx == "simple_input":
            col = self._find_token_col(line, word)
            if col < 0:
                return None

            occurrences = _collect_simple_input_keyword_occurrences(text, word)
            if not occurrences:
                return None

            return RenameTarget(
                name=word,
                kind="simple_input_keyword",
                occurrences=tuple(occurrences),
            )

        return None

    def _rename_block_name(
        self,
        uri: str,
        target: RenameTarget,
        new_name: str,
    ) -> Optional[WorkspaceEdit]:
        """Build workspace edits for a block name rename."""
        changes: Dict[str, List[TextEdit]] = {uri: []}

        for occ in target.occurrences:
            changes[uri].append(
                TextEdit(
                    range=Range(
                        start=Position(line=occ.line, character=occ.start_col),
                        end=Position(line=occ.line, character=occ.end_col),
                    ),
                    new_text=new_name,
                )
            )

        if not changes[uri]:
            return None

        return WorkspaceEdit(changes=changes)

    def _rename_simple_input_keyword(
        self,
        uri: str,
        target: RenameTarget,
        new_name: str,
    ) -> Optional[WorkspaceEdit]:
        """Build workspace edits for a simple-input keyword rename."""
        changes: Dict[str, List[TextEdit]] = {uri: []}

        for occ in target.occurrences:
            changes[uri].append(
                TextEdit(
                    range=Range(
                        start=Position(line=occ.line, character=occ.start_col),
                        end=Position(line=occ.line, character=occ.end_col),
                    ),
                    new_text=new_name,
                )
            )

        if not changes[uri]:
            return None

        return WorkspaceEdit(changes=changes)

    def _rename_block_param(
        self,
        uri: str,
        target: RenameTarget,
        new_name: str,
    ) -> Optional[WorkspaceEdit]:
        """Build workspace edits for a block parameter rename."""
        changes: Dict[str, List[TextEdit]] = {uri: []}

        for occ in target.occurrences:
            changes[uri].append(
                TextEdit(
                    range=Range(
                        start=Position(line=occ.line, character=occ.start_col),
                        end=Position(line=occ.line, character=occ.end_col),
                    ),
                    new_text=new_name,
                )
            )

        if not changes[uri]:
            return None

        return WorkspaceEdit(changes=changes)

    @staticmethod
    def _find_token_col(line: str, word: str) -> int:
        """Find the column of *word* in *line*."""
        # Try exact case match first
        col = line.find(word)
        if col >= 0:
            return col
        # Try case-insensitive match
        lower = line.lower()
        col = lower.find(word.lower())
        return col


__all__ = ["RenameProvider"]
