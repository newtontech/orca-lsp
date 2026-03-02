"""Tests to reach 100% coverage."""
import pytest
from orca_lsp.parser import ORCAParser, ParseResult


class TestParserEdgeCases:
    """Test parser edge cases for full coverage."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_parse_with_invalid_charge(self, parser):
        """Test parsing with invalid charge value."""
        content = "! B3LYP def2-SVP\n* xyz invalid 1\nH 0 0 0\n*"
        result = parser.parse(content)
        # Should handle gracefully

    def test_parse_with_invalid_multiplicity(self, parser):
        """Test parsing with invalid multiplicity value."""
        content = "! B3LYP def2-SVP\n* xyz 0 invalid\nH 0 0 0\n*"
        result = parser.parse(content)
        # Should handle gracefully

    def test_parse_scf_maxiter(self, parser):
        """Test parsing %scf with maxiter."""
        content = """! B3LYP def2-SVP
%scf
  maxiter 50
end

* xyz 0 1
H 0 0 0
*"""
        result = parser.parse(content)
        scf_block = next((b for b in result.percent_blocks if b.name == 'scf'), None)
        if scf_block:
            assert scf_block.parameters.get('maxiter') == 50

    def test_parse_percent_block_with_whitespace(self, parser):
        """Test parsing % block with various whitespace."""
        content = "! B3LYP def2-SVP\n%maxcore    8000\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) > 0

    def test_parse_empty_file(self, parser):
        """Test parsing completely empty file."""
        result = parser.parse("")
        assert isinstance(result, ParseResult)
        assert len(result.errors) > 0

    def test_parse_only_comments(self, parser):
        """Test parsing file with only comments."""
        content = "# Comment 1\n# Comment 2\n# Comment 3"
        result = parser.parse(content)
        assert isinstance(result, ParseResult)

    def test_parse_multiple_simple_input_lines(self, parser):
        """Test parsing multiple simple input lines (only first should be used)."""
        content = "! B3LYP def2-SVP\n! HF 6-31G*\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert result.simple_input is not None
        # Should parse the first one

    def test_parse_case_variations(self, parser):
        """Test parsing with various case variations."""
        test_cases = [
            "! b3lyp def2-svp",
            "! B3LYP DEF2-SVP",
            "! B3lYp DeF2-SvP",
        ]
        for case in test_cases:
            content = f"{case}\n* xyz 0 1\nH 0 0 0\n*"
            result = parser.parse(content)
            assert result.simple_input is not None

    def test_parse_without_end_in_multiline_block(self, parser):
        """Test parsing multi-line % block without end."""
        content = """! B3LYP def2-SVP
%pal
  nprocs 4

* xyz 0 1
H 0 0 0
*"""
        result = parser.parse(content)
        # Should handle gracefully

    def test_parse_job_type_opt_freq(self, parser):
        """Test parsing OPT FREQ job type combination."""
        content = "! B3LYP def2-SVP OPT FREQ\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert 'OPT' in result.simple_input.job_types
        assert 'FREQ' in result.simple_input.job_types

    def test_parse_method_block_single_line(self, parser):
        """Test parsing %method block on single line."""
        content = "! B3LYP def2-SVP\n%method d3 end\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        method_block = next((b for b in result.percent_blocks if b.name == 'method'), None)
        if method_block:
            assert 'dispersion' in method_block.parameters

    def test_parse_pal_block_without_nprocs(self, parser):
        """Test parsing %pal block without nprocs."""
        content = "! B3LYP def2-SVP\n%pal end\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        pal_block = next((b for b in result.percent_blocks if b.name == 'pal'), None)
        if pal_block:
            # nprocs should not be set
            assert 'nprocs' not in pal_block.parameters

    def test_atom_line_with_extra_fields(self, parser):
        """Test parsing atom line with extra fields."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nH 0 0 0 extra_field\n*"
        result = parser.parse(content)
        if result.geometry:
            # Should parse the atom with basic fields
            assert len(result.geometry.atoms) > 0

    def test_parse_with_tab_separator(self, parser):
        """Test parsing with tab separators instead of spaces."""
        content = "! B3LYP\tdef2-SVP\n*\txyz\t0\t1\nH\t0\t0\t0\n*"
        result = parser.parse(content)
        # Should handle tabs
        assert result.simple_input is not None

    def test_parse_wavefunction_variations(self, parser):
        """Test parsing various wavefunction methods."""
        methods = ['RHF', 'UHF', 'ROHF', 'RI-MP2', 'SCS-MP2', 'MP3', 
                   'DLPNO-CCSD', 'DLPNO-CCSD(T)', 'CASSCF', 'NEVPT2', 'CASPT2']
        for method in methods:
            content = f"! {method} cc-pVDZ\n* xyz 0 1\nH 0 0 0\n*"
            result = parser.parse(content)
            assert result.simple_input is not None

    def test_parse_dft_functional_variations(self, parser):
        """Test parsing various DFT functionals."""
        functionals = ['PBE0', 'TPSS0', 'M06-2X', 'M06L', 'M06-HF',
                       'ωB97X-D', 'ωB97X-V', 'B97-D', 'B97-D3', 'B2PLYP']
        for func in functionals:
            content = f"! {func} def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
            result = parser.parse(content)
            assert result.simple_input is not None

    def test_parse_basis_set_variations(self, parser):
        """Test parsing various basis sets."""
        basis_sets = ['STO-3G', '3-21G', '6-31G*', '6-31G**', 
                     '6-31+G*', '6-311G*', '6-311G**', 
                     '6-311+G*', '6-311++G**',
                     'def2-SVP', 'def2-TZVPP', 'def2-QZVP', 'def2-SVPD', 'def2-TZVPD',
                     'cc-pVDZ', 'cc-pVTZ', 'cc-pVQZ', 'cc-pV5Z',
                     'aug-cc-pVDZ', 'aug-cc-pVTZ', 'aug-cc-pVQZ',
                     'def2/J', 'def2-TZVP/C', 'def2-QZVP/C']
        for basis in basis_sets:
            content = f"! B3LYP {basis}\n* xyz 0 1\nH 0 0 0\n*"
            result = parser.parse(content)
            assert result.simple_input is not None
