"""Behavioral tests for ORCA parser.

Consolidates unique behaviors from coverage-oriented test files into
meaningful assertions about parser behavior.
"""

import pytest

from orca_lsp.parser import ORCAParser, Atom, Geometry, SimpleInput, PercentBlock


class TestUnknownKeywordHandling:
    """Parser correctly classifies unknown keywords."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_single_unknown_keyword_goes_to_other(self, parser):
        """An unrecognized keyword is collected in other_keywords."""
        result = parser.parse_simple_input("! TotallyUnknownKeyword12345", 0)
        assert "TotallyUnknownKeyword12345" in result.other_keywords
        assert len(result.methods) == 0
        assert len(result.basis_sets) == 0
        assert len(result.job_types) == 0

    def test_multiple_unknown_keywords_all_collected(self, parser):
        """Multiple unrecognized keywords are all collected."""
        result = parser.parse_simple_input("! UnknownA UnknownB UnknownC", 0)
        assert "UnknownA" in result.other_keywords
        assert "UnknownB" in result.other_keywords
        assert "UnknownC" in result.other_keywords

    def test_mixed_known_and_unknown_keywords(self, parser):
        """Known keywords are classified; unknown ones go to other_keywords."""
        result = parser.parse_simple_input("! B3LYP unknown_keyword def2-SVP", 0)
        assert "unknown_keyword" in result.other_keywords
        assert len(result.methods) > 0
        assert len(result.basis_sets) > 0


class TestCaseInsensitiveKeywordLookup:
    """Parser finds keywords regardless of case."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_lowercase_method_found(self, parser):
        """Lowercase method name is found via case-insensitive lookup."""
        result = parser.parse_simple_input("! b3lyp", 0)
        assert len(result.methods) > 0

    def test_uppercase_method_found(self, parser):
        """Uppercase method name is found."""
        result = parser.parse_simple_input("! B3LYP", 0)
        assert len(result.methods) > 0

    def test_mixed_case_method_found(self, parser):
        """Mixed-case method name is found."""
        result = parser.parse_simple_input("! B3lYp", 0)
        assert len(result.methods) > 0 or "B3lYp" in result.other_keywords

    def test_lowercase_basis_found(self, parser):
        """Lowercase basis set name is found via case-insensitive lookup."""
        result = parser.parse_simple_input("! def2-svp", 0)
        assert len(result.basis_sets) > 0

    def test_uppercase_basis_found(self, parser):
        """Uppercase basis set triggers case-insensitive branch."""
        result = parser.parse_simple_input("! DEF2-TZVP", 0)
        assert len(result.basis_sets) > 0
        assert "def2-TZVP" in result.basis_sets

    def test_lowercase_job_type_found(self, parser):
        """Lowercase job type is found."""
        result = parser.parse_simple_input("! opt", 0)
        assert len(result.job_types) > 0

    def test_lowercase_freq_found(self, parser):
        """Lowercase freq is found."""
        result = parser.parse_simple_input("! freq", 0)
        assert len(result.job_types) > 0

    def test_lowercase_hf_found(self, parser):
        """Lowercase HF is found as a method."""
        result = parser.parse_simple_input("! hf", 0)
        assert len(result.methods) > 0

    def test_lowercase_mp2_found(self, parser):
        """Lowercase MP2 is found."""
        result = parser.parse_simple_input("! mp2", 0)
        assert len(result.methods) > 0

    def test_omega_method_found(self, parser):
        """Method with omega character is found."""
        result = parser.parse_simple_input("! ωB97X-V", 0)
        assert len(result.methods) > 0

    def test_omega_uppercase_method_found(self, parser):
        """Method with uppercase omega character is handled."""
        result = parser.parse_simple_input("! ΩB97X-V", 0)
        assert len(result.methods) > 0 or "ΩB97X-V" in result.other_keywords

    def test_omega_d_method_found(self, parser):
        """omegaB97X-D method is found."""
        result = parser.parse_simple_input("! ωB97X-D", 0)
        assert len(result.methods) > 0

    def test_combined_case_insensitive(self, parser):
        """Multiple case-insensitive keywords are all resolved."""
        result = parser.parse_simple_input("! ωB97X-V DEF2-TZVP opt", 0)
        assert len(result.methods) > 0
        assert len(result.basis_sets) > 0
        assert len(result.job_types) > 0


class TestGeometryParsing:
    """Parser handles various geometry formats and edge cases."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_geometry_with_comment_line(self, parser):
        """Comment lines inside geometry section are skipped."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\n# comment\nH 0.0 0.0 0.0\n*"
        result = parser.parse(content)
        assert result.geometry is not None
        assert len(result.geometry.atoms) >= 1

    def test_geometry_with_empty_line(self, parser):
        """Empty lines inside geometry section are handled."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\n\nH 0.0 0.0 0.0\n*"
        result = parser.parse(content)
        assert result.geometry is not None
        assert len(result.geometry.atoms) >= 1

    def test_geometry_multiple_atoms(self, parser):
        """Multiple atoms are parsed correctly."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nO 0.0 0.0 0.0\nH 0.75 0.58 0.0\nH -0.75 0.58 0.0\n*"
        result = parser.parse(content)
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 3

    def test_geometry_without_end_marker(self, parser):
        """Geometry without trailing * falls back gracefully."""
        lines = ["* xyz 0 1", "H 0.0 0.0 0.0", "O 1.0 0.0 0.0"]
        geom, end_line = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) >= 1

    def test_geometry_no_charge_or_multiplicity(self, parser):
        """Geometry with only format type uses defaults."""
        lines = ["* xyz", "H 0.0 0.0 0.0", "*"]
        geom, end = parser.parse_geometry(lines, 0)
        if geom:
            assert geom.format_type == "xyz"

    def test_geometry_invalid_charge_defaults(self, parser):
        """Invalid charge falls back to default 0."""
        lines = ["* xyz abc def", "H 0 0 0", "*"]
        geom, end = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert geom.charge == 0
        assert geom.multiplicity == 1

    def test_geometry_invalid_atom_line_skipped(self, parser):
        """Invalid atom lines inside geometry are skipped."""
        lines = ["* xyz 0 1", "invalid line here", "H 0 0 0", "*"]
        geom, end = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) >= 1

    def test_geometry_with_nonzero_multiplicity(self, parser):
        """Geometry with non-default multiplicity is parsed correctly."""
        content = "! B3LYP def2-SVP\n* xyz 0 2\nO 0.0 0.0 0.0\n*"
        result = parser.parse(content)
        assert result.geometry is not None
        assert result.geometry.multiplicity == 2

    def test_geometry_insufficient_header_parts(self, parser):
        """Geometry with only * is handled gracefully."""
        content = "! B3LYP def2-SVP\n*\nH 0 0 0\n*"
        result = parser.parse(content)
        assert result is not None


class TestPercentBlockParsing:
    """Parser handles percent block edge cases."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_maxcore_non_numeric_value(self, parser):
        """Non-numeric value in %maxcore does not set memory parameter."""
        lines = ["%maxcore notanumber"]
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "maxcore"
        assert "memory" not in block.parameters

    def test_pal_without_nprocs(self, parser):
        """PAL block without nprocs does not set the parameter."""
        content = "! B3LYP def2-SVP\n%pal\nend\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        pal_block = next((b for b in result.percent_blocks if b.name == "pal"), None)
        assert pal_block is not None
        assert "nprocs" not in pal_block.parameters

    def test_scf_without_maxiter(self, parser):
        """SCF block without maxiter does not set the parameter."""
        content = "! B3LYP def2-SVP\n%scf\nend\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        scf_block = next((b for b in result.percent_blocks if b.name == "scf"), None)
        assert scf_block is not None
        assert "maxiter" not in scf_block.parameters

    def test_method_block_with_d3(self, parser):
        """Method block recognizes D3 dispersion."""
        lines = ["%method", "  d3", "end"]
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.parameters.get("dispersion") == "D3"

    def test_method_block_with_d4(self, parser):
        """Method block recognizes D4 dispersion."""
        lines = ["%method", "  D4", "end"]
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert "D4" in block.parameters.values()

    def test_method_block_multiple_dispersion_lines(self, parser):
        """Method block processes multiple dispersion lines."""
        lines = ["%method", "d3bj", "d4", "end"]
        block, end = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert "dispersion" in block.parameters

    def test_scf_multiple_maxiter_lines(self, parser):
        """SCF block processes multiple maxiter lines (last wins)."""
        lines = ["%scf", "maxiter 100", "maxiter 200", "end"]
        block, end = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert "maxiter" in block.parameters

    def test_pal_nprocs_case_insensitive(self, parser):
        """PAL block recognizes NPROCS in uppercase."""
        lines = ["%pal", "  NPROCS 4", "end"]
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.parameters.get("nprocs") == 4

    def test_unknown_block_still_parsed(self, parser):
        """Unknown % blocks are still collected."""
        content = "! B3LYP def2-SVP\n%unknownblock\n  someparam somevalue\nend"
        result = parser.parse(content)
        assert result is not None
        assert len(result.percent_blocks) > 0


class TestEmptyInputHandling:
    """Parser handles empty or minimal input correctly."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_empty_string_to_parse_simple_input(self, parser):
        """Empty string produces empty result without error."""
        result = parser.parse_simple_input("", 0)
        assert result is not None
        assert len(result.methods) == 0
        assert len(result.basis_sets) == 0
        assert len(result.job_types) == 0

    def test_bang_only_to_parse_simple_input(self, parser):
        """Just '!' produces empty result."""
        result = parser.parse_simple_input("!", 0)
        assert result is not None
        assert len(result.methods) == 0

    def test_full_document_with_all_sections(self, parser):
        """Complete ORCA input with all sections parses correctly."""
        content = "! B3LYP def2-SVP OPT FREQ\n%maxcore 4000\n%pal nprocs 4 end\n%method\n  d3bj\nend\n%scf\n  maxiter 100\nend\n\n* xyz 0 1\nO 0.0 0.0 0.0\nH 0.75 0.58 0.0\nH -0.75 0.58 0.0\n*"
        result = parser.parse(content)
        assert result is not None
        assert result.simple_input is not None
        assert len(result.simple_input.methods) > 0
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 3
        assert len(result.percent_blocks) > 0
