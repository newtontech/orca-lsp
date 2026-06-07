"""ORCA input validation - separated from parsing for single-responsibility."""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, List

from .keywords import DFT_FUNCTIONALS

if TYPE_CHECKING:
    from .parser import ParseResult, SimpleInput


class ORCAValidator:
    """Validates parsed ORCA input and populates errors/warnings on ParseResult.

    Extracted from ORCAParser to separate pure parsing from validation (SRP).
    """

    def __init__(self) -> None:
        # Pre-compute uppercase lookup dicts for O(1) validation lookups
        self._dft_functionals_by_upper: Dict[str, str] = {
            name.upper(): name for name in DFT_FUNCTIONALS
        }

    def validate(self, result: "ParseResult") -> None:
        """Run all diagnostics and populate errors/warnings on *result*."""
        self._check_simple_input(result)
        self._check_geometry(result)
        self._check_maxcore_recommendation(result)
        self._check_scf_conflicts(result)
        self._check_method_combinations(result)
        self._check_spin_charge(result)
        self._check_basis_compatibility(result)

    # ------------------------------------------------------------------
    # Individual validation checks
    # ------------------------------------------------------------------

    def _check_simple_input(self, result: ParseResult) -> None:
        """Validate presence and content of the simple input line."""
        if result.simple_input is None:
            result.errors.append(
                {
                    "message": "Missing simple input line (!) with method and basis set",
                    "line": 0,
                    "severity": "error",
                }
            )
            return

        if not result.simple_input.methods:
            result.errors.append(
                {
                    "message": "No method specified in simple input (e.g., B3LYP, HF, MP2)",
                    "line": result.simple_input.line_number,
                    "severity": "error",
                }
            )

        if not result.simple_input.basis_sets:
            result.errors.append(
                {
                    "message": "No basis set specified in simple input (e.g., def2-TZVP, 6-31G*)",
                    "line": result.simple_input.line_number,
                    "severity": "error",
                }
            )

    def _check_geometry(self, result: ParseResult) -> None:
        """Validate geometry section and atom elements."""
        if result.geometry is None:
            result.errors.append(
                {
                    "message": "Missing geometry section (* xyz charge multiplicity ...)",
                    "line": 0,
                    "severity": "error",
                }
            )
            return

        for atom in result.geometry.atoms:
            if not atom.is_valid():
                result.errors.append(
                    {
                        "message": f"Invalid element symbol: {atom.element}",
                        "line": atom.line_number,
                        "severity": "error",
                    }
                )

    def _check_maxcore_recommendation(self, result: ParseResult) -> None:
        """Warn if %maxcore is not set."""
        has_maxcore = any(b.name == "maxcore" for b in result.percent_blocks)
        if not has_maxcore:
            result.warnings.append(
                {
                    "message": "Missing %maxcore setting. Recommended: %maxcore 2000-4000 (MB per core)",
                    "line": 0,
                    "severity": "warning",
                }
            )

    def _check_scf_conflicts(self, result: ParseResult) -> None:
        """Check for mutually exclusive SCF types."""
        if not result.simple_input:
            return

        keywords = self._simple_input_keywords(result.simple_input)

        scf_types = {"RHF", "UHF", "ROHF"}
        found_scf = [keyword for keyword in keywords if keyword in scf_types]
        if len(found_scf) > 1:
            result.errors.append(
                {
                    "message": f"Mutually exclusive SCF types: {' '.join(found_scf)}",
                    "line": result.simple_input.line_number,
                    "severity": "error",
                }
            )

    def _check_method_combinations(self, result: ParseResult) -> None:
        """Check for invalid method combinations."""
        if not result.simple_input:
            return

        keywords = self._simple_input_keywords(result.simple_input)
        methods = {method.upper() for method in result.simple_input.methods}

        self._check_mutually_exclusive_groups(result, keywords)

        has_dft = any(
            m in {"B3LYP", "PBE0", "PBE", "M06", "TPSS", "HF", "RHF", "UHF"} for m in methods
        )
        has_mp2 = "MP2" in methods or "RI-MP2" in methods

        if has_dft and has_mp2:
            result.warnings.append(
                {
                    "message": "DFT combined with MP2 is not standard. Consider double-hybrid functionals (e.g., B2PLYP) for such combinations.",
                    "line": result.simple_input.line_number,
                    "severity": "warning",
                }
            )

    def _check_mutually_exclusive_groups(
        self, result: ParseResult, keywords: List[str]
    ) -> None:
        """Check simple-line keyword groups where ORCA accepts only one choice."""
        if not result.simple_input:
            return

        keyword_set = set(keywords)
        functional_keywords = {
            keyword.upper()
            for keyword in result.simple_input.methods
            if keyword.upper() in self._dft_functionals_by_upper
        }
        basis_keywords = {basis.upper() for basis in result.simple_input.basis_sets}

        exclusive_groups = [
            ("dispersion corrections", {"D3", "D3BJ", "D4"}),
            ("RI approximations", {"RIJCOSX", "RI-J"}),
            ("DFT functionals", functional_keywords),
            ("correlation methods", {"MP2", "RI-MP2", "SCS-MP2", "CCSD", "CCSD(T)"}),
            ("basis sets", basis_keywords),
            ("SCF convergence settings", {"TIGHTSCF", "LOOSESCF"}),
            ("relativistic corrections", {"ZORA", "DKH"}),
            ("solvent models", {"CPCM", "SMD"}),
        ]

        for label, group in exclusive_groups:
            found = sorted(keyword_set & group)
            if len(found) > 1:
                result.errors.append(
                    {
                        "message": f"Mutually exclusive {label}: {' '.join(found)}",
                        "line": result.simple_input.line_number,
                        "severity": "error",
                    }
                )

    def _check_spin_charge(self, result: ParseResult) -> None:
        """Check spin/charge consistency in geometry."""
        if not result.geometry:
            return

        multiplicity = result.geometry.multiplicity
        charge = result.geometry.charge

        if multiplicity < 1:
            result.errors.append(
                {
                    "message": "Multiplicity must be >= 1",
                    "line": result.geometry.line_start,
                    "severity": "error",
                }
            )

        if charge < 0:
            result.errors.append(
                {
                    "message": "Charge cannot be negative",
                    "line": result.geometry.line_start,
                    "severity": "error",
                }
            )

    def _check_basis_compatibility(self, result: ParseResult) -> None:
        """Check basis set compatibility."""
        if not result.simple_input:
            return

        basis_sets = result.simple_input.basis_sets

        def2_bases = [b for b in basis_sets if b.upper().startswith("DEF2")]
        def2_with_diffuse = [b for b in def2_bases if "D" in b.upper()[-2:]]

        if def2_bases and not def2_with_diffuse:
            for atom in result.geometry.atoms if result.geometry else []:
                if atom.element in ["F", "CL", "BR", "I"]:
                    result.warnings.append(
                        {
                            "message": f"Heavy halogen {atom.element} detected with def2 basis without diffuse functions. Consider {atom.element}-relevant basis set.",
                            "line": atom.line_number,
                            "severity": "warning",
                        }
                    )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _simple_input_keywords(simple_input: SimpleInput) -> List[str]:
        """Return all simple-line keywords normalized to uppercase."""
        tokens = (
            simple_input.methods
            + simple_input.basis_sets
            + simple_input.job_types
            + simple_input.other_keywords
        )
        return [token.upper() for token in tokens]
