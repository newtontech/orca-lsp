"""Tests for ORCA parser"""

import pytest
from orca_lsp.parser import ORCAParser, SimpleInput, PercentBlock, Geometry


class TestSimpleInputParser:
    """Tests for simple input (!) parsing"""
    
    def test_parse_dft_method(self):
        parser = ORCAParser()
        result = parser.parse_simple_input("! B3LYP def2-SVP", 0)
        
        assert "B3LYP" in result.methods
        assert "def2-SVP" in result.basis_sets
    
    def test_parse_hf_method(self):
        parser = ORCAParser()
        result = parser.parse_simple_input("! HF 6-31G*", 0)
        
        assert "HF" in result.methods
        assert "6-31G*" in result.basis_sets
    
    def test_parse_job_types(self):
        parser = ORCAParser()
        result = parser.parse_simple_input("! B3LYP def2-TZVP OPT FREQ", 0)
        
        assert "OPT" in result.job_types
        assert "FREQ" in result.job_types
    
    def test_parse_wavefunction_methods(self):
        parser = ORCAParser()
        
        methods = ["MP2", "CCSD", "CCSD(T)", "DLPNO-CCSD(T)"]
        for method in methods:
            result = parser.parse_simple_input(f"! {method} def2-TZVP", 0)
            assert method in result.methods
    
    def test_parse_case_insensitive(self):
        parser = ORCAParser()
        result = parser.parse_simple_input("! b3lyp DEF2-SVP opt", 0)
        
        # Should recognize keywords regardless of case
        assert len(result.methods) > 0
        assert len(result.basis_sets) > 0
    
    def test_parse_multiple_methods(self):
        parser = ORCAParser()
        result = parser.parse_simple_input("! B3LYP D4 def2-TZVP OPT", 0)
        
        assert "B3LYP" in result.methods


class TestPercentBlockParser:
    """Tests for % block parsing"""
    
    def test_parse_maxcore(self):
        parser = ORCAParser()
        lines = ["%maxcore 4000"]
        block, end = parser.parse_percent_block(lines, 0)
        
        assert block.name == "maxcore"
        assert block.parameters['memory'] == 4000
    
    def test_parse_pal(self):
        parser = ORCAParser()
        lines = [
            "%pal",
            "  nprocs 4",
            "end"
        ]
        block, end = parser.parse_percent_block(lines, 0)
        
        assert block.name == "pal"
        assert block.parameters['nprocs'] == 4
        assert end == 2
    
    def test_parse_pal_single_line(self):
        parser = ORCAParser()
        lines = ["%pal nprocs 8 end"]
        block, end = parser.parse_percent_block(lines, 0)
        
        assert block.name == "pal"
        assert block.parameters['nprocs'] == 8
    
    def test_parse_method_block(self):
        parser = ORCAParser()
        lines = [
            "%method",
            "  D3BJ",
            "end"
        ]
        block, end = parser.parse_percent_block(lines, 0)
        
        assert block.name == "method"
        assert block.parameters.get('dispersion') == "D3BJ"
    
    def test_parse_scf_block(self):
        parser = ORCAParser()
        lines = [
            "%scf",
            "  maxiter 200",
            "end"
        ]
        block, end = parser.parse_percent_block(lines, 0)
        
        assert block.name == "scf"
        assert block.parameters['maxiter'] == 200


class TestGeometryParser:
    """Tests for geometry section parsing"""
    
    def test_parse_xyz_geometry(self):
        parser = ORCAParser()
        lines = [
            "* xyz 0 1",
            "  O   0.000000   0.000000   0.000000",
            "  H   0.757160   0.586260   0.000000",
            "  H  -0.757160   0.586260   0.000000",
            "*"
        ]
        geom, end = parser.parse_geometry(lines, 0)
        
        assert geom.charge == 0
        assert geom.multiplicity == 1
        assert len(geom.atoms) == 3
        assert geom.atoms[0].element == "O"
        assert geom.atoms[0].x == 0.0
    
    def test_parse_charge_multiplicity(self):
        parser = ORCAParser()
        lines = [
            "* xyz -1 2",
            "  C   0.000000   0.000000   0.000000",
            "*"
        ]
        geom, end = parser.parse_geometry(lines, 0)
        
        assert geom.charge == -1
        assert geom.multiplicity == 2
    
    def test_parse_internal_coords(self):
        parser = ORCAParser()
        lines = [
            "* int 0 1",
            "  C",
            "  H   1   1.08",
            "*"
        ]
        geom, end = parser.parse_geometry(lines, 0)
        
        assert geom.format_type == "int"


class TestFullParse:
    """Tests for full document parsing"""
    
    def test_parse_simple_input(self):
        content = """
! B3LYP def2-TZVP OPT

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
*
"""
        parser = ORCAParser()
        result = parser.parse(content)
        
        assert result.simple_input is not None
        assert "B3LYP" in result.simple_input.methods
        assert "def2-TZVP" in result.simple_input.basis_sets
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 2
    
    def test_parse_with_percent_blocks(self):
        content = """
! HF 6-31G* SP
%maxcore 2000
%pal nprocs 2 end

* xyz 0 1
  He  0.0  0.0  0.0
*
"""
        parser = ORCAParser()
        result = parser.parse(content)
        
        assert len(result.percent_blocks) == 2
        assert result.percent_blocks[0].name == "maxcore"
        assert result.percent_blocks[1].name == "pal"
    
    def test_diagnostics_missing_simple_input(self):
        content = """
* xyz 0 1
  H  0.0  0.0  0.0
*
"""
        parser = ORCAParser()
        result = parser.parse(content)
        
        assert any("Missing simple input" in e['message'] for e in result.errors)
    
    def test_diagnostics_missing_geometry(self):
        content = """
! B3LYP def2-SVP
"""
        parser = ORCAParser()
        result = parser.parse(content)
        
        assert any("Missing geometry" in e['message'] for e in result.errors)
    
    def test_diagnostics_invalid_element(self):
        content = """
! HF 6-31G*

* xyz 0 1
  Xx  0.0  0.0  0.0
*
"""
        parser = ORCAParser()
        result = parser.parse(content)
        
        assert any("Invalid element" in e['message'] for e in result.errors)
    
    def test_warning_missing_maxcore(self):
        content = """
! HF 6-31G*

* xyz 0 1
  H  0.0  0.0  0.0
*
"""
        parser = ORCAParser()
        result = parser.parse(content)
        
        assert any("Missing %maxcore" in w['message'] for w in result.warnings)


class TestEdgeCases:
    """Tests for edge cases"""
    
    def test_empty_file(self):
        parser = ORCAParser()
        result = parser.parse("")
        
        assert result.simple_input is None
        assert result.geometry is None
    
    def test_comments_ignored(self):
        content = """
# This is a comment
! B3LYP def2-SVP
# Another comment

* xyz 0 1
  H  0.0  0.0  0.0
*
"""
        parser = ORCAParser()
        result = parser.parse(content)
        
        assert result.simple_input is not None
    
    def test_multiple_percent_blocks(self):
        content = """
! HF 6-31G*
%maxcore 4000
%pal nprocs 4 end
%scf maxiter 300 end

* xyz 0 1
  H  0.0  0.0  0.0
*
"""
        parser = ORCAParser()
        result = parser.parse(content)
        
        assert len(result.percent_blocks) == 3
        block_names = [b.name for b in result.percent_blocks]
        assert "maxcore" in block_names
        assert "pal" in block_names
        assert "scf" in block_names
