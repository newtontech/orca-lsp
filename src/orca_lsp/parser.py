"""ORCA input file parser"""

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .keywords import (
    BASIS_SETS,
    DFT_FUNCTIONALS,
    ELEMENTS,
    JOB_TYPES,
    WAVEFUNCTION_METHODS,
)
from .validator import ORCAValidator

# Pre-compiled regex patterns for performance (avoid recompilation on every loop)
_NPROCS_RE = re.compile(r"nprocs\s+(\d+)", re.IGNORECASE)
_MAXITER_RE = re.compile(r"maxiter\s+(\d+)", re.IGNORECASE)
_GTENSOR_RE = re.compile(r"gtensor\s+(\d+)", re.IGNORECASE)
_NROOTS_RE = re.compile(r"nroots\s+(\d+)", re.IGNORECASE)


@dataclass
class SimpleInput:
    """Parsed simple input line (!)"""

    methods: List[str] = field(default_factory=list)
    basis_sets: List[str] = field(default_factory=list)
    job_types: List[str] = field(default_factory=list)
    other_keywords: List[str] = field(default_factory=list)
    raw: str = ""
    line_number: int = 0

    def is_valid(self) -> bool:
        """Check if simple input has required components"""
        return len(self.methods) > 0 or len(self.basis_sets) > 0


@dataclass
class PercentBlock:
    """Parsed % block"""

    name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""
    line_start: int = 0
    line_end: int = 0

    def is_valid(self) -> bool:
        """Check if % block is valid"""
        return bool(self.name)


@dataclass
class Atom:
    """Represents an atom in geometry"""

    element: str = ""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    line_number: int = 0

    def is_valid(self) -> bool:
        """Check if atom data is valid"""
        return self.element in ELEMENTS


@dataclass
class Geometry:
    """Parsed geometry section (* xyz ... *)"""

    charge: int = 0
    multiplicity: int = 1
    atoms: List[Atom] = field(default_factory=list)
    format_type: str = "xyz"  # xyz, int, etc.
    line_start: int = 0
    line_end: int = 0

    def is_valid(self) -> bool:
        """Check if geometry section is valid"""
        return len(self.atoms) > 0 and all(atom.is_valid() for atom in self.atoms)


@dataclass
class ParseResult:
    """Complete parse result for an ORCA input file"""

    simple_input: Optional[SimpleInput] = None
    percent_blocks: List[PercentBlock] = field(default_factory=list)
    geometry: Optional[Geometry] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)


class ORCAParser:
    """Parser for ORCA input files"""

    def __init__(self) -> None:
        self.dft_functionals = set(DFT_FUNCTIONALS.keys())
        self.wavefunction_methods = set(WAVEFUNCTION_METHODS.keys())
        self.basis_sets = set(BASIS_SETS.keys())
        self.job_types = set(JOB_TYPES.keys())
        self.all_methods = self.dft_functionals | self.wavefunction_methods
        self._dft_functionals_by_upper = {name.upper(): name for name in self.dft_functionals}
        self._wavefunction_methods_by_upper = {
            name.upper(): name for name in self.wavefunction_methods
        }
        self._basis_sets_by_upper = {name.upper(): name for name in self.basis_sets}
        self._job_types_by_upper = {name.upper(): name for name in self.job_types}
        self._validator = ORCAValidator()

        # Registry mapping block names to parameter handlers (OCP: extensible without modification)
        self._block_handlers: Dict[str, Callable[[PercentBlock, str], None]] = {
            "maxcore": self._parse_maxcore,
            "method": self._parse_method,
            "pal": self._parse_pal,
            "scf": self._parse_scf,
            "eprnmr": self._parse_eprnmr,
            "rirpa": self._parse_rirpa,
        }

    def parse(self, content: str) -> ParseResult:
        """Parse complete ORCA input file"""
        result = ParseResult()
        lines = content.split("\n")

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                i += 1
                continue

            # Parse simple input line (!)
            if stripped.startswith("!"):
                result.simple_input = self.parse_simple_input(stripped, i)
                i += 1
                continue

            # Parse % blocks
            if stripped.startswith("%"):
                block, end_line = self.parse_percent_block(lines, i)
                if block:
                    result.percent_blocks.append(block)
                i = end_line + 1
                continue

            # Parse geometry section
            if stripped.startswith("*"):
                geom, end_line = self.parse_geometry(lines, i)
                if geom:
                    result.geometry = geom
                i = end_line + 1
                continue

            i += 1

        # Run diagnostics via separate validator
        self._validator.validate(result)

        return result

    def parse_simple_input(self, line: str, line_number: int) -> SimpleInput:
        """Parse simple input line starting with !"""
        result = SimpleInput(raw=line, line_number=line_number)

        # Remove leading ! and strip inline comments (a second ! starts a comment)
        content = line[1:].strip()
        comment_pos = content.find("!")
        if comment_pos >= 0:
            content = content[:comment_pos].strip()

        tokens = content.split()

        for token in tokens:
            token_upper = token.upper()

            if token_upper in self._dft_functionals_by_upper:
                result.methods.append(self._dft_functionals_by_upper[token_upper])
            elif token_upper in self._wavefunction_methods_by_upper:
                result.methods.append(self._wavefunction_methods_by_upper[token_upper])
            elif token_upper in self._basis_sets_by_upper:
                result.basis_sets.append(self._basis_sets_by_upper[token_upper])
            elif token_upper in self._job_types_by_upper:
                result.job_types.append(self._job_types_by_upper[token_upper])
            else:
                result.other_keywords.append(token)

        return result

    def parse_percent_block(
        self, lines: List[str], start_line: int
    ) -> Tuple[Optional[PercentBlock], int]:
        """Parse a % block starting at start_line"""
        block = PercentBlock(line_start=start_line)

        first_line = lines[start_line].strip()

        # Extract block name
        match = re.match(r"%\s*(\w+)", first_line)
        if match:
            block.name = match.group(1).lower()
        else:
            return None, start_line

        # Check if block contains 'end' on the same line
        if " end" in first_line.lower() or first_line.lower().endswith("end"):
            block.raw_content = first_line
            block.line_end = start_line
            # Parse parameters from single line
            self._parse_block_parameters(block, first_line)
            return block, start_line

        # Check if this is a single-line assignment (e.g., %maxcore 4000)
        # These don't have 'end' and are complete on one line
        parts = first_line.split()
        if len(parts) == 2 and not parts[1].lower() == "end":
            try:
                # Try to parse as a value
                int(parts[1])
                block.raw_content = first_line
                block.line_end = start_line
                self._parse_block_parameters(block, first_line)
                return block, start_line
            except ValueError:
                pass

        # Multi-line block - look for 'end'
        content_lines = [first_line]
        i = start_line + 1

        while i < len(lines):
            line = lines[i]
            content_lines.append(line)

            stripped = line.strip().lower()
            if stripped == "end" or stripped.endswith(" end"):
                block.line_end = i
                break
            i += 1
        else:
            # No 'end' found, treat as single line
            block.line_end = start_line
            content_lines = [first_line]

        block.raw_content = "\n".join(content_lines)

        # Parse block-specific parameters
        self._parse_block_parameters(block, block.raw_content)

        return block, block.line_end

    def _parse_block_parameters(self, block: PercentBlock, content: str) -> None:
        """Parse parameters for a % block using a handler registry."""
        handler = self._block_handlers.get(block.name)
        if handler is not None:
            handler(block, content)

    @staticmethod
    def _parse_regex_param(
        block: PercentBlock,
        content: str,
        keyword: str,
        pattern: "re.Pattern[str]",
        param_name: str,
    ) -> None:
        """Extract an integer parameter matching a regex pattern."""
        for line in content.split("\n"):
            if keyword in line.lower():
                match = pattern.search(line)
                if match:
                    block.parameters[param_name] = int(match.group(1))

    @staticmethod
    def _parse_maxcore(block: PercentBlock, content: str) -> None:
        """Parse %maxcore block parameters."""
        for line in content.split("\n"):
            parts = line.split()
            if len(parts) >= 2 and parts[0].lower() == "%maxcore":
                try:
                    block.parameters["memory"] = int(parts[1])
                except ValueError:
                    pass

    @staticmethod
    def _parse_method(block: PercentBlock, content: str) -> None:
        """Parse %method block parameters."""
        for line in content.split("\n"):
            stripped = line.strip().lower()
            if "d3bj" in stripped:
                block.parameters["dispersion"] = "D3BJ"
            elif "d3" in stripped:
                block.parameters["dispersion"] = "D3"
            elif "d4" in stripped:
                block.parameters["dispersion"] = "D4"

    def _parse_pal(self, block: PercentBlock, content: str) -> None:
        """Parse %pal block parameters."""
        self._parse_regex_param(block, content, "nprocs", _NPROCS_RE, "nprocs")

    def _parse_scf(self, block: PercentBlock, content: str) -> None:
        """Parse %scf block parameters."""
        self._parse_regex_param(block, content, "maxiter", _MAXITER_RE, "maxiter")

    def _parse_eprnmr(self, block: PercentBlock, content: str) -> None:
        """Parse %eprnmr block parameters."""
        self._parse_regex_param(block, content, "gtensor", _GTENSOR_RE, "gtensor")

    def _parse_rirpa(self, block: PercentBlock, content: str) -> None:
        """Parse %rirpa block parameters."""
        self._parse_regex_param(block, content, "nroots", _NROOTS_RE, "nroots")

    def parse_geometry(self, lines: List[str], start_line: int) -> Tuple[Optional[Geometry], int]:
        """Parse geometry section (* xyz ... *)"""
        geom = Geometry(line_start=start_line)

        first_line = lines[start_line].strip()

        # Parse header: * xyz charge multiplicity
        # or * int charge multiplicity for internal coordinates
        parts = first_line.split()

        if len(parts) < 2:
            return None, start_line

        # Check format type
        geom.format_type = parts[1].lower() if len(parts) > 1 else "xyz"

        # Parse charge and multiplicity
        if len(parts) >= 4:
            try:
                geom.charge = int(parts[2])
                geom.multiplicity = int(parts[3])
            except ValueError:
                pass

        # Parse atom lines
        i = start_line + 1
        while i < len(lines):
            line = lines[i].strip()

            # End of geometry (bare * or * with trailing text like "* end")
            if line == "*" or line.startswith("* "):
                geom.line_end = i
                break

            # Skip empty lines within geometry block
            if not line:
                i += 1
                continue

            # Strip inline comments from atom lines (e.g., "H 0.0 0.0 0.0 ! hydrogen")
            comment_pos = line.find("!")
            if comment_pos >= 0:
                line = line[:comment_pos].strip()

            # Parse atom
            atom_parts = line.split()
            if len(atom_parts) >= 4:
                try:
                    atom = Atom(
                        element=atom_parts[0],
                        x=float(atom_parts[1]),
                        y=float(atom_parts[2]),
                        z=float(atom_parts[3]),
                        line_number=i,
                    )
                    geom.atoms.append(atom)
                except ValueError:
                    pass

            i += 1

        return geom, geom.line_end if geom.line_end > 0 else i
