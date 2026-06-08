"""Tests for TypecheckProvider value type, enum, unit, and required-section checks."""

import pytest

from lsprotocol.types import DiagnosticSeverity

from orca_lsp.features.typecheck import (
    RULE_INVALID_ENUM,
    RULE_INVALID_TYPE,
    RULE_INVALID_UNIT,
    RULE_MISSING_KEYWORD,
    RULE_MISSING_SECTION,
    RULE_NON_NUMERIC,
    TypecheckProvider,
)
from orca_lsp.parser import ORCAParser


@pytest.fixture
def provider() -> TypecheckProvider:
    """Create a TypecheckProvider with a fresh parser."""
    return TypecheckProvider(ORCAParser())


# ---------------------------------------------------------------------------
# Valid inputs produce no typecheck diagnostics
# ---------------------------------------------------------------------------


class TestValidInputNoTypecheck:
    """Valid ORCA inputs should produce zero typecheck diagnostics."""

    def test_valid_minimal(self, provider: TypecheckProvider) -> None:
        """Well-formed minimal input has no typecheck diagnostics."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "  H 0.0 0.0 0.74\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        assert diagnostics == [], (
            f"Expected no typecheck diagnostics, got: {[d.message for d in diagnostics]}"
        )

    def test_valid_with_dispersion(self, provider: TypecheckProvider) -> None:
        """Valid input with D3BJ modifier produces no typecheck diagnostics."""
        text = (
            "! B3LYP D3BJ def2-TZVP OPT\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "  H 0.0 0.0 0.74\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        assert diagnostics == []

    def test_valid_wavefunction_method(self, provider: TypecheckProvider) -> None:
        """Valid wavefunction method produces no typecheck diagnostics."""
        text = (
            "! HF def2-SVP SP\n"
            "%maxcore 2000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        assert diagnostics == []

    def test_valid_scf_block(self, provider: TypecheckProvider) -> None:
        """Valid %scf block produces no typecheck diagnostics."""
        text = (
            "! HF def2-SVP SP\n"
            "%scf\n"
            "  maxiter 150\n"
            "end\n"
            "%maxcore 2000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        assert diagnostics == []


# ---------------------------------------------------------------------------
# Enum validation (TC-E002) -- simple input misspellings
# ---------------------------------------------------------------------------


class TestEnumValidation:
    """Tests for enum validation in the simple input line."""

    def test_misspelled_method_suggestion(self, provider: TypecheckProvider) -> None:
        """A misspelled method gets a suggestion via TC-E002."""
        text = (
            "! B3LYPz def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_ENUM in codes, (
            f"Expected {RULE_INVALID_ENUM}, got codes: {codes}"
        )
        # Check that B3LYP is suggested
        for d in diagnostics:
            if d.code == RULE_INVALID_ENUM:
                assert "B3LYP" in d.message
                return
        pytest.fail("No TC-E002 diagnostic found")

    def test_misspelled_basis_set(self, provider: TypecheckProvider) -> None:
        """A misspelled basis set gets a suggestion via TC-E002."""
        text = (
            "! B3LYP def2-TZVPPX SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_ENUM in codes

    def test_valid_method_no_diagnostic(self, provider: TypecheckProvider) -> None:
        """Valid methods produce no TC-E002."""
        text = (
            "! PBE0 def2-TZVP OPT\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_ENUM not in codes

    def test_valid_all_modifiers(self, provider: TypecheckProvider) -> None:
        """Known modifiers produce no TC-E002."""
        text = (
            "! B3LYP RIJCOSX TIGHTSCF def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_ENUM not in codes


# ---------------------------------------------------------------------------
# Block value type validation (TC-E001)
# ---------------------------------------------------------------------------


class TestBlockValueTypes:
    """Tests for % block parameter value type validation."""

    def test_non_integer_maxcore(self, provider: TypecheckProvider) -> None:
        """Non-integer value for %maxcore produces TC-E001."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore abc\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE in codes, (
            f"Expected {RULE_INVALID_TYPE}, got codes: {codes}"
        )
        for d in diagnostics:
            if d.code == RULE_INVALID_TYPE:
                assert "integer" in d.message.lower()
                return
        pytest.fail("No TC-E001 diagnostic found")

    def test_valid_integer_maxcore(self, provider: TypecheckProvider) -> None:
        """Valid integer value for %maxcore produces no TC-E001."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE not in codes

    def test_non_numeric_scf_maxiter(self, provider: TypecheckProvider) -> None:
        """Non-numeric value for maxiter produces TC-E001."""
        text = (
            "! HF def2-SVP SP\n"
            "%scf\n"
            "  maxiter abc\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE in codes

    def test_non_bool_output_param(self, provider: TypecheckProvider) -> None:
        """Non-boolean value for %output xyzfile produces TC-E001."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%output\n"
            "  xyzfile notabool\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE in codes

    def test_valid_bool_output_param(self, provider: TypecheckProvider) -> None:
        """Valid boolean values for %output produce no TC-E001."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%output\n"
            "  xyzfile true\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE not in codes

    def test_invalid_enum_scf_convergence(self, provider: TypecheckProvider) -> None:
        """Invalid value for %scf convergence produces TC-E002."""
        text = (
            "! HF def2-SVP SP\n"
            "%scf\n"
            "  convergence superstrict\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_ENUM in codes

    def test_valid_enum_scf_convergence(self, provider: TypecheckProvider) -> None:
        """Valid value for %scf convergence produces no TC-E002."""
        text = (
            "! HF def2-SVP SP\n"
            "%scf\n"
            "  convergence tight\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_ENUM not in codes

    def test_non_numeric_cpcm_epsilon(self, provider: TypecheckProvider) -> None:
        """Non-numeric value for %cpcm epsilon produces TC-E001."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%cpcm\n"
            "  epsilon water\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE in codes

    def test_valid_float_cpcm_epsilon(self, provider: TypecheckProvider) -> None:
        """Valid float value for %cpcm epsilon produces no TC-E001."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%cpcm\n"
            "  epsilon 80.4\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE not in codes


# ---------------------------------------------------------------------------
# Range validation (TC-W003)
# ---------------------------------------------------------------------------


class TestRangeValidation:
    """Tests for value range validation in % block parameters."""

    def test_maxcore_below_minimum(self, provider: TypecheckProvider) -> None:
        """%maxcore below minimum produces TC-W003."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 50\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_NON_NUMERIC in codes

    def test_maxcore_above_maximum(self, provider: TypecheckProvider) -> None:
        """%maxcore above maximum produces TC-W003."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 100000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_NON_NUMERIC in codes

    def test_maxcore_in_range(self, provider: TypecheckProvider) -> None:
        """%maxcore in range produces no TC-W003."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_NON_NUMERIC not in codes

    def test_nprocs_below_minimum(self, provider: TypecheckProvider) -> None:
        """nprocs below minimum produces TC-W003."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%pal nprocs 0 end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_NON_NUMERIC in codes

    def test_float_below_minimum(self, provider: TypecheckProvider) -> None:
        """Float value below minimum produces TC-W003."""
        text = (
            "! B3LYP def2-TZVP FREQ\n"
            "%freq\n"
            "  temp -10.0\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_NON_NUMERIC in codes


# ---------------------------------------------------------------------------
# Unit validation (TC-E003)
# ---------------------------------------------------------------------------


class TestUnitValidation:
    """Tests for unit validation in % block parameters."""

    def test_invalid_unit_maxcore(self, provider: TypecheckProvider) -> None:
        """Invalid unit for %maxcore produces TC-E003."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000KB\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_UNIT in codes, (
            f"Expected {RULE_INVALID_UNIT}, got codes: {codes}"
        )

    def test_valid_unit_maxcore_mb(self, provider: TypecheckProvider) -> None:
        """Valid unit 'MB' for %maxcore produces no TC-E003."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000MB\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_UNIT not in codes

    def test_valid_unit_maxcore_gb(self, provider: TypecheckProvider) -> None:
        """Valid unit 'GB' for %maxcore produces no TC-E003."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4GB\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_UNIT not in codes

    def test_invalid_unit_temp(self, provider: TypecheckProvider) -> None:
        """Invalid unit for temperature produces TC-E003."""
        text = (
            "! B3LYP def2-TZVP FREQ\n"
            "%freq\n"
            "  temp 298.15F\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_UNIT in codes

    def test_valid_unit_temp_kelvin(self, provider: TypecheckProvider) -> None:
        """Valid unit 'K' for temperature produces no TC-E003."""
        text = (
            "! B3LYP def2-TZVP FREQ\n"
            "%freq\n"
            "  temp 298.15K\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_UNIT not in codes

    def test_no_unit_still_valid(self, provider: TypecheckProvider) -> None:
        """A value without a unit suffix is still valid (unit is optional)."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_UNIT not in codes


# ---------------------------------------------------------------------------
# Required sections validation (TC-W001, TC-W002)
# ---------------------------------------------------------------------------


class TestRequiredSections:
    """Tests for missing required sections."""

    def test_missing_simple_input(self, provider: TypecheckProvider) -> None:
        """Missing simple input line produces TC-W001."""
        text = "%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_SECTION in codes

    def test_missing_method(self, provider: TypecheckProvider) -> None:
        """Missing method in simple input produces TC-W002."""
        text = "! def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_KEYWORD in codes

    def test_missing_basis_set(self, provider: TypecheckProvider) -> None:
        """Missing basis set in simple input produces TC-W002."""
        text = "! B3LYP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_KEYWORD in codes

    def test_missing_geometry(self, provider: TypecheckProvider) -> None:
        """Missing geometry section produces TC-W001."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_SECTION in codes

    def test_complete_input_no_missing(self, provider: TypecheckProvider) -> None:
        """Complete input produces no TC-W001 or TC-W002 diagnostics."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "  H 0 0 0.74\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_SECTION not in codes
        assert RULE_MISSING_KEYWORD not in codes


# ---------------------------------------------------------------------------
# Diagnostic metadata
# ---------------------------------------------------------------------------


class TestDiagnosticMetadata:
    """Tests for diagnostic source, code, and range fields."""

    def test_all_typecheck_diagnostics_have_source(
        self, provider: TypecheckProvider,
    ) -> None:
        """All typecheck diagnostics have source='orca-lsp-typecheck'."""
        text = (
            "! B3LYPz def2-TZVP SP\n"
            "%maxcore abc\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        for d in diagnostics:
            assert d.source == "orca-lsp-typecheck", (
                f"Expected source 'orca-lsp-typecheck', got '{d.source}'"
            )

    def test_all_typecheck_diagnostics_have_code(
        self, provider: TypecheckProvider,
    ) -> None:
        """All typecheck diagnostics have a non-None code starting with 'TC-'."""
        text = (
            "! B3LYPz def2-TZVP SP\n"
            "%maxcore abc\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        for d in diagnostics:
            assert d.code is not None, f"Diagnostic missing code: {d.message}"
            assert str(d.code).startswith("TC-"), (
                f"Code should start with 'TC-', got '{d.code}'"
            )

    def test_all_typecheck_diagnostics_have_valid_range(
        self, provider: TypecheckProvider,
    ) -> None:
        """All typecheck diagnostics have a valid range with non-negative lines."""
        text = "! B3LYPz\n%maxcore abc\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.typecheck(text)
        for d in diagnostics:
            assert d.range.start.line >= 0
            assert d.range.end.line >= 0
            assert d.range.start.character >= 0
            assert d.range.end.character >= 0


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_input(self, provider: TypecheckProvider) -> None:
        """Empty input produces missing-section diagnostics."""
        diagnostics = provider.typecheck("")
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_SECTION in codes

    def test_comment_only(self, provider: TypecheckProvider) -> None:
        """Comment-only input produces missing-section diagnostics."""
        text = "# This is a comment\n"
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_SECTION in codes

    def test_typecheck_and_lint_have_different_source(
        self, provider: TypecheckProvider,
    ) -> None:
        """Typecheck diagnostics have different source from LintProvider."""
        from orca_lsp.features.lint import LintProvider

        lint_provider = LintProvider(ORCAParser())
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        lints = lint_provider.lint(text)
        typechecks = provider.typecheck(text)
        for d in lints:
            assert d.source == "orca-lsp-lint"
        for d in typechecks:
            assert d.source == "orca-lsp-typecheck"

    def test_bool_zero_is_valid(self, provider: TypecheckProvider) -> None:
        """Boolean '0' is a valid value."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%output\n"
            "  xyzfile 0\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE not in codes

    def test_bool_yes_is_valid(self, provider: TypecheckProvider) -> None:
        """Boolean 'yes' is a valid value."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%output\n"
            "  xyzfile yes\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE not in codes

    def test_geom_maxiter_valid(self, provider: TypecheckProvider) -> None:
        """Valid %geom maxiter produces no diagnostics."""
        text = (
            "! B3LYP def2-TZVP OPT\n"
            "%geom\n"
            "  maxiter 100\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "  H 0 0 0.74\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE not in codes
        assert RULE_NON_NUMERIC not in codes

    def test_geom_maxiter_non_numeric(self, provider: TypecheckProvider) -> None:
        """Non-numeric %geom maxiter produces TC-E001."""
        text = (
            "! B3LYP def2-TZVP OPT\n"
            "%geom\n"
            "  maxiter lots\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE in codes

    def test_unknown_block_no_typecheck_error(
        self, provider: TypecheckProvider,
    ) -> None:
        """An unknown % block does not produce typecheck errors (lint handles it)."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%fakeblock\n"
            "  someparam 1\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE not in codes

    def test_method_dispersion_valid(self, provider: TypecheckProvider) -> None:
        """Valid dispersion values in %method produce no diagnostics."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%method\n"
            "  dispersion D3BJ\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_ENUM not in codes

    def test_method_dispersion_invalid(self, provider: TypecheckProvider) -> None:
        """Invalid dispersion value in %method produces TC-E002."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%method\n"
            "  dispersion D99\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_ENUM in codes

    def test_eprnmr_gtensor_valid(self, provider: TypecheckProvider) -> None:
        """Valid gtensor value produces no diagnostics."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%eprnmr\n"
            "  gtensor 1\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_TYPE not in codes
        assert RULE_NON_NUMERIC not in codes

    def test_md_timestep_valid_unit(self, provider: TypecheckProvider) -> None:
        """Valid MD timestep with unit produces no diagnostics."""
        text = (
            "! B3LYP def2-TZVP MD\n"
            "%md\n"
            "  timestep 0.5fs\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_UNIT not in codes

    def test_md_timestep_invalid_unit(self, provider: TypecheckProvider) -> None:
        """Invalid MD timestep unit produces TC-E003."""
        text = (
            "! B3LYP def2-TZVP MD\n"
            "%md\n"
            "  timestep 0.5ns\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.typecheck(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_UNIT in codes


# ---------------------------------------------------------------------------
# Levenshtein helper tests
# ---------------------------------------------------------------------------


class TestLevenshtein:
    """Tests for the Levenshtein distance helper."""

    def test_identical_strings(self, provider: TypecheckProvider) -> None:
        """Identical strings have distance 0."""
        assert TypecheckProvider._levenshtein("B3LYP", "B3LYP") == 0

    def test_one_edit(self, provider: TypecheckProvider) -> None:
        """One character difference has distance 1."""
        assert TypecheckProvider._levenshtein("B3LYP", "B3LYQ") == 1

    def test_empty_string(self, provider: TypecheckProvider) -> None:
        """Empty string distance equals length of other."""
        assert TypecheckProvider._levenshtein("", "ABC") == 3
