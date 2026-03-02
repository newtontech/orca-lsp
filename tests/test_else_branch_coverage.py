"""Tests for if statement else branch coverage."""

import pytest
from orca_lsp.parser import ORCAParser


class TestIfElseBranchCoverage:
    """Test if/else branch coverage in parser."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_pal_block_with_nprocs_but_no_number(self, parser):
        """Test %pal block with 'nprocs' keyword but no number.
        
        This covers the else branch of 'if match:' at line 253->250.
        The line contains 'nprocs' but regex doesn't match a number.
        """
        content = """! B3LYP def2-SVP
%pal
  nprocs
end
* xyz 0 1
H 0 0 0
*
"""
        result = parser.parse(content)
        pal_block = next((b for b in result.percent_blocks if b.name == 'pal'), None)
        assert pal_block is not None
        # Should not have nprocs parameter (regex didn't match)
        assert 'nprocs' not in pal_block.parameters

    def test_scf_block_with_maxiter_but_no_number(self, parser):
        """Test %scf block with 'maxiter' keyword but no number.
        
        This covers the else branch of 'if match:' at line 273->269.
        The line contains 'maxiter' but regex doesn't match a number.
        """
        content = """! B3LYP def2-SVP
%scf
  maxiter
end
* xyz 0 1
H 0 0 0
*
"""
        result = parser.parse(content)
        scf_block = next((b for b in result.percent_blocks if b.name == 'scf'), None)
        assert scf_block is not None
        # Should not have maxiter parameter (regex didn't match)
        assert 'maxiter' not in scf_block.parameters
