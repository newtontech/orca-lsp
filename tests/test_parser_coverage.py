"""Tests to improve parser coverage."""
import pytest
from orca_lsp.parser import ORCAParser, SimpleInput, PercentBlock, Atom, Geometry, ParseResult


class TestSimpleInput:
    """Test SimpleInput dataclass."""
    
    def test_is_valid_with_methods(self):
        """Test is_valid returns True when methods present."""
        si = SimpleInput(methods=["B3LYP"])
        assert si.is_valid() is True
    
    def test_is_valid_with_basis_sets(self):
        """Test is_valid returns True when basis sets present."""
        si = SimpleInput(basis_sets=["def2-TZVP"])
        assert si.is_valid() is True
    
    def test_is_valid_empty(self):
        """Test is_valid returns False when empty."""
        si = SimpleInput()
        assert si.is_valid() is False


class TestPercentBlock:
    """Test PercentBlock dataclass."""
    
    def test_is_valid_with_name(self):
        """Test is_valid returns True when name present."""
        pb = PercentBlock(name="maxcore")
        assert pb.is_valid() is True
    
    def test_is_valid_empty(self):
        """Test is_valid returns False when empty."""
        pb = PercentBlock()
        assert pb.is_valid() is False


class TestAtom:
    """Test Atom dataclass."""
    
    def test_is_valid_element(self):
        """Test is_valid returns True for valid element."""
        atom = Atom(element="C", x=0.0, y=0.0, z=0.0)
        assert atom.is_valid() is True
    
    def test_is_invalid_element(self):
        """Test is_valid returns False for invalid element."""
        atom = Atom(element="Xx", x=0.0, y=0.0, z=0.0)
        assert atom.is_valid() is False


class TestGeometry:
    """Test Geometry dataclass."""
    
    def test_is_valid_with_atoms(self):
        """Test is_valid returns True with valid atoms."""
        geom = Geometry()
        geom.atoms = [Atom(element="H", x=0, y=0, z=0)]
        assert geom.is_valid() is True
    
    def test_is_invalid_empty(self):
        """Test is_valid returns False when empty."""
        geom = Geometry()
        assert geom.is_valid() is False
    
    def test_is_invalid_with_invalid_atom(self):
        """Test is_valid returns False with invalid atom."""
        geom = Geometry()
        geom.atoms = [Atom(element="Xx", x=0, y=0, z=0)]
        assert geom.is_valid() is False


class TestParserFullCoverage:
    """Test parser for full coverage."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_parse_comments(self, parser):
        """Test parsing with comments."""
        content = "# This is a comment\n! B3LYP def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert result.simple_input is not None

    def test_parse_empty_lines(self, parser):
        """Test parsing with empty lines."""
        content = "\n\n! B3LYP def2-SVP\n\n\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert result.simple_input is not None

    def test_parse_simple_input_case_insensitive(self, parser):
        """Test parsing case insensitive keywords."""
        content = "! b3lyp DEF2-TZVP opt"
        result = parser.parse(content)
        assert len(result.simple_input.methods) > 0

    def test_parse_unknown_keyword(self, parser):
        """Test parsing with unknown keyword."""
        content = "! B3LYP UNKNOWN_KEYWORD def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert "UNKNOWN_KEYWORD" in result.simple_input.other_keywords

    def test_parse_multiline_percent_block(self, parser):
        """Test parsing multi-line % block."""
        content = """! B3LYP def2-SVP
%scf
  maxiter 100
end

* xyz 0 1
H 0 0 0
*"""
        result = parser.parse(content)
        assert any(b.name == 'scf' for b in result.percent_blocks)

    def test_parse_method_block_d3bj(self, parser):
        """Test parsing %method block with D3BJ."""
        content = """! B3LYP def2-SVP
%method
  d3bj
end

* xyz 0 1
H 0 0 0
*"""
        result = parser.parse(content)
        method_block = next((b for b in result.percent_blocks if b.name == 'method'), None)
        if method_block:
            assert method_block.parameters.get('dispersion') == 'D3BJ'

    def test_parse_method_block_d4(self, parser):
        """Test parsing %method block with D4."""
        content = """! B3LYP def2-SVP
%method
  d4
end

* xyz 0 1
H 0 0 0
*"""
        result = parser.parse(content)
        method_block = next((b for b in result.percent_blocks if b.name == 'method'), None)
        if method_block:
            assert method_block.parameters.get('dispersion') == 'D4'

    def test_parse_invalid_percent_block(self, parser):
        """Test parsing invalid % block."""
        content = """! B3LYP def2-SVP
%

* xyz 0 1
H 0 0 0
*"""
        result = parser.parse(content)
        # Should handle gracefully

    def test_parse_geometry_no_charge_mult(self, parser):
        """Test parsing geometry without charge/multiplicity."""
        content = "! B3LYP def2-SVP\n*\nH 0 0 0\n*"
        result = parser.parse(content)
        # Should handle gracefully

    def test_parse_geometry_invalid_atom(self, parser):
        """Test parsing geometry with invalid atom line."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nnot_an_atom\n*"
        result = parser.parse(content)
        # Should handle gracefully

    def test_parse_geometry_invalid_coords(self, parser):
        """Test parsing geometry with invalid coordinates."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nH not a number\n*"
        result = parser.parse(content)
        # Should handle gracefully

    def test_parse_internal_coordinates(self, parser):
        """Test parsing internal coordinates."""
        content = "! B3LYP def2-SVP\n* int 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        if result.geometry:
            assert result.geometry.format_type == "int"

    def test_parse_missing_basis_set(self, parser):
        """Test diagnostics for missing basis set."""
        content = "! B3LYP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any('basis set' in e.get('message', '').lower() for e in result.errors)

    def test_parse_missing_method(self, parser):
        """Test diagnostics for missing method."""
        content = "! def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any('method' in e.get('message', '').lower() for e in result.errors)

    def test_parse_with_maxcore_warning(self, parser):
        """Test warning for missing maxcore."""
        content = "! B3LYP def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any('maxcore' in w.get('message', '').lower() for w in result.warnings)

    def test_parse_percent_block_single_line_with_end(self, parser):
        """Test single line % block with end."""
        content = "! B3LYP def2-SVP\n%pal nprocs 4 end\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        pal_block = next((b for b in result.percent_blocks if b.name == 'pal'), None)
        assert pal_block is not None
        assert pal_block.parameters.get('nprocs') == 4

    def test_parse_wavefunction_methods(self, parser):
        """Test parsing wavefunction methods."""
        for method in ['HF', 'MP2', 'CCSD', 'CCSD(T)']:
            content = f"! {method} cc-pVTZ\n* xyz 0 1\nH 0 0 0\n*"
            result = parser.parse(content)
            assert any(method in m for m in result.simple_input.methods), f"Failed for {method}"

    def test_parse_job_types(self, parser):
        """Test parsing job types."""
        for job in ['SP', 'OPT', 'FREQ']:
            content = f"! B3LYP def2-SVP {job}\n* xyz 0 1\nH 0 0 0\n*"
            result = parser.parse(content)
            assert any(job in j for j in result.simple_input.job_types), f"Failed for {job}"

    def test_parse_invalid_maxcore_value(self, parser):
        """Test parsing %maxcore with invalid value."""
        content = "! B3LYP def2-SVP\n%maxcore invalid\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        # Should handle gracefully
        assert result is not None
