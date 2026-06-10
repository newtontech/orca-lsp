"""Tests verifying that all bundled example .inp files parse and validate correctly.

These tests guarantee parse/diagnostic stability: every example file in the
``examples/`` directory must parse without crashing and produce the expected
class of diagnostics (no internal errors, expected warnings about missing
sections are fine for incomplete examples).
"""

import os
from pathlib import Path

import pytest

from orca_lsp.parser import ORCAParser
from orca_lsp.features.diagnostic import DiagnosticProvider
from orca_lsp.features.lint import LintProvider
from orca_lsp.features.typecheck import TypecheckProvider
from orca_lsp.features.formatting import FormattingProvider

# Resolve the examples directory relative to this test file.
EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

# Collect all .inp files.
EXAMPLE_FILES = sorted(EXAMPLES_DIR.glob("*.inp"))


@pytest.fixture
def parser():
    return ORCAParser()


@pytest.fixture
def diagnostic_provider(parser):
    return DiagnosticProvider(parser)


@pytest.fixture
def lint_provider(parser):
    return LintProvider(parser)


@pytest.fixture
def typecheck_provider(parser):
    return TypecheckProvider(parser)


@pytest.fixture
def formatting_provider():
    return FormattingProvider()


# ---------------------------------------------------------------------------
# Parametrized fixtures
# ---------------------------------------------------------------------------

def _read_example(path: Path) -> str:
    """Read an example file, skipping if missing."""
    assert path.exists(), f"Example file not found: {path}"
    return path.read_text(encoding="utf-8")


def example_ids():
    return [p.stem for p in EXAMPLE_FILES]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestExampleParseStability:
    """Every example .inp file parses without error."""

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_parse_does_not_raise(self, parser, path):
        """Parsing never raises an exception."""
        content = _read_example(path)
        result = parser.parse(content)
        assert result is not None

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_parse_produces_result_with_expected_sections(self, parser, path):
        """Every example has a simple input line and a geometry section."""
        content = _read_example(path)
        result = parser.parse(content)
        assert result.simple_input is not None, f"{path.name}: missing simple input"
        assert result.geometry is not None, f"{path.name}: missing geometry"

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_parse_at_least_one_method(self, parser, path):
        """Every example has at least one method in the simple input."""
        content = _read_example(path)
        result = parser.parse(content)
        assert len(result.simple_input.methods) > 0, (
            f"{path.name}: expected at least one method"
        )

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_parse_at_least_one_basis_set(self, parser, path):
        """Every example has at least one basis set."""
        content = _read_example(path)
        result = parser.parse(content)
        assert len(result.simple_input.basis_sets) > 0, (
            f"{path.name}: expected at least one basis set"
        )

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_parse_geometry_has_atoms(self, parser, path):
        """Every example geometry has at least one atom."""
        content = _read_example(path)
        result = parser.parse(content)
        assert len(result.geometry.atoms) > 0, (
            f"{path.name}: expected at least one atom"
        )

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_all_atoms_valid(self, parser, path):
        """All atoms in every example have valid element symbols."""
        content = _read_example(path)
        result = parser.parse(content)
        for atom in result.geometry.atoms:
            assert atom.is_valid(), f"{path.name}: invalid element '{atom.element}'"


class TestExampleDiagnosticStability:
    """Diagnostics on example files are stable and deterministic."""

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_diagnostic_provider_no_crash(self, diagnostic_provider, path):
        """DiagnosticProvider handles every example without raising."""
        content = _read_example(path)
        diags = diagnostic_provider.get_diagnostics(content)
        assert isinstance(diags, list)

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_lint_provider_no_crash(self, lint_provider, path):
        """LintProvider handles every example without raising."""
        content = _read_example(path)
        diags = lint_provider.lint(content)
        assert isinstance(diags, list)

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_typecheck_provider_no_crash(self, typecheck_provider, path):
        """TypecheckProvider handles every example without raising."""
        content = _read_example(path)
        diags = typecheck_provider.typecheck(content)
        assert isinstance(diags, list)

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_no_internal_parser_errors(self, diagnostic_provider, path):
        """No example produces a 'Parser error' diagnostic."""
        content = _read_example(path)
        diags = diagnostic_provider.get_diagnostics(content)
        for d in diags:
            assert "Parser error" not in d.message, (
                f"{path.name}: internal parser error: {d.message}"
            )


class TestExampleFormattingStability:
    """Formatting on example files is stable."""

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_formatting_does_not_crash(self, formatting_provider, path):
        """Formatting every example file does not raise."""
        content = _read_example(path)
        from unittest.mock import MagicMock
        params = MagicMock()
        params.options = MagicMock()
        params.options.tab_size = 2
        params.options.insert_spaces = True
        result = formatting_provider.format_document(content, params)
        assert isinstance(result, list)

    @pytest.mark.parametrize("path", EXAMPLE_FILES, ids=example_ids())
    def test_formatting_idempotent(self, formatting_provider, path):
        """Formatting is idempotent: format(format(x)) == format(x)."""
        content = _read_example(path)
        from unittest.mock import MagicMock
        params = MagicMock()
        params.options = MagicMock()
        params.options.tab_size = 2
        params.options.insert_spaces = True

        edits1 = formatting_provider.format_document(content, params)
        if not edits1:
            pytest.skip("Already formatted")
        formatted1 = edits1[0].new_text

        edits2 = formatting_provider.format_document(formatted1, params)
        if not edits2:
            # Idempotent: second format produces no changes
            return
        formatted2 = edits2[0].new_text
        assert formatted1 == formatted2, (
            f"{path.name}: formatting is not idempotent"
        )


class TestExampleSpecificAssertions:
    """Per-file assertions verifying content-specific details."""

    def test_water_molecule(self, parser):
        """water.inp has 3 atoms and OPT+FREQ job types."""
        content = _read_example(EXAMPLES_DIR / "water.inp")
        result = parser.parse(content)
        assert len(result.geometry.atoms) == 3
        assert any(
            jt.upper() == "OPT" for jt in result.simple_input.job_types
        )

    def test_benzene_molecule(self, parser):
        """benzene.inp has 12 atoms (6 C + 6 H) and DLPNO-CCSD(T)."""
        content = _read_example(EXAMPLES_DIR / "benzene.inp")
        result = parser.parse(content)
        assert len(result.geometry.atoms) == 12
        assert any("DLPNO" in m.upper() for m in result.simple_input.methods)

    def test_ethylene_molecule(self, parser):
        """ethylene.inp has 6 atoms."""
        content = _read_example(EXAMPLES_DIR / "ethylene.inp")
        result = parser.parse(content)
        assert len(result.geometry.atoms) == 6

    def test_solvation_has_cpcm(self, parser):
        """solvation.inp uses CPCM solvent model."""
        content = _read_example(EXAMPLES_DIR / "solvation.inp")
        # Check there's a cpcm block
        result = parser.parse(content)
        cpcm_blocks = [b for b in result.percent_blocks if b.name == "cpcm"]
        assert len(cpcm_blocks) > 0

    def test_td_dft_has_tddft_block(self, parser):
        """td_dft.inp has a %tddft block."""
        content = _read_example(EXAMPLES_DIR / "td_dft.inp")
        result = parser.parse(content)
        tddft_blocks = [b for b in result.percent_blocks if b.name == "tddft"]
        assert len(tddft_blocks) > 0

    def test_counterpoise_has_cp_block(self, parser):
        """counterpoise.inp has a %cp block."""
        content = _read_example(EXAMPLES_DIR / "counterpoise.inp")
        result = parser.parse(content)
        cp_blocks = [b for b in result.percent_blocks if b.name == "cp"]
        assert len(cp_blocks) > 0

    def test_transition_state_has_ts(self, parser):
        """transition_state.inp uses TS job type."""
        content = _read_example(EXAMPLES_DIR / "transition_state.inp")
        result = parser.parse(content)
        assert "TS" in result.simple_input.job_types

    def test_camb3lyp_functional(self, parser):
        """camb3lyp.inp uses CAM-B3LYP functional."""
        content = _read_example(EXAMPLES_DIR / "camb3lyp.inp")
        result = parser.parse(content)
        assert any("CAM-B3LYP" in m.upper() for m in result.simple_input.methods)
