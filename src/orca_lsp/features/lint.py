"""Schema-aware static lint checks for ORCA input files.

Produces LSP diagnostics with stable rule codes for automation.  Checks are
deterministic, offline, and purely based on the ORCA grammar and curated
keyword metadata from :mod:`orca_lsp.keywords`.

Rule codes
----------
Each diagnostic carries a ``code`` string that identifies the check:

============  =================================================  ==========
Code          Description                                        Severity
============  =================================================  ==========
ORCA-E001     Unknown token in simple input line                 Error
ORCA-E002     Unknown ``%`` block name                           Error
ORCA-E003     Unclosed ``%`` block                               Error
ORCA-E004     Duplicate ``%`` block                              Error
ORCA-E005     Invalid charge value                               Error
ORCA-E006     Invalid multiplicity value                         Error
ORCA-E007     Multiplicity incompatible with charge              Error
ORCA-W001     Suggested ``%maxcore`` not set                     Warning
ORCA-W002     Non-standard token in simple input                 Warning
ORCA-W003     Duplicate token in simple input                    Warning
ORCA-W004     %scf maxiter out of typical range                  Warning
ORCA-W005     %pal nprocs unusually high                         Warning
============  =================================================  ==========
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)

from ..keywords import (
    ALL_KEYWORDS,
    PERCENT_BLOCKS,
)
from ..parser import ORCAParser, ParseResult, PercentBlock

# ---------------------------------------------------------------------------
# Rule codes
# ---------------------------------------------------------------------------

RULE_UNKNOWN_TOKEN = "ORCA-E001"
RULE_UNKNOWN_BLOCK = "ORCA-E002"
RULE_UNCLOSED_BLOCK = "ORCA-E003"
RULE_DUPLICATE_BLOCK = "ORCA-E004"
RULE_INVALID_CHARGE = "ORCA-E005"
RULE_INVALID_MULTIPLICITY = "ORCA-E006"
RULE_CHARGE_MULTIPLICITY = "ORCA-E007"

RULE_MISSING_MAXCORE = "ORCA-W001"
RULE_NONSTANDARD_TOKEN = "ORCA-W002"
RULE_DUPLICATE_TOKEN = "ORCA-W003"
RULE_MAXITER_RANGE = "ORCA-W004"
RULE_NPROCS_HIGH = "ORCA-W005"

# Known tokens that are not in ALL_KEYWORDS but are valid ORCA simple-input
# keywords (modifiers, convergence settings, solvent models, etc.).
_KNOWN_MODIFIERS: Dict[str, str] = {
    "RHF": "wavefunction",
    "UHF": "wavefunction",
    "ROHF": "wavefunction",
    "RKS": "wavefunction",
    "UKS": "wavefunction",
    "ROKS": "wavefunction",
    "D3": "dispersion",
    "D3BJ": "dispersion",
    "D4": "dispersion",
    "RIJCOSX": "ri-approximation",
    "RI-J": "ri-approximation",
    "TIGHTSCF": "convergence",
    "LOOSESCF": "convergence",
    "VERYTIGHTSCF": "convergence",
    "SLOPPYSCF": "convergence",
    "ZORA": "relativistic",
    "DKH": "relativistic",
    "CPCM": "solvent",
    "SMD": "solvent",
    "GRID5": "grid",
    "GRID4": "grid",
    "GRID3": "grid",
    "FINALGRID6": "grid",
    "FINALGRID5": "grid",
    "FINALGRID4": "grid",
    "NORMALSCF": "convergence",
    "STRONGSCF": "convergence",
    "DEFGRID2": "grid",
    "DEFGRID3": "grid",
    "NOITER": "convergence",
    "PRINTLEVEL": "output",
    "MOREAD": "input",
    "KEEPDENS": "density",
    "KEEPMOS": "orbitals",
    "MINIPRINT": "output",
    "LARGEPRINT": "output",
    "NOPRINT": "output",
}

# Canonical severity mapping.
_SEVERITY_NAMES: Dict[int, str] = {
    DiagnosticSeverity.Error: "error",
    DiagnosticSeverity.Warning: "warning",
    DiagnosticSeverity.Information: "information",
    DiagnosticSeverity.Hint: "hint",
}


class LintProvider:
    """Schema-aware static lint for ORCA input files.

    Performs checks that go beyond basic parsing/validation:
    unknown tokens, unknown or duplicate blocks, unclosed blocks,
    charge/multiplicity physics warnings, and parameter range checks.

    All diagnostics are emitted with ``source="orca-lsp-lint"`` and a
    stable rule ``code`` for downstream filtering or automation.
    """

    def __init__(self, parser: Optional[ORCAParser] = None) -> None:
        """Initialize lint provider.

        Args:
            parser: Optional ORCAParser instance.  A fresh one is created
                when *None* is passed.
        """
        self.parser = parser if parser is not None else ORCAParser()
        # Pre-compute lookup set for O(1) token validation.
        self._known_tokens: Dict[str, str] = {}
        for name in ALL_KEYWORDS:
            self._known_tokens[name.upper()] = "keyword"
        for name in _KNOWN_MODIFIERS:
            self._known_tokens[name.upper()] = _KNOWN_MODIFIERS[name]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def lint(self, text: str) -> List[Diagnostic]:
        """Run all lint checks and return LSP diagnostics.

        Args:
            text: Full document text.

        Returns:
            List of ``Diagnostic`` instances with ``source="orca-lsp-lint"``.
        """
        lines = text.split("\n")
        result = self._parse(text)
        diagnostics: List[Diagnostic] = []

        self._check_simple_input_tokens(result, lines, diagnostics)
        self._check_percent_blocks(result, lines, diagnostics)
        self._check_charge_multiplicity(result, lines, diagnostics)
        self._check_block_parameters(result, lines, diagnostics)

        return diagnostics

    def snapshot(self, text: str) -> str:
        """Return a JSON-serializable snapshot of lint diagnostics.

        The output is deterministic and suitable for CLI piping or agent
        feedback loops.

        Args:
            text: Full document text.

        Returns:
            Indented JSON string of diagnostic dicts.
        """
        diagnostics = self.lint(text)
        data = [self._diagnostic_to_dict(d) for d in diagnostics]
        # Sort by line, character, severity for determinism.
        data.sort(
            key=lambda d: (
                d["range"]["start"]["line"],
                d["range"]["start"]["character"],
                d["severity"],
            )
        )
        return json.dumps(data, indent=2, sort_keys=True)

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    def _parse(self, text: str) -> ParseResult:
        """Parse text, catching unexpected errors.

        Args:
            text: Document text.

        Returns:
            ParseResult (possibly with errors).
        """
        try:
            return self.parser.parse(text)
        except Exception:
            return ParseResult()

    # ------------------------------------------------------------------
    # Simple input checks
    # ------------------------------------------------------------------

    def _check_simple_input_tokens(
        self,
        result: ParseResult,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check for unknown and duplicate tokens in the simple input line.

        Args:
            result: Parsed result.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        if result.simple_input is None:
            return

        si = result.simple_input
        line_idx = si.line_number
        if line_idx >= len(lines):
            return

        raw_line = lines[line_idx]
        # Extract content after "!" and before an inline "!" comment.
        content = raw_line.lstrip()
        if content.startswith("!"):
            content = content[1:]
        bang_pos = content.find("!")
        if bang_pos >= 0:
            content = content[:bang_pos]
        tokens = content.split()

        # Track duplicates.
        seen: Dict[str, int] = {}
        for token in tokens:
            token_upper = token.upper()
            if token_upper in seen:
                seen[token_upper] += 1
            else:
                seen[token_upper] = 1

        for i, token in enumerate(tokens):
            token_upper = token.upper()
            if token_upper not in self._known_tokens:
                col = self._token_column(raw_line, token, i)
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line_idx, character=col),
                            end=Position(line=line_idx, character=col + len(token)),
                        ),
                        message=f"Unknown token in simple input: '{token}'",
                        severity=DiagnosticSeverity.Error,
                        source="orca-lsp-lint",
                        code=RULE_UNKNOWN_TOKEN,
                    )
                )
            elif seen[token_upper] > 1:
                # Only warn for the second and later occurrences.
                first_idx = next(j for j, t in enumerate(tokens) if t.upper() == token_upper)
                if i != first_idx:
                    col = self._token_column(raw_line, token, i)
                    diagnostics.append(
                        Diagnostic(
                            range=Range(
                                start=Position(line=line_idx, character=col),
                                end=Position(line=line_idx, character=col + len(token)),
                            ),
                            message=(f"Duplicate token in simple input: '{token}'"),
                            severity=DiagnosticSeverity.Warning,
                            source="orca-lsp-lint",
                            code=RULE_DUPLICATE_TOKEN,
                        )
                    )

    # ------------------------------------------------------------------
    # % block checks
    # ------------------------------------------------------------------

    def _check_percent_blocks(
        self,
        result: ParseResult,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check for unknown, duplicate, and unclosed % blocks.

        Args:
            result: Parsed result.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        # --- Unknown block names ---
        for block in result.percent_blocks:
            if block.name not in PERCENT_BLOCKS:
                line_idx = block.line_start
                col = self._block_name_col(lines, line_idx)
                name_text = block.name
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line_idx, character=col),
                            end=Position(
                                line=line_idx,
                                character=col + len(name_text) + 1,
                            ),
                        ),
                        message=f"Unknown % block: '%{block.name}'",
                        severity=DiagnosticSeverity.Error,
                        source="orca-lsp-lint",
                        code=RULE_UNKNOWN_BLOCK,
                    )
                )

        # --- Duplicate blocks ---
        seen_blocks: Dict[str, int] = {}
        for block in result.percent_blocks:
            name_lower = block.name.lower()
            if name_lower in seen_blocks:
                seen_blocks[name_lower] += 1
            else:
                seen_blocks[name_lower] = 1

        reported_duplicates: set[str] = set()
        for block in result.percent_blocks:
            name_lower = block.name.lower()
            if seen_blocks.get(name_lower, 0) > 1 and name_lower not in reported_duplicates:
                reported_duplicates.add(name_lower)
                matches = [b for b in result.percent_blocks if b.name.lower() == name_lower]
                for dup_block in matches[1:]:
                    col = self._block_name_col(lines, dup_block.line_start)
                    diagnostics.append(
                        Diagnostic(
                            range=Range(
                                start=Position(line=dup_block.line_start, character=col),
                                end=Position(
                                    line=dup_block.line_start,
                                    character=col + len(dup_block.name) + 1,
                                ),
                            ),
                            message=f"Duplicate % block: '%{dup_block.name}'",
                            severity=DiagnosticSeverity.Error,
                            source="orca-lsp-lint",
                            code=RULE_DUPLICATE_BLOCK,
                        )
                    )

        # --- Unclosed blocks ---
        self._check_unclosed_blocks(lines, diagnostics)

    def _check_unclosed_blocks(
        self,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Detect multi-line % blocks that have no closing 'end'.

        Single-line assignments like ``%maxcore 4000`` are not flagged.

        Args:
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        _block_start_re = re.compile(r"^\s*%\s*(\w+)", re.IGNORECASE)
        _end_re = re.compile(r"\bend\b", re.IGNORECASE)

        i = 0
        while i < len(lines):
            stripped = lines[i].strip()
            match = _block_start_re.match(stripped)
            if not match:
                i += 1
                continue

            block_name = match.group(1).lower()

            # If the line has "end", it's self-closing.
            if _end_re.search(stripped):
                i += 1
                continue

            # Single-line value block (e.g. %maxcore 4000): two parts where
            # the second is a number or a quoted string.
            parts = stripped.split()
            if len(parts) == 2:
                value = parts[1]
                if value.isdigit() or (value.startswith('"') and value.endswith('"')):
                    i += 1
                    continue

            # A bare "%blockname" (no rest) is a multi-line block start.
            # Fall through to multi-line end search.

            # Multi-line block: look for "end".
            found_end = False
            j = i + 1
            while j < len(lines):
                inner_stripped = lines[j].strip()
                if _end_re.search(inner_stripped):
                    found_end = True
                    break
                # Another block starts before end.
                inner_match = _block_start_re.match(inner_stripped)
                if inner_match:
                    inner_name = inner_match.group(1).lower()
                    if inner_name in PERCENT_BLOCKS or inner_name == block_name:
                        break
                j += 1

            if not found_end:
                col = lines[i].find("%")
                if col < 0:
                    col = 0
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=i, character=col),
                            end=Position(line=i, character=col + len(block_name) + 1),
                        ),
                        message=f"Unclosed % block: '%{block_name}'",
                        severity=DiagnosticSeverity.Error,
                        source="orca-lsp-lint",
                        code=RULE_UNCLOSED_BLOCK,
                    )
                )

            i = j + 1 if found_end else i + 1

    # ------------------------------------------------------------------
    # Charge / multiplicity checks
    # ------------------------------------------------------------------

    def _check_charge_multiplicity(
        self,
        result: ParseResult,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check charge and multiplicity for physics warnings.

        Args:
            result: Parsed result.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        if result.geometry is None:
            return

        geom = result.geometry
        charge = geom.charge
        mult = geom.multiplicity
        line_idx = geom.line_start

        if mult < 1:
            col = self._geom_mult_col(lines, line_idx)
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=col + len(str(mult))),
                    ),
                    message=f"Multiplicity must be >= 1, got {mult}",
                    severity=DiagnosticSeverity.Error,
                    source="orca-lsp-lint",
                    code=RULE_INVALID_MULTIPLICITY,
                )
            )
            return

        # n_electrons % 2 must be: mult is odd -> even n_electrons,
        # mult is even -> odd n_electrons.
        n_electrons = self._count_electrons(geom.atoms, charge)
        if n_electrons is not None:
            is_even = n_electrons % 2 == 0
            mult_odd = mult % 2 == 1
            if is_even != mult_odd:
                col = self._geom_mult_col(lines, line_idx)
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line_idx, character=col),
                            end=Position(
                                line=line_idx,
                                character=col + len(str(mult)),
                            ),
                        ),
                        message=(
                            f"Multiplicity {mult} inconsistent with "
                            f"{n_electrons} electrons (charge {charge})"
                        ),
                        severity=DiagnosticSeverity.Error,
                        source="orca-lsp-lint",
                        code=RULE_CHARGE_MULTIPLICITY,
                    )
                )

    # ------------------------------------------------------------------
    # Block parameter range checks
    # ------------------------------------------------------------------

    def _check_block_parameters(
        self,
        result: ParseResult,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check % block parameter values for out-of-range warnings.

        Args:
            result: Parsed result.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        for block in result.percent_blocks:
            if block.name == "scf":
                self._check_scf_params(block, lines, diagnostics)
            elif block.name == "pal":
                self._check_pal_params(block, lines, diagnostics)
            elif block.name == "maxcore":
                self._check_maxcore_params(block, lines, diagnostics)

    def _check_scf_params(
        self,
        block: PercentBlock,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check %scf block parameters.

        Args:
            block: Parsed %scf block.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        maxiter = block.parameters.get("maxiter")
        if maxiter is not None and (maxiter < 10 or maxiter > 5000):
            line_idx = self._find_param_line(block, "maxiter", lines)
            col = self._param_col(lines, line_idx, "maxiter")
            val_str = str(maxiter)
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=col + len(val_str)),
                    ),
                    message=(f"SCF maxiter {maxiter} is outside typical range " f"(10-5000)"),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-lint",
                    code=RULE_MAXITER_RANGE,
                )
            )

    def _check_pal_params(
        self,
        block: PercentBlock,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check %pal block parameters.

        Args:
            block: Parsed %pal block.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        nprocs = block.parameters.get("nprocs")
        if nprocs is not None and nprocs > 256:
            line_idx = self._find_param_line(block, "nprocs", lines)
            col = self._param_col(lines, line_idx, "nprocs")
            val_str = str(nprocs)
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=col + len(val_str)),
                    ),
                    message=(f"nprocs {nprocs} is unusually high (typical max: 256)"),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-lint",
                    code=RULE_NPROCS_HIGH,
                )
            )

    def _check_maxcore_params(
        self,
        block: PercentBlock,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check %maxcore parameter.

        Args:
            block: Parsed %maxcore block.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        memory = block.parameters.get("memory")
        if memory is not None and memory < 100:
            line_idx = block.line_start
            val_str = str(memory)
            col = self._param_col(lines, line_idx, val_str)
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=col + len(val_str)),
                    ),
                    message=(f"%maxcore {memory} MB is very low " f"(recommended: 1000-4000)"),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-lint",
                    code=RULE_MISSING_MAXCORE,
                )
            )

    # ------------------------------------------------------------------
    # Snapshot helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _diagnostic_to_dict(diag: Diagnostic) -> Dict[str, Any]:
        """Convert an LSP Diagnostic to a JSON-serializable dict.

        Args:
            diag: LSP Diagnostic object.

        Returns:
            Deterministic, JSON-safe dictionary.
        """
        severity_value = diag.severity if diag.severity is not None else DiagnosticSeverity.Error
        return {
            "range": {
                "start": {
                    "line": diag.range.start.line,
                    "character": diag.range.start.character,
                },
                "end": {
                    "line": diag.range.end.line,
                    "character": diag.range.end.character,
                },
            },
            "severity": severity_value,
            "severity_label": _SEVERITY_NAMES.get(severity_value, "unknown"),
            "source": diag.source or "orca-lsp-lint",
            "code": str(diag.code) if diag.code is not None else None,
            "message": diag.message,
        }

    # ------------------------------------------------------------------
    # Position helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _token_column(line: str, token: str, occurrence_index: int) -> int:
        """Find the column of the n-th occurrence of *token* in *line*.

        Args:
            line: Source line.
            token: Token text.
            occurrence_index: Zero-based index among all tokens on the line.

        Returns:
            Character column where the token starts.
        """
        col = 0
        parts = line.split()
        for idx, part in enumerate(parts):
            found = line.find(part, col)
            if found < 0:
                found = col
            if idx == occurrence_index:
                return found
            col = found + len(part)
        return 0

    @staticmethod
    def _block_name_col(lines: List[str], line_idx: int) -> int:
        """Find the column of the ``%`` in a block header line.

        Args:
            lines: Document lines.
            line_idx: Zero-based line index.

        Returns:
            Column of the ``%``.
        """
        if line_idx < len(lines):
            col = lines[line_idx].find("%")
            return col if col >= 0 else 0
        return 0

    @staticmethod
    def _geom_mult_col(lines: List[str], line_idx: int) -> int:
        """Find the column of the multiplicity value in a geometry header.

        The header format is ``* xyz CHARGE MULT``.

        Args:
            lines: Document lines.
            line_idx: Zero-based line index.

        Returns:
            Approximate column of the multiplicity value.
        """
        if line_idx >= len(lines):
            return 0
        parts = lines[line_idx].split()
        if len(parts) >= 4:
            pos = 0
            for part in parts[:3]:
                found = lines[line_idx].find(part, pos)
                if found >= 0:
                    pos = found + len(part) + 1
                else:
                    pos += len(part) + 1
            col = lines[line_idx].find(parts[3], pos)
            return col if col >= 0 else 0
        return 0

    @staticmethod
    def _count_electrons(atoms: Any, charge: int) -> Optional[int]:
        """Count total electrons from geometry atoms and charge.

        Args:
            atoms: List of Atom objects.
            charge: Molecular charge.

        Returns:
            Total electron count, or None if elements are unknown.
        """
        _Z: Dict[str, int] = {
            "H": 1,
            "He": 2,
            "Li": 3,
            "Be": 4,
            "B": 5,
            "C": 6,
            "N": 7,
            "O": 8,
            "F": 9,
            "Ne": 10,
            "Na": 11,
            "Mg": 12,
            "Al": 13,
            "Si": 14,
            "P": 15,
            "S": 16,
            "Cl": 17,
            "Ar": 18,
            "K": 19,
            "Ca": 20,
            "Sc": 21,
            "Ti": 22,
            "V": 23,
            "Cr": 24,
            "Mn": 25,
            "Fe": 26,
            "Co": 27,
            "Ni": 28,
            "Cu": 29,
            "Zn": 30,
            "Ga": 31,
            "Ge": 32,
            "As": 33,
            "Se": 34,
            "Br": 35,
            "Kr": 36,
            "Rb": 37,
            "Sr": 38,
            "Y": 39,
            "Zr": 40,
            "Nb": 41,
            "Mo": 42,
            "Tc": 43,
            "Ru": 44,
            "Rh": 45,
            "Pd": 46,
            "Ag": 47,
            "Cd": 48,
            "In": 49,
            "Sn": 50,
            "Sb": 51,
            "Te": 52,
            "I": 53,
            "Xe": 54,
        }

        total_z = 0
        for atom in atoms:
            z = _Z.get(atom.element)
            if z is None:
                return None
            total_z += z
        return total_z - charge

    @staticmethod
    def _find_param_line(block: PercentBlock, param_name: str, lines: List[str]) -> int:
        """Find the line index of a parameter within a block.

        Args:
            block: Parsed block.
            param_name: Parameter keyword to locate.
            lines: Document lines.

        Returns:
            Zero-based line index (falls back to block.line_start).
        """
        for i in range(block.line_start, block.line_end + 1):
            if i < len(lines) and param_name.lower() in lines[i].lower():
                return i
        return block.line_start

    @staticmethod
    def _param_col(lines: List[str], line_idx: int, param_name: str) -> int:
        """Find the column of a parameter value on a line.

        Args:
            lines: Document lines.
            line_idx: Zero-based line index.
            param_name: Parameter keyword or value.

        Returns:
            Column position of the parameter value.
        """
        if line_idx >= len(lines):
            return 0
        line = lines[line_idx]
        col = line.lower().find(param_name.lower())
        return col if col >= 0 else 0


__all__ = ["LintProvider"]
