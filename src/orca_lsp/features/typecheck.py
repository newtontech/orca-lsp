"""Type-check provider for ORCA input files.

Validates keyword value types, enum choices, units, and required sections
in ORCA input files.  Produces LSP diagnostics with ``source="orca-lsp-typecheck"``
and stable rule codes for downstream filtering.

Rule codes
----------
============  =================================================  ==========
Code          Description                                        Severity
============  =================================================  ==========
TC-E001       Invalid value type for % block parameter            Error
TC-E002       Invalid enum value for keyword                      Error
TC-E003       Invalid unit for keyword                            Error
TC-W001       Missing required section                            Warning
TC-W002       Missing required keyword in simple input            Warning
TC-W003       Non-numeric value where number expected             Warning
============  =================================================  ==========
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set, Tuple

from lsprotocol.types import (
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)

from ..keywords import (
    BASIS_SETS,
    DFT_FUNCTIONALS,
    JOB_TYPES,
    PERCENT_BLOCKS,
    WAVEFUNCTION_METHODS,
)
from ..parser import ORCAParser, ParseResult, PercentBlock

# ---------------------------------------------------------------------------
# Rule codes
# ---------------------------------------------------------------------------

RULE_INVALID_TYPE = "TC-E001"
RULE_INVALID_ENUM = "TC-E002"
RULE_INVALID_UNIT = "TC-E003"
RULE_MISSING_SECTION = "TC-W001"
RULE_MISSING_KEYWORD = "TC-W002"
RULE_NON_NUMERIC = "TC-W003"

# ---------------------------------------------------------------------------
# Type metadata for % block parameters
# ---------------------------------------------------------------------------

# Maps block_name -> param_name -> expected type info
# "type" can be: "int", "float", "bool", "string", "enum"
_BLOCK_PARAM_SCHEMA: Dict[str, Dict[str, Dict[str, Any]]] = {
    "maxcore": {
        "memory": {
            "type": "int",
            "min": 100,
            "max": 64000,
            "unit": "MB",
            "description": "Memory per core in MB",
        },
    },
    "pal": {
        "nprocs": {
            "type": "int",
            "min": 1,
            "max": 256,
            "description": "Number of processors",
        },
    },
    "scf": {
        "maxiter": {
            "type": "int",
            "min": 1,
            "max": 5000,
            "description": "Maximum SCF iterations",
        },
        "convergence": {
            "type": "enum",
            "values": {"tight", "normal", "loose", "sloppy"},
            "description": "SCF convergence level",
        },
    },
    "method": {
        "dispersion": {
            "type": "enum",
            "values": {"D3", "D3BJ", "D4"},
            "description": "Dispersion correction method",
        },
    },
    "eprnmr": {
        "gtensor": {
            "type": "int",
            "min": 0,
            "max": 1,
            "description": "G-tensor calculation flag (0 or 1)",
        },
        "nroots": {
            "type": "int",
            "min": 1,
            "max": 100,
            "description": "Number of roots",
        },
    },
    "rirpa": {
        "nroots": {
            "type": "int",
            "min": 1,
            "max": 200,
            "description": "Number of roots for RI-RPA",
        },
    },
    "cpcm": {
        "epsilon": {
            "type": "float",
            "min": 1.0,
            "max": 200.0,
            "description": "Dielectric constant of solvent",
        },
    },
    "md": {
        "timestep": {
            "type": "float",
            "min": 0.01,
            "max": 100.0,
            "unit": "fs",
            "description": "MD timestep in femtoseconds",
        },
    },
    "freq": {
        "temp": {
            "type": "float",
            "min": 0.0,
            "max": 10000.0,
            "unit": "K",
            "description": "Temperature in Kelvin",
        },
    },
    "output": {
        "xyzfile": {
            "type": "bool",
            "description": "Whether to output XYZ file",
        },
        "density": {
            "type": "bool",
            "description": "Whether to output density",
        },
    },
    "geom": {
        "maxiter": {
            "type": "int",
            "min": 1,
            "max": 1000,
            "description": "Maximum geometry optimization iterations",
        },
    },
}

# Known valid units per block parameter (where applicable)
_VALID_UNITS: Dict[str, Dict[str, Set[str]]] = {
    "maxcore": {
        "memory": {"MB", "GB"},
    },
    "md": {
        "timestep": {"fs", "ps", "au"},
    },
    "freq": {
        "temp": {"K", "C"},
    },
}

# Enum validation sets for simple-input keywords (case-insensitive check)
_METHOD_ENUM: Set[str] = (
    set(DFT_FUNCTIONALS.keys()) | set(WAVEFUNCTION_METHODS.keys())
)
_METHOD_ENUM_UPPER: Set[str] = {m.upper() for m in _METHOD_ENUM}

_BASIS_ENUM_UPPER: Set[str] = {b.upper() for b in BASIS_SETS.keys()}

_JOB_TYPE_ENUM_UPPER: Set[str] = {j.upper() for j in JOB_TYPES.keys()}

_DISPERSION_ENUM_UPPER: Set[str] = {"D3", "D3BJ", "D4"}

_SOLVENT_ENUM_UPPER: Set[str] = {"CPCM", "SMD"}

_SCF_CONV_ENUM_UPPER: Set[str] = {
    "TIGHTSCF", "LOOSESCF", "VERYTIGHTSCF", "SLOPPYSCF", "NORMALSCF",
}

_BOOLEAN_STRINGS: Set[str] = {"true", "false", "1", "0", "yes", "no"}

# All known simple-input modifiers (not in method/basis/job dictionaries)
_KNOWN_MODIFIERS_UPPER: Set[str] = {
    "RIJCOSX", "RI-J", "GRID3", "GRID4", "GRID5",
    "FINALGRID4", "FINALGRID5", "FINALGRID6",
    "DEFGRID2", "DEFGRID3", "NOITER",
    "PRINTLEVEL", "MOREAD", "KEEPDENS", "KEEPMOS",
    "MINIPRINT", "LARGEPRINT", "NOPRINT",
    "DFT", "RKS", "UKS", "ROKS",
    "ZORA", "DKH",
    "RHF", "UHF", "ROHF",
}

# Regex for extracting block parameter assignments
_PARAM_ASSIGNMENT_RE = re.compile(
    r"^\s*(\w+)\s+(.+?)(?:\s+#.*)?$", re.IGNORECASE
)

# Regex for matching a unit suffix like "MB", "GB", "K", "fs", "ps"
_UNIT_SUFFIX_RE = re.compile(r"^(-?[\d.]+)\s*([A-Za-z]+)$")


class TypecheckProvider:
    """Type-checking validation for ORCA input files.

    Validates:
    - Scalar types for % block parameters (int, float, bool, string, enum)
    - Enum values for methods, basis sets, job types, and simple-input modifiers
    - Units where applicable (memory, temperature, timestep)
    - Required sections and keywords

    All diagnostics use ``source="orca-lsp-typecheck"`` with stable rule codes.
    """

    def __init__(self, parser: Optional[ORCAParser] = None) -> None:
        """Initialize typecheck provider.

        Args:
            parser: Optional ORCAParser instance.  A fresh one is created
                when *None* is passed.
        """
        self.parser = parser if parser is not None else ORCAParser()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def typecheck(self, text: str) -> List[Diagnostic]:
        """Run all type checks and return LSP diagnostics.

        Args:
            text: Full document text.

        Returns:
            List of ``Diagnostic`` instances with ``source="orca-lsp-typecheck"``.
        """
        lines = text.split("\n")
        result = self._parse(text)
        diagnostics: List[Diagnostic] = []

        self._check_simple_input_enums(result, lines, diagnostics)
        self._check_block_value_types(result, lines, diagnostics)
        self._check_units(result, lines, diagnostics)
        self._check_required_sections(result, lines, diagnostics)

        return diagnostics

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
    # Simple-input enum validation
    # ------------------------------------------------------------------

    def _check_simple_input_enums(
        self,
        result: ParseResult,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate enum values in the simple input line.

        Checks methods, basis sets, job types, dispersion corrections,
        solvent models, and SCF convergence settings.

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
        content = raw_line.lstrip()
        if content.startswith("!"):
            content = content[1:]
        bang_pos = content.find("!")
        if bang_pos >= 0:
            content = content[:bang_pos]
        tokens = content.split()

        # Validate tokens -- check for unknown tokens with suggestions
        for i, token in enumerate(tokens):
            token_upper = token.upper()

            # Skip known valid categories
            if token_upper in _METHOD_ENUM_UPPER:
                continue
            if token_upper in _BASIS_ENUM_UPPER:
                continue
            if token_upper in _JOB_TYPE_ENUM_UPPER:
                continue
            if token_upper in _DISPERSION_ENUM_UPPER:
                continue
            if token_upper in _SOLVENT_ENUM_UPPER:
                continue
            if token_upper in _SCF_CONV_ENUM_UPPER:
                continue
            if token_upper in _KNOWN_MODIFIERS_UPPER:
                continue

            # Check if it looks like a misspelled method, basis set, or job type
            suggestion = self._find_similar(token_upper)
            if suggestion is not None:
                col = self._token_column(raw_line, token, i)
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(line=line_idx, character=col),
                            end=Position(
                                line=line_idx, character=col + len(token)
                            ),
                        ),
                        message=(
                            f"Unknown keyword '{token}'. "
                            f"Did you mean '{suggestion}'?"
                        ),
                        severity=DiagnosticSeverity.Error,
                        source="orca-lsp-typecheck",
                        code=RULE_INVALID_ENUM,
                    )
                )

    def _find_similar(self, token_upper: str) -> Optional[str]:
        """Find a similar known keyword using edit distance heuristic.

        Args:
            token_upper: Uppercase token to look up.

        Returns:
            Best matching known keyword if close enough, else None.
        """
        candidates: List[Tuple[int, str]] = []
        all_known = (
            _METHOD_ENUM_UPPER | _BASIS_ENUM_UPPER | _JOB_TYPE_ENUM_UPPER
        )
        for known in all_known:
            dist = self._levenshtein(token_upper, known)
            if dist <= max(2, len(token_upper) // 3):
                candidates.append((dist, known))

        if candidates:
            candidates.sort()
            return candidates[0][1]
        return None

    @staticmethod
    def _levenshtein(s1: str, s2: str) -> int:
        """Compute Levenshtein distance between two strings.

        Args:
            s1: First string.
            s2: Second string.

        Returns:
            Edit distance.
        """
        if len(s1) < len(s2):
            return TypecheckProvider._levenshtein(s2, s1)

        if len(s2) == 0:
            return len(s1)

        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (0 if c1 == c2 else 1)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row

        return prev_row[-1]

    # ------------------------------------------------------------------
    # % block value type validation
    # ------------------------------------------------------------------

    def _check_block_value_types(
        self,
        result: ParseResult,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate value types for % block parameters.

        Handles three block formats:
        1. Single-line value blocks: ``%maxcore 4000``
        2. Inline parameter blocks: ``%pal nprocs 4 end``
        3. Multi-line blocks: ``%scf\\n  maxiter 150\\nend``

        Args:
            result: Parsed result.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        for block in result.percent_blocks:
            schema = _BLOCK_PARAM_SCHEMA.get(block.name)
            if schema is None:
                continue

            # Check if this is a single-line value block (e.g. %maxcore 4000)
            first_line = block.raw_content.split("\n")[0].strip()
            self._check_single_line_block(
                block, first_line, schema, lines, diagnostics,
            )

            # Check multi-line content (lines not starting with %)
            block_lines = block.raw_content.split("\n")
            for rel_line_idx, bline in enumerate(block_lines):
                stripped = bline.strip()
                if not stripped or stripped.startswith("%"):
                    continue

                # Only process parameter assignment lines
                match = _PARAM_ASSIGNMENT_RE.match(stripped)
                if not match:
                    continue

                param_name_raw = match.group(1)
                param_value_raw = match.group(2).strip()
                param_name_lower = param_name_raw.lower()

                param_schema = schema.get(param_name_lower)
                if param_schema is None:
                    continue

                expected_type = param_schema.get("type")
                abs_line_idx = block.line_start + rel_line_idx

                self._validate_param_value(
                    param_name_raw,
                    param_value_raw,
                    param_schema,
                    expected_type,
                    abs_line_idx,
                    block.name,
                    lines,
                    diagnostics,
                )

    def _check_single_line_block(
        self,
        block: PercentBlock,
        first_line: str,
        schema: Dict[str, Dict[str, Any]],
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate single-line value blocks like %maxcore 4000.

        Also handles inline parameter blocks like %pal nprocs 4 end.

        Args:
            block: Parsed block.
            first_line: First line of the block content.
            schema: Block parameter schema.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        # Extract content after %blockname
        match = re.match(r"%\s*(\w+)(.*)", first_line, re.IGNORECASE)
        if not match:
            return

        rest = match.group(2).strip()
        if not rest:
            return

        # Remove trailing "end"
        rest_clean = re.sub(r"\bend\s*$", "", rest, flags=re.IGNORECASE).strip()
        if not rest_clean:
            return

        # Try to match as a single value (e.g. %maxcore 4000)
        parts = rest_clean.split(None, 1)
        if len(parts) == 1:
            # Single value -- look for the first schema param
            for param_name, param_schema in schema.items():
                expected_type = param_schema.get("type")
                if expected_type in ("int", "float"):
                    self._validate_param_value(
                        param_name,
                        parts[0],
                        param_schema,
                        expected_type,
                        block.line_start,
                        block.name,
                        lines,
                        diagnostics,
                    )
                    break
        elif len(parts) == 2:
            # Could be "paramname value" inline (e.g. nprocs 4)
            param_name_raw = parts[0]
            param_value_raw = parts[1].strip()
            param_name_lower = param_name_raw.lower()
            param_schema = schema.get(param_name_lower)
            if param_schema is not None:
                expected_type = param_schema.get("type")
                self._validate_param_value(
                    param_name_raw,
                    param_value_raw,
                    param_schema,
                    expected_type,
                    block.line_start,
                    block.name,
                    lines,
                    diagnostics,
                )
            else:
                # Single value with a compound argument
                for pname, pschema in schema.items():
                    etype = pschema.get("type")
                    if etype in ("int", "float"):
                        self._validate_param_value(
                            pname,
                            rest_clean,
                            pschema,
                            etype,
                            block.line_start,
                            block.name,
                            lines,
                            diagnostics,
                        )
                        break

    def _validate_param_value(
        self,
        param_name: str,
        param_value: str,
        schema: Dict[str, Any],
        expected_type: str,
        line_idx: int,
        block_name: str,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate a single parameter value against its schema.

        Args:
            param_name: Parameter name as written.
            param_value: Raw value string.
            schema: Parameter schema dict.
            expected_type: Expected type string ("int", "float", etc.).
            line_idx: Absolute line index.
            block_name: Parent block name.
            lines: All document lines.
            diagnostics: Accumulator for diagnostics.
        """
        col = self._find_value_col(lines, line_idx, param_name, param_value)
        val_end_col = col + len(param_value)

        if expected_type == "int":
            self._validate_int(
                param_value, param_name, schema, line_idx, col,
                val_end_col, block_name, diagnostics,
            )
        elif expected_type == "float":
            self._validate_float(
                param_value, param_name, schema, line_idx, col,
                val_end_col, block_name, diagnostics,
            )
        elif expected_type == "bool":
            self._validate_bool(
                param_value, param_name, line_idx, col,
                val_end_col, diagnostics,
            )
        elif expected_type == "enum":
            self._validate_enum(
                param_value, param_name, schema, line_idx, col,
                val_end_col, diagnostics,
            )

    def _validate_int(
        self,
        value: str,
        param_name: str,
        schema: Dict[str, Any],
        line_idx: int,
        col: int,
        end_col: int,
        block_name: str,
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate an integer parameter value.

        Args:
            value: Raw value string.
            param_name: Parameter name.
            schema: Parameter schema.
            line_idx: Line index.
            col: Start column.
            end_col: End column.
            block_name: Parent block name.
            diagnostics: Accumulator for diagnostics.
        """
        # Strip unit suffix if present
        stripped = self._strip_unit(value, block_name, param_name.lower())
        try:
            int_val = int(float(stripped))
        except (ValueError, TypeError):
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=end_col),
                    ),
                    message=(
                        f"Expected integer for '%{block_name} {param_name}', "
                        f"got '{value}'"
                    ),
                    severity=DiagnosticSeverity.Error,
                    source="orca-lsp-typecheck",
                    code=RULE_INVALID_TYPE,
                )
            )
            return

        min_val = schema.get("min")
        max_val = schema.get("max")
        if min_val is not None and int_val < min_val:
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=end_col),
                    ),
                    message=(
                        f"Value {int_val} for '{param_name}' is below "
                        f"minimum {min_val}"
                    ),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-typecheck",
                    code=RULE_NON_NUMERIC,
                )
            )
        if max_val is not None and int_val > max_val:
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=end_col),
                    ),
                    message=(
                        f"Value {int_val} for '{param_name}' is above "
                        f"maximum {max_val}"
                    ),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-typecheck",
                    code=RULE_NON_NUMERIC,
                )
            )

    def _validate_float(
        self,
        value: str,
        param_name: str,
        schema: Dict[str, Any],
        line_idx: int,
        col: int,
        end_col: int,
        block_name: str,
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate a float parameter value.

        Args:
            value: Raw value string.
            param_name: Parameter name.
            schema: Parameter schema.
            line_idx: Line index.
            col: Start column.
            end_col: End column.
            block_name: Parent block name.
            diagnostics: Accumulator for diagnostics.
        """
        stripped = self._strip_unit(value, block_name, param_name.lower())
        try:
            float_val = float(stripped)
        except (ValueError, TypeError):
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=end_col),
                    ),
                    message=(
                        f"Expected number for '%{block_name} {param_name}', "
                        f"got '{value}'"
                    ),
                    severity=DiagnosticSeverity.Error,
                    source="orca-lsp-typecheck",
                    code=RULE_INVALID_TYPE,
                )
            )
            return

        min_val = schema.get("min")
        max_val = schema.get("max")
        if min_val is not None and float_val < min_val:
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=end_col),
                    ),
                    message=(
                        f"Value {float_val} for '{param_name}' is below "
                        f"minimum {min_val}"
                    ),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-typecheck",
                    code=RULE_NON_NUMERIC,
                )
            )
        if max_val is not None and float_val > max_val:
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=end_col),
                    ),
                    message=(
                        f"Value {float_val} for '{param_name}' is above "
                        f"maximum {max_val}"
                    ),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-typecheck",
                    code=RULE_NON_NUMERIC,
                )
            )

    def _validate_bool(
        self,
        value: str,
        param_name: str,
        line_idx: int,
        col: int,
        end_col: int,
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate a boolean parameter value.

        Args:
            value: Raw value string.
            param_name: Parameter name.
            line_idx: Line index.
            col: Start column.
            end_col: End column.
            diagnostics: Accumulator for diagnostics.
        """
        if value.lower() not in _BOOLEAN_STRINGS:
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=end_col),
                    ),
                    message=(
                        f"Expected boolean (true/false) for '{param_name}', "
                        f"got '{value}'"
                    ),
                    severity=DiagnosticSeverity.Error,
                    source="orca-lsp-typecheck",
                    code=RULE_INVALID_TYPE,
                )
            )

    def _validate_enum(
        self,
        value: str,
        param_name: str,
        schema: Dict[str, Any],
        line_idx: int,
        col: int,
        end_col: int,
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate an enum parameter value.

        Args:
            value: Raw value string.
            param_name: Parameter name.
            schema: Parameter schema with "values" set.
            line_idx: Line index.
            col: Start column.
            end_col: End column.
            diagnostics: Accumulator for diagnostics.
        """
        valid_values = schema.get("values", set())
        if value.upper() not in {v.upper() for v in valid_values}:
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(line=line_idx, character=end_col),
                    ),
                    message=(
                        f"Invalid value '{value}' for '{param_name}'. "
                        f"Expected one of: {', '.join(sorted(valid_values))}"
                    ),
                    severity=DiagnosticSeverity.Error,
                    source="orca-lsp-typecheck",
                    code=RULE_INVALID_ENUM,
                )
            )

    # ------------------------------------------------------------------
    # Unit validation
    # ------------------------------------------------------------------

    def _check_units(
        self,
        result: ParseResult,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Validate units for block parameters that support them.

        Handles single-line blocks (e.g. ``%maxcore 4000KB``) as well as
        multi-line parameter assignments.

        Args:
            result: Parsed result.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        for block in result.percent_blocks:
            valid_units = _VALID_UNITS.get(block.name)
            if valid_units is None:
                continue

            # Check single-line blocks (value on % line)
            self._check_single_line_units(
                block, valid_units, lines, diagnostics,
            )

            # Check multi-line parameter assignments
            block_lines = block.raw_content.split("\n")
            for rel_line_idx, bline in enumerate(block_lines):
                stripped = bline.strip()
                if not stripped or stripped.startswith("%"):
                    continue

                match = _PARAM_ASSIGNMENT_RE.match(stripped)
                if not match:
                    continue

                param_name_raw = match.group(1)
                param_value_raw = match.group(2).strip()
                param_name_lower = param_name_raw.lower()

                allowed_units = valid_units.get(param_name_lower)
                if allowed_units is None:
                    continue

                self._check_unit_value(
                    param_value_raw, param_name_raw, allowed_units,
                    block.line_start + rel_line_idx, lines, diagnostics,
                )

    def _check_single_line_units(
        self,
        block: PercentBlock,
        valid_units: Dict[str, Set[str]],
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check units on single-line value blocks.

        Args:
            block: Parsed block.
            valid_units: Valid unit sets per parameter.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        first_line = block.raw_content.split("\n")[0].strip()
        header_match = re.match(r"%\s*(\w+)(.*)", first_line, re.IGNORECASE)
        if not header_match:
            return

        rest = header_match.group(2).strip()
        if not rest:
            return

        # Remove trailing "end"
        rest_clean = re.sub(r"\bend\s*$", "", rest, flags=re.IGNORECASE).strip()
        if not rest_clean:
            return

        parts = rest_clean.split(None, 1)
        if len(parts) == 1:
            # Single value (e.g. %maxcore 4000KB)
            # Find matching parameter in valid_units
            for param_name, allowed_units in valid_units.items():
                unit_match = _UNIT_SUFFIX_RE.match(parts[0])
                if unit_match:
                    unit_str = unit_match.group(2)
                    if unit_str not in allowed_units:
                        col = self._find_value_col(
                            lines, block.line_start,
                            block.name, parts[0],
                        )
                        diagnostics.append(
                            Diagnostic(
                                range=Range(
                                    start=Position(
                                        line=block.line_start, character=col,
                                    ),
                                    end=Position(
                                        line=block.line_start,
                                        character=col + len(parts[0]),
                                    ),
                                ),
                                message=(
                                    f"Invalid unit '{unit_str}' for "
                                    f"'{param_name}'. "
                                    f"Allowed: {', '.join(sorted(allowed_units))}"
                                ),
                                severity=DiagnosticSeverity.Error,
                                source="orca-lsp-typecheck",
                                code=RULE_INVALID_UNIT,
                            )
                        )
                break  # Only check first matching param for single-line
        elif len(parts) == 2:
            # Inline param (e.g. %pal nprocs 4)
            param_name_lower = parts[0].lower()
            param_value = parts[1].strip()
            allowed_units = valid_units.get(param_name_lower)
            if allowed_units is not None:
                self._check_unit_value(
                    param_value, parts[0], allowed_units,
                    block.line_start, lines, diagnostics,
                )

    def _check_unit_value(
        self,
        value: str,
        param_name: str,
        allowed_units: Set[str],
        line_idx: int,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check a single parameter value for invalid units.

        Args:
            value: Raw value string possibly with unit.
            param_name: Parameter name.
            allowed_units: Set of allowed unit strings.
            line_idx: Line index.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        unit_match = _UNIT_SUFFIX_RE.match(value)
        if unit_match:
            unit_str = unit_match.group(2)
            if unit_str not in allowed_units:
                col = self._find_value_col(
                    lines, line_idx, param_name, value,
                )
                diagnostics.append(
                    Diagnostic(
                        range=Range(
                            start=Position(
                                line=line_idx, character=col,
                            ),
                            end=Position(
                                line=line_idx,
                                character=col + len(value),
                            ),
                        ),
                        message=(
                            f"Invalid unit '{unit_str}' for "
                            f"'{param_name}'. "
                            f"Allowed: {', '.join(sorted(allowed_units))}"
                        ),
                        severity=DiagnosticSeverity.Error,
                        source="orca-lsp-typecheck",
                        code=RULE_INVALID_UNIT,
                    )
                )

    # ------------------------------------------------------------------
    # Required sections validation
    # ------------------------------------------------------------------

    def _check_required_sections(
        self,
        result: ParseResult,
        lines: List[str],
        diagnostics: List[Diagnostic],
    ) -> None:
        """Check for missing required sections.

        Reports missing:
        - Simple input line (!)
        - Method in simple input
        - Basis set in simple input
        - Geometry section

        Args:
            result: Parsed result.
            lines: Document lines.
            diagnostics: Accumulator for diagnostics.
        """
        # Simple input line
        if result.simple_input is None:
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=0, character=0),
                    ),
                    message=(
                        "Missing required simple input line "
                        "(e.g. '! B3LYP def2-TZVP OPT')"
                    ),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-typecheck",
                    code=RULE_MISSING_SECTION,
                )
            )
            return

        si = result.simple_input

        # Method
        if not si.methods:
            line_idx = si.line_number
            col = self._find_bang_col(lines, line_idx)
            line_len = len(lines[line_idx]) if line_idx < len(lines) else 50
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(
                            line=line_idx,
                            character=min(col + 50, line_len),
                        ),
                    ),
                    message=(
                        "No method specified in simple input. "
                        "Expected a DFT functional (e.g. B3LYP) or "
                        "wavefunction method (e.g. HF, MP2)"
                    ),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-typecheck",
                    code=RULE_MISSING_KEYWORD,
                )
            )

        # Basis set
        if not si.basis_sets:
            line_idx = si.line_number
            col = self._find_bang_col(lines, line_idx)
            line_len = len(lines[line_idx]) if line_idx < len(lines) else 50
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col),
                        end=Position(
                            line=line_idx,
                            character=min(col + 50, line_len),
                        ),
                    ),
                    message=(
                        "No basis set specified in simple input. "
                        "Expected a basis set (e.g. def2-TZVP, 6-31G*)"
                    ),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-typecheck",
                    code=RULE_MISSING_KEYWORD,
                )
            )

        # Geometry section
        if result.geometry is None:
            last_line = max(0, len(lines) - 1)
            last_len = len(lines[-1]) if lines else 1
            diagnostics.append(
                Diagnostic(
                    range=Range(
                        start=Position(line=last_line, character=0),
                        end=Position(
                            line=last_line,
                            character=max(1, last_len),
                        ),
                    ),
                    message=(
                        "Missing required geometry section "
                        "(e.g. '* xyz 0 1\\n  H 0 0 0\\n*')"
                    ),
                    severity=DiagnosticSeverity.Warning,
                    source="orca-lsp-typecheck",
                    code=RULE_MISSING_SECTION,
                )
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _strip_unit(
        value: str, block_name: str, param_name: str,
    ) -> str:
        """Strip a recognized unit suffix from a value string.

        Args:
            value: Raw value string possibly with unit.
            block_name: Block name for unit lookup.
            param_name: Parameter name for unit lookup.

        Returns:
            Numeric string with unit stripped.
        """
        units = _VALID_UNITS.get(block_name, {}).get(param_name)
        if units:
            for unit in units:
                if value.upper().endswith(unit.upper()):
                    return value[: -len(unit)].strip()
        return value

    @staticmethod
    def _find_value_col(
        lines: List[str], line_idx: int, param_name: str, value: str,
    ) -> int:
        """Find the column position of a parameter value on a line.

        Args:
            lines: Document lines.
            line_idx: Line index.
            param_name: Parameter name to locate.
            value: Value to locate after the parameter name.

        Returns:
            Column position of the value.
        """
        if line_idx >= len(lines):
            return 0
        line = lines[line_idx]
        name_pos = line.lower().find(param_name.lower())
        if name_pos < 0:
            return 0
        # Find value after the parameter name
        after_name = name_pos + len(param_name)
        val_pos = line.find(value, after_name)
        return val_pos if val_pos >= 0 else after_name

    @staticmethod
    def _token_column(line: str, token: str, occurrence_index: int) -> int:
        """Find the column of the n-th token in a line.

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
    def _find_bang_col(lines: List[str], line_idx: int) -> int:
        """Find the column of the ! in a simple input line.

        Args:
            lines: Document lines.
            line_idx: Zero-based line index.

        Returns:
            Column of the !.
        """
        if line_idx < len(lines):
            col = lines[line_idx].find("!")
            return col if col >= 0 else 0
        return 0


__all__ = ["TypecheckProvider"]
