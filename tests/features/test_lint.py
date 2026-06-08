"""Tests for LintProvider schema-aware static checks."""

import json

import pytest

from orca_lsp.features.lint import (
    LintProvider,
    RULE_CHARGE_MULTIPLICITY,
    RULE_DUPLICATE_BLOCK,
    RULE_DUPLICATE_TOKEN,
    RULE_INVALID_MULTIPLICITY,
    RULE_MAXITER_RANGE,
    RULE_MISSING_MAXCORE,
    RULE_NPROCS_HIGH,
    RULE_UNCLOSED_BLOCK,
    RULE_UNKNOWN_BLOCK,
    RULE_UNKNOWN_TOKEN,
)
from orca_lsp.parser import ORCAParser


@pytest.fixture
def provider() -> LintProvider:
    """Create a LintProvider with a fresh parser."""
    return LintProvider(ORCAParser())


# ---------------------------------------------------------------------------
# Valid inputs produce no lint diagnostics
# ---------------------------------------------------------------------------


class TestValidInputNoLint:
    """Valid ORCA inputs should produce zero lint diagnostics."""

    def test_valid_minimal(self, provider: LintProvider) -> None:
        """Well-formed minimal input has no lint diagnostics."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "  H 0.0 0.0 0.74\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        assert diagnostics == [], (
            f"Expected no lint diagnostics, got: {[d.message for d in diagnostics]}"
        )

    def test_valid_with_dispersion(self, provider: LintProvider) -> None:
        """Valid input with D3BJ modifier produces no lint diagnostics."""
        text = (
            "! B3LYP D3BJ def2-TZVP OPT\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  O 0.0 0.0 0.0\n"
            "  H 0.0 0.0 0.96\n"
            "  H 0.0 0.96 0.0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        assert diagnostics == []

    def test_valid_with_scf_block(self, provider: LintProvider) -> None:
        """Valid input with %scf block produces no lint diagnostics."""
        text = (
            "! HF def2-SVP SP\n"
            "%scf\n"
            "  maxiter 150\n"
            "end\n"
            "%maxcore 2000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "  H 0.0 0.0 0.74\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        assert diagnostics == []

    def test_valid_with_pal_block(self, provider: LintProvider) -> None:
        """Valid input with %pal block produces no lint diagnostics."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%pal nprocs 4 end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "  H 0 0 0.74\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        assert diagnostics == []


# ---------------------------------------------------------------------------
# Unknown tokens (ORCA-E001)
# ---------------------------------------------------------------------------


class TestUnknownToken:
    """Tests for unknown tokens in the simple input line."""

    def test_unknown_token_detected(self, provider: LintProvider) -> None:
        """Unknown token in simple input produces ORCA-E001."""
        text = (
            "! B3LYP NOTAREALTOKEN def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_UNKNOWN_TOKEN in codes, (
            f"Expected {RULE_UNKNOWN_TOKEN}, got codes: {codes}"
        )

    def test_unknown_token_has_error_severity(self, provider: LintProvider) -> None:
        """Unknown token diagnostic has Error severity."""
        text = "! GARBAGE def2-TZVP\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        for d in diagnostics:
            if d.code == RULE_UNKNOWN_TOKEN:
                from lsprotocol.types import DiagnosticSeverity

                assert d.severity == DiagnosticSeverity.Error
                return
        pytest.fail("No ORCA-E001 diagnostic found")

    def test_unknown_token_message_contains_name(self, provider: LintProvider) -> None:
        """Unknown token message includes the token name."""
        text = "! B3LYP FAKETOKEN def2-TZVP\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        for d in diagnostics:
            if d.code == RULE_UNKNOWN_TOKEN:
                assert "FAKETOKEN" in d.message
                return
        pytest.fail("No ORCA-E001 diagnostic found")

    def test_valid_tokens_no_unknown(self, provider: LintProvider) -> None:
        """All known tokens produce no ORCA-E001 diagnostics."""
        text = (
            "! B3LYP RIJCOSX TIGHTSCF def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_UNKNOWN_TOKEN not in codes


# ---------------------------------------------------------------------------
# Unknown % blocks (ORCA-E002)
# ---------------------------------------------------------------------------


class TestUnknownBlock:
    """Tests for unknown % block names."""

    def test_unknown_block_detected(self, provider: LintProvider) -> None:
        """Unknown % block produces ORCA-E002."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "%fakeblock\n"
            "  someparam 1\n"
            "end\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_UNKNOWN_BLOCK in codes, (
            f"Expected {RULE_UNKNOWN_BLOCK}, got codes: {codes}"
        )

    def test_unknown_block_message_contains_name(self, provider: LintProvider) -> None:
        """Unknown block message includes the block name."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "%nonexistent\n"
            "end\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        for d in diagnostics:
            if d.code == RULE_UNKNOWN_BLOCK:
                assert "nonexistent" in d.message
                return
        pytest.fail("No ORCA-E002 diagnostic found")


# ---------------------------------------------------------------------------
# Unclosed blocks (ORCA-E003)
# ---------------------------------------------------------------------------


class TestUnclosedBlock:
    """Tests for unclosed % blocks."""

    def test_unclosed_block_detected(self, provider: LintProvider) -> None:
        """Multi-line % block without 'end' produces ORCA-E003."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "%scf\n"
            "  maxiter 100\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_UNCLOSED_BLOCK in codes, (
            f"Expected {RULE_UNCLOSED_BLOCK}, got codes: {codes}"
        )

    def test_closed_block_not_flagged(self, provider: LintProvider) -> None:
        """Properly closed % block is not flagged."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "%scf\n"
            "  maxiter 100\n"
            "end\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_UNCLOSED_BLOCK not in codes

    def test_single_line_value_not_flagged(self, provider: LintProvider) -> None:
        """Single-line %maxcore is not flagged as unclosed."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_UNCLOSED_BLOCK not in codes


# ---------------------------------------------------------------------------
# Duplicate blocks (ORCA-E004)
# ---------------------------------------------------------------------------


class TestDuplicateBlock:
    """Tests for duplicate % blocks."""

    def test_duplicate_block_detected(self, provider: LintProvider) -> None:
        """Duplicate % block produces ORCA-E004."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "%maxcore 8000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_DUPLICATE_BLOCK in codes, (
            f"Expected {RULE_DUPLICATE_BLOCK}, got codes: {codes}"
        )

    def test_single_block_not_flagged(self, provider: LintProvider) -> None:
        """A single % block is not flagged as duplicate."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_DUPLICATE_BLOCK not in codes


# ---------------------------------------------------------------------------
# Charge / multiplicity (ORCA-E006, ORCA-E007)
# ---------------------------------------------------------------------------


class TestChargeMultiplicity:
    """Tests for charge/multiplicity physics checks."""

    def test_zero_multiplicity(self, provider: LintProvider) -> None:
        """Multiplicity 0 produces ORCA-E006."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 0\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_INVALID_MULTIPLICITY in codes

    def test_inconsistent_multiplicity(self, provider: LintProvider) -> None:
        """Multiplicity 2 with 2 electrons (H2, charge 0) is inconsistent.

        H2 has 2 electrons (even), so multiplicity must be odd (1, 3, ...).
        Multiplicity 2 is even, so it's inconsistent.
        """
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 2\n"
            "  H 0 0 0\n"
            "  H 0 0 0.74\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_CHARGE_MULTIPLICITY in codes, (
            f"Expected {RULE_CHARGE_MULTIPLICITY}, got codes: {codes}"
        )

    def test_consistent_multiplicity_no_diagnostic(self, provider: LintProvider) -> None:
        """Multiplicity 1 with 2 electrons (H2) is consistent."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "  H 0 0 0.74\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_CHARGE_MULTIPLICITY not in codes

    def test_triplet_h2_valid(self, provider: LintProvider) -> None:
        """Multiplicity 3 with 2 electrons is odd, so consistent."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 3\n"
            "  H 0 0 0\n"
            "  H 0 0 0.74\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_CHARGE_MULTIPLICITY not in codes


# ---------------------------------------------------------------------------
# Duplicate tokens (ORCA-W003)
# ---------------------------------------------------------------------------


class TestDuplicateToken:
    """Tests for duplicate tokens in simple input."""

    def test_duplicate_basis_set_detected(self, provider: LintProvider) -> None:
        """Duplicate basis set token produces ORCA-W003."""
        text = (
            "! B3LYP def2-TZVP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_DUPLICATE_TOKEN in codes

    def test_no_duplicate_no_diagnostic(self, provider: LintProvider) -> None:
        """No duplicate tokens produces no ORCA-W003."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_DUPLICATE_TOKEN not in codes


# ---------------------------------------------------------------------------
# Block parameter ranges (ORCA-W004, ORCA-W005, ORCA-W001)
# ---------------------------------------------------------------------------


class TestBlockParameters:
    """Tests for block parameter range checks."""

    def test_maxiter_too_low(self, provider: LintProvider) -> None:
        """SCF maxiter < 10 produces ORCA-W004."""
        text = (
            "! HF def2-SVP SP\n"
            "%scf\n"
            "  maxiter 5\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MAXITER_RANGE in codes

    def test_maxiter_too_high(self, provider: LintProvider) -> None:
        """SCF maxiter > 5000 produces ORCA-W004."""
        text = (
            "! HF def2-SVP SP\n"
            "%scf\n"
            "  maxiter 9999\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MAXITER_RANGE in codes

    def test_maxiter_normal_range(self, provider: LintProvider) -> None:
        """SCF maxiter in range [10, 5000] produces no ORCA-W004."""
        text = (
            "! HF def2-SVP SP\n"
            "%scf\n"
            "  maxiter 150\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MAXITER_RANGE not in codes

    def test_nprocs_high(self, provider: LintProvider) -> None:
        """nprocs > 256 produces ORCA-W005."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%pal nprocs 512 end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_NPROCS_HIGH in codes

    def test_nprocs_normal(self, provider: LintProvider) -> None:
        """nprocs <= 256 produces no ORCA-W005."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%pal nprocs 8 end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_NPROCS_HIGH not in codes

    def test_maxcore_very_low(self, provider: LintProvider) -> None:
        """%maxcore < 100 produces ORCA-W001."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 50\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_MAXCORE in codes

    def test_maxcore_normal(self, provider: LintProvider) -> None:
        """%maxcore >= 100 produces no ORCA-W001."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 2000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_MISSING_MAXCORE not in codes


# ---------------------------------------------------------------------------
# Diagnostic metadata
# ---------------------------------------------------------------------------


class TestDiagnosticMetadata:
    """Tests for diagnostic source, code, and range fields."""

    def test_all_lint_diagnostics_have_source(self, provider: LintProvider) -> None:
        """All lint diagnostics have source='orca-lsp-lint'."""
        text = "! GARBAGE def2-TZVP\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        for d in diagnostics:
            assert d.source == "orca-lsp-lint", (
                f"Expected source 'orca-lsp-lint', got '{d.source}'"
            )

    def test_all_lint_diagnostics_have_code(self, provider: LintProvider) -> None:
        """All lint diagnostics have a non-None code starting with 'ORCA-'."""
        text = "! GARBAGE def2-TZVP\n%fakeblock\nend\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        for d in diagnostics:
            assert d.code is not None, f"Diagnostic missing code: {d.message}"
            assert str(d.code).startswith("ORCA-"), (
                f"Code should start with 'ORCA-', got '{d.code}'"
            )

    def test_all_lint_diagnostics_have_valid_range(self, provider: LintProvider) -> None:
        """All lint diagnostics have a valid range with non-negative lines."""
        text = "! GARBAGE\n%fakeblock\nend\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.lint(text)
        for d in diagnostics:
            assert d.range.start.line >= 0
            assert d.range.end.line >= 0
            assert d.range.start.character >= 0
            assert d.range.end.character >= 0


# ---------------------------------------------------------------------------
# Snapshot API
# ---------------------------------------------------------------------------


class TestSnapshot:
    """Tests for the JSON snapshot method."""

    def test_snapshot_is_valid_json(self, provider: LintProvider) -> None:
        """snapshot() returns valid JSON."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        result = provider.snapshot(text)
        parsed = json.loads(result)
        assert isinstance(parsed, list)

    def test_snapshot_valid_input_empty(self, provider: LintProvider) -> None:
        """snapshot() for valid input returns empty JSON array."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "  H 0 0 0.74\n"
            "*\n"
        )
        result = provider.snapshot(text)
        parsed = json.loads(result)
        assert parsed == []

    def test_snapshot_has_expected_keys(self, provider: LintProvider) -> None:
        """Each snapshot entry has expected keys."""
        text = "! GARBAGE def2-TZVP\n* xyz 0 1\n  H 0 0 0\n*\n"
        result = provider.snapshot(text)
        parsed = json.loads(result)
        assert len(parsed) > 0
        for entry in parsed:
            assert "range" in entry
            assert "severity" in entry
            assert "severity_label" in entry
            assert "source" in entry
            assert "code" in entry
            assert "message" in entry

    def test_snapshot_deterministic(self, provider: LintProvider) -> None:
        """snapshot() is deterministic across calls."""
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        snap1 = provider.snapshot(text)
        snap2 = provider.snapshot(text)
        assert snap1 == snap2

    def test_snapshot_sorted(self, provider: LintProvider) -> None:
        """Snapshot entries are sorted by line, character, severity."""
        text = "! GARBAGE NOTREAL def2-TZVP\n%fakeblock\nend\n* xyz 0 1\n  H 0 0 0\n*\n"
        result = provider.snapshot(text)
        parsed = json.loads(result)
        for i in range(1, len(parsed)):
            prev = parsed[i - 1]
            curr = parsed[i]
            key_prev = (
                prev["range"]["start"]["line"],
                prev["range"]["start"]["character"],
                prev["severity"],
            )
            key_curr = (
                curr["range"]["start"]["line"],
                curr["range"]["start"]["character"],
                curr["severity"],
            )
            assert key_prev <= key_curr


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_empty_input(self, provider: LintProvider) -> None:
        """Empty input produces no lint diagnostics (nothing to lint)."""
        diagnostics = provider.lint("")
        # No simple input, no blocks, no geometry -> nothing to lint.
        assert diagnostics == []

    def test_comment_only(self, provider: LintProvider) -> None:
        """Comment-only input produces no lint diagnostics."""
        text = "# This is a comment\n"
        diagnostics = provider.lint(text)
        assert diagnostics == []

    def test_lint_and_diagnostic_coexist(self, provider: LintProvider) -> None:
        """Lint diagnostics have different source from DiagnosticProvider."""
        from orca_lsp.features.diagnostic import DiagnosticProvider

        diag_provider = DiagnosticProvider(ORCAParser())
        text = "! B3LYP def2-TZVP SP\n%maxcore 4000\n* xyz 0 1\n  H 0 0 0\n*\n"
        diags = diag_provider.get_diagnostics(text)
        lints = provider.lint(text)
        # DiagnosticProvider and LintProvider use different sources.
        for d in diags:
            assert d.source == "orca-lsp"
        for d in lints:
            assert d.source == "orca-lsp-lint"

    def test_valid_wavefunction_method(self, provider: LintProvider) -> None:
        """Valid wavefunction methods are not flagged as unknown."""
        text = (
            "! HF def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        diagnostics = provider.lint(text)
        codes = [d.code for d in diagnostics]
        assert RULE_UNKNOWN_TOKEN not in codes
