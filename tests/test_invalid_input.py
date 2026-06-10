"""Tests for common invalid ORCA input cases.

Covers error detection, validation, and diagnostics for malformed or
semantically incorrect input files.
"""

import pytest

from lsprotocol.types import DiagnosticSeverity

from orca_lsp.parser import ORCAParser
from orca_lsp.features.diagnostic import DiagnosticProvider
from orca_lsp.features.lint import LintProvider
from orca_lsp.features.typecheck import TypecheckProvider
from orca_lsp.features.code_actions import CodeActionProvider


@pytest.fixture
def parser():
    return ORCAParser()


@pytest.fixture
def diag():
    return DiagnosticProvider()


@pytest.fixture
def lint():
    return LintProvider()


@pytest.fixture
def typecheck():
    return TypecheckProvider()


@pytest.fixture
def code_actions():
    return CodeActionProvider()


# ---------------------------------------------------------------------------
# Missing sections
# ---------------------------------------------------------------------------

class TestMissingSections:
    """Missing required sections produce errors."""

    def test_missing_simple_input(self, diag):
        """Empty file produces error for missing simple input."""
        diags = diag.get_diagnostics("")
        msgs = [d.message for d in diags]
        assert any("simple input" in m.lower() for m in msgs)

    def test_missing_geometry(self, diag):
        """File without geometry section produces error."""
        content = "! B3LYP def2-SVP"
        diags = diag.get_diagnostics(content)
        msgs = [d.message for d in diags]
        assert any("geometry" in m.lower() for m in msgs)

    def test_missing_method(self, diag):
        """Simple input with no method produces error."""
        content = "! def2-SVP OPT\n* xyz 0 1\nH 0 0 0\n*"
        diags = diag.get_diagnostics(content)
        msgs = [d.message for d in diags]
        assert any("method" in m.lower() or "No method" in m for m in msgs)

    def test_missing_basis_set(self, diag):
        """Simple input with no basis set produces error."""
        content = "! B3LYP OPT\n* xyz 0 1\nH 0 0 0\n*"
        diags = diag.get_diagnostics(content)
        msgs = [d.message for d in diags]
        assert any("basis" in m.lower() for m in msgs)


# ---------------------------------------------------------------------------
# Invalid elements
# ---------------------------------------------------------------------------

class TestInvalidElements:
    """Invalid element symbols in geometry produce errors."""

    def test_invalid_element_xx(self, parser, diag):
        """Element 'Xx' is invalid."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nXx 0 0 0\n*"
        result = parser.parse(content)
        assert any("Invalid element" in e["message"] for e in result.errors)

    def test_invalid_element_abc(self, parser, diag):
        """Element 'Abc' is invalid."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nAbc 0 0 0\n*"
        result = parser.parse(content)
        assert any("Invalid element" in e["message"] for e in result.errors)


# ---------------------------------------------------------------------------
# Charge/multiplicity errors
# ---------------------------------------------------------------------------

class TestChargeMultiplicity:
    """Invalid charge or multiplicity produce errors."""

    def test_multiplicity_zero(self, parser):
        """Multiplicity 0 produces error."""
        content = "! B3LYP def2-SVP\n* xyz 0 0\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any("Multiplicity" in e["message"] for e in result.errors)

    def test_negative_charge_rejected(self, parser):
        """Negative charge produces error."""
        content = "! B3LYP def2-SVP\n* xyz -1 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any("negative" in e["message"].lower() or "Charge" in e["message"] for e in result.errors)

    def test_multiplicity_electron_mismatch(self, lint):
        """Multiplicity inconsistent with electron count.

        H2 has 2 electrons (even). Multiplicity 2 is even.
        Rule: even electrons -> mult must be odd. mult=2 is even -> inconsistent.
        """
        content = "! B3LYP def2-SVP\n%maxcore 4000\n* xyz 0 2\nH 0 0 0\nH 0 0 1\n*"
        diags = lint.lint(content)
        msgs = [d.message for d in diags]
        assert any("inconsistent" in m.lower() or "Multiplicity" in m for m in msgs)


# ---------------------------------------------------------------------------
# Mutually exclusive keywords
# ---------------------------------------------------------------------------

class TestMutuallyExclusiveKeywords:
    """Mutually exclusive keywords in simple input produce errors."""

    def test_multiple_scf_types(self, parser):
        """RHF + UHF together are mutually exclusive."""
        content = "! RHF UHF def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any("Mutually exclusive SCF" in e["message"] for e in result.errors)

    def test_multiple_dispersion_corrections(self, parser):
        """D3 + D3BJ together are mutually exclusive."""
        content = "! B3LYP D3 D3BJ def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any("Mutually exclusive" in e["message"] for e in result.errors)


# ---------------------------------------------------------------------------
# Unknown tokens and blocks
# ---------------------------------------------------------------------------

class TestUnknownTokensAndBlocks:
    """Unknown tokens and blocks produce lint diagnostics."""

    def test_unknown_token_in_simple_input(self, lint):
        """Unknown token in simple input is flagged."""
        content = "! B3LYP TotallyMadeUpKeyword123 def2-SVP\n%maxcore 4000\n* xyz 0 1\nH 0 0 0\n*"
        diags = lint.lint(content)
        msgs = [d.message for d in diags]
        assert any("Unknown token" in m for m in msgs)

    def test_unknown_percent_block(self, lint):
        """Unknown % block name is flagged."""
        content = "! B3LYP def2-SVP\n%totallyfake\n  param 1\nend\n%maxcore 4000\n* xyz 0 1\nH 0 0 0\n*"
        diags = lint.lint(content)
        msgs = [d.message for d in diags]
        assert any("Unknown % block" in m for m in msgs)

    def test_unclosed_percent_block(self, lint):
        """Unclosed % block is flagged."""
        content = "! B3LYP def2-SVP\n%scf\n  maxiter 100\n%maxcore 4000\n* xyz 0 1\nH 0 0 0\n*"
        diags = lint.lint(content)
        msgs = [d.message for d in diags]
        assert any("Unclosed" in m for m in msgs)


# ---------------------------------------------------------------------------
# Type validation errors
# ---------------------------------------------------------------------------

class TestTypeValidationErrors:
    """Invalid parameter types produce typecheck diagnostics."""

    def test_maxcore_non_numeric(self, typecheck):
        """Non-numeric maxcore value produces type error."""
        content = "! B3LYP def2-SVP\n%maxcore abc\n* xyz 0 1\nH 0 0 0\n*"
        diags = typecheck.typecheck(content)
        msgs = [d.message for d in diags]
        assert any("integer" in m.lower() or "Expected" in m for m in msgs)

    def test_scf_maxiter_out_of_range(self, lint):
        """SCF maxiter 5 is below typical range."""
        content = "! B3LYP def2-SVP\n%scf\n  maxiter 5\nend\n%maxcore 4000\n* xyz 0 1\nH 0 0 0\n*"
        diags = lint.lint(content)
        msgs = [d.message for d in diags]
        assert any("maxiter" in m.lower() for m in msgs)

    def test_pal_nprocs_unusually_high(self, lint):
        """nprocs=999 produces warning."""
        content = "! B3LYP def2-SVP\n%pal nprocs 999 end\n%maxcore 4000\n* xyz 0 1\nH 0 0 0\n*"
        diags = lint.lint(content)
        msgs = [d.message for d in diags]
        assert any("nprocs" in m.lower() or "unusually" in m.lower() for m in msgs)


# ---------------------------------------------------------------------------
# Missing %maxcore warning
# ---------------------------------------------------------------------------

class TestMissingMaxcoreWarning:
    """Missing %maxcore produces a warning."""

    def test_missing_maxcore_warning_from_parser(self, parser):
        """Parser produces warning for missing %maxcore."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any("maxcore" in w["message"].lower() for w in result.warnings)

    def test_missing_maxcore_warning_from_diag(self, diag):
        """DiagnosticProvider produces warning for missing %maxcore."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        diags = diag.get_diagnostics(content)
        warnings = [d for d in diags if d.severity == DiagnosticSeverity.Warning]
        msgs = [d.message for d in warnings]
        assert any("maxcore" in m.lower() for m in msgs)


# ---------------------------------------------------------------------------
# Duplicate blocks
# ---------------------------------------------------------------------------

class TestDuplicateBlocks:
    """Duplicate % blocks produce lint errors."""

    def test_duplicate_maxcore(self, lint):
        """Two %maxcore blocks produce duplicate error."""
        content = "! B3LYP def2-SVP\n%maxcore 4000\n%maxcore 8000\n* xyz 0 1\nH 0 0 0\n*"
        diags = lint.lint(content)
        msgs = [d.message for d in diags]
        assert any("Duplicate" in m for m in msgs)
