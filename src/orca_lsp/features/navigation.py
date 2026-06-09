"""LSP navigation providers for ORCA input files.

Provides go-to-definition, hover, and find-references for ORCA input files.
Supports navigation to/from:

* ``%`` block names and parameters
* Simple-input keywords
* Geometry atom symbols
* Coordinate block references
"""

from __future__ import annotations

import re
from typing import List, Optional

from lsprotocol.types import (
    Hover,
    Location,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
)

from ..parser import (
    ORCAParser,
    ParseResult,
    PercentBlock,
)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z_]\w*")


def _word_at_line(line: str, char: int) -> str:
    """Extract the identifier word at *char* in *line*."""
    for m in _WORD_RE.finditer(line):
        if m.start() <= char <= m.end():
            return m.group()
    return ""


def _position_in_range(pos: Position, rng: Range) -> bool:
    """Return True when *pos* falls inside *rng*."""
    if pos.line < rng.start.line or pos.line > rng.end.line:
        return False
    if pos.line == rng.start.line and pos.character < rng.start.character:
        return False
    if pos.line == rng.end.line and pos.character > rng.end.character:
        return False
    return True


# ------------------------------------------------------------------
# DefinitionProvider
# ------------------------------------------------------------------

class DefinitionProvider:
    """Provides go-to-definition for ORCA input files."""

    def __init__(self, parser: ORCAParser) -> None:
        self._parser = parser

    def get_definition(
        self,
        text: str,
        position: Position,
    ) -> Optional[Location]:
        """Return the definition location of the symbol at *position*."""
        lines = text.splitlines()
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        word = _word_at_line(line, position.character)
        if not word:
            return None

        # Check if cursor is on a % block parameter → jump to block start
        stripped = line.lstrip()
        if stripped.startswith("%"):
            # Inside a % block — try to find the parameter definition
            return self._definition_in_block(lines, position, word)

        # Try to find as a % block name (e.g. "scf" → "%scf")
        for i, l in enumerate(lines):
            sl = l.lstrip()
            if sl.startswith("%"):
                block_name = sl[1:].split()[0].rstrip("{")
                if block_name.lower() == word.lower():
                    col = l.index("%")
                    return Location(
                        uri="",
                        range=Range(
                            start=Position(line=i, character=col),
                            end=Position(line=i, character=col + len(sl.split()[0])),
                        ),
                    )

        # Try geometry element symbols
        return self._definition_geometry(lines, position, word)

    def _definition_in_block(
        self,
        lines: List[str],
        position: Position,
        word: str,
    ) -> Optional[Location]:
        """Find definition of a parameter inside a % block."""
        # Find which block we're in
        current_block_start: Optional[int] = None
        for i in range(position.line, -1, -1):
            if lines[i].lstrip().startswith("%"):
                current_block_start = i
                break

        if current_block_start is None:
            return None

        # Search for the first occurrence of this parameter in the block
        word_lower = word.lower()
        for i in range(current_block_start, len(lines)):
            stripped = lines[i].strip()
            if stripped.startswith("end") and i > current_block_start:
                break
            for m in _WORD_RE.finditer(lines[i]):
                if m.group().lower() == word_lower and m.start() < lines[i].lstrip().find(" ") if " " in lines[i].lstrip() else True:
                    return Location(
                        uri="",
                        range=Range(
                            start=Position(line=i, character=m.start()),
                            end=Position(line=i, character=m.end()),
                        ),
                    )
        return None

    def _definition_geometry(
        self,
        lines: List[str],
        position: Position,
        word: str,
    ) -> Optional[Location]:
        """Find definition in geometry section."""
        word_upper = word.upper()
        # Find geometry section
        in_geom = False
        for i, l in enumerate(lines):
            stripped = l.strip()
            if stripped.startswith("*") and "xyz" in stripped.lower():
                in_geom = True
                continue
            if in_geom and stripped.startswith("*"):
                break
            if in_geom and i == position.line:
                continue  # skip current line
            if in_geom:
                parts = stripped.split()
                if parts and parts[0].upper() == word_upper:
                    col = l.index(parts[0])
                    return Location(
                        uri="",
                        range=Range(
                            start=Position(line=i, character=col),
                            end=Position(line=i, character=col + len(parts[0])),
                        ),
                    )
        return None


# ------------------------------------------------------------------
# HoverProvider
# ------------------------------------------------------------------

class HoverProvider:
    """Provides hover information for ORCA input files."""

    def __init__(self, parser: ORCAParser) -> None:
        self._parser = parser

    def get_hover(self, text: str, position: Position) -> Optional[Hover]:
        """Return hover documentation for the symbol at *position*."""
        lines = text.splitlines()
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        word = _word_at_line(line, position.character)
        if not word:
            return None

        word_upper = word.upper()
        word_lower = word.lower()

        # Check keywords.py for documentation
        from ..keywords import (
            DFT_FUNCTIONALS,
            WAVEFUNCTION_METHODS,
            BASIS_SETS,
            JOB_TYPES,
        )

        # Check DFT functionals
        if word_upper in DFT_FUNCTIONALS:
            info = DFT_FUNCTIONALS[word_upper]
            desc = info if isinstance(info, str) else "Density functional method"
            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=f"**{word}** (DFT Functional)\n\n{desc}"),
                range=Range(
                    start=Position(line=position.line, character=0),
                    end=Position(line=position.line, character=len(line)),
                ),
            )

        # Check wavefunction methods
        if word_upper in WAVEFUNCTION_METHODS:
            desc = WAVEFUNCTION_METHODS.get(word_upper, "Electronic structure method")
            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=f"**{word}** (Wavefunction Method)\n\n{desc}"),
                range=Range(
                    start=Position(line=position.line, character=0),
                    end=Position(line=position.line, character=len(line)),
                ),
            )

        # Check job types
        if word_upper in JOB_TYPES:
            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=f"**{word}** (Job Type)\n\n{JOB_TYPES[word_upper]}"),
                range=Range(
                    start=Position(line=position.line, character=0),
                    end=Position(line=position.line, character=len(line)),
                ),
            )

        # Check basis sets
        if word_upper in BASIS_SETS:
            return Hover(
                contents=MarkupContent(kind=MarkupKind.Markdown, value=f"**{word}** (Basis Set)\n\n{BASIS_SETS[word_upper]}"),
                range=Range(
                    start=Position(line=position.line, character=0),
                    end=Position(line=position.line, character=len(line)),
                ),
            )

        # % block hover
        stripped = line.lstrip()
        if stripped.startswith("%"):
            block_name = stripped[1:].split()[0].rstrip("{").lower()
            descriptions = {
                "scf": "SCF convergence and algorithm settings",
                "method": "Computational method configuration",
                "basis": "Basis set configuration",
                "rel": "Relativistic corrections",
                "dft": "DFT-specific settings (grid, functional overrides)",
                "output": "Output control (print level, format)",
                "pal": "Parallel execution settings (nproc)",
                "maxcore": "Memory allocation per core (MB)",
                "mp2": "MP2 correlation settings",
                "cipsi": "CIPSI selected configuration interaction",
                "casscf": "Complete active space SCF",
                "nept": "NEPT (N-electron valence perturbation theory)",
                "md": "Molecular dynamics settings",
                "geom": "Geometry optimization settings",
                "freq": "Frequency analysis settings",
                "tddft": "Time-dependent DFT settings",
                "eprnmr": "EPR/NMR property settings",
                "rirpa": "RI-RPA correlation settings",
            }
            if block_name in descriptions:
                return Hover(
                    contents=MarkupContent(kind=MarkupKind.Markdown, value=f"**%{block_name}**\n\n{descriptions[block_name]}"),
                    range=Range(
                        start=Position(line=position.line, character=0),
                        end=Position(line=position.line, character=len(line)),
                    ),
                )

        return None


# ------------------------------------------------------------------
# ReferencesProvider
# ------------------------------------------------------------------

class ReferencesProvider:
    """Provides find-references for ORCA input files."""

    def __init__(self, parser: ORCAParser) -> None:
        self._parser = parser

    def get_references(
        self,
        text: str,
        uri: str,
        position: Position,
        include_declaration: bool = True,
    ) -> List[Location]:
        """Return all references to the symbol at *position*."""
        lines = text.splitlines()
        if position.line >= len(lines):
            return []

        line = lines[position.line]
        word = _word_at_line(line, position.character)
        if not word:
            return []

        word_lower = word.lower()
        locations: List[Location] = []

        # Find all occurrences of the word in the file
        for i, l in enumerate(lines):
            for m in _WORD_RE.finditer(l):
                if m.group().lower() == word_lower:
                    # Exact case-insensitive match
                    if not include_declaration and i == position.line and m.start() == position.character:
                        continue
                    locations.append(
                        Location(
                            uri=uri,
                            range=Range(
                                start=Position(line=i, character=m.start()),
                                end=Position(line=i, character=m.end()),
                            ),
                        )
                    )

        return locations
