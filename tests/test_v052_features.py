"""Tests for v0.5.2 new features"""

from orca_lsp.keywords import DFT_FUNCTIONALS, PERCENT_BLOCKS


class TestNewFunctionals:
    def test_new_functionals_exist(self):
        """Test that new functionals are present"""
        assert len(DFT_FUNCTIONALS) >= 45

    def test_wb97x_d3_exists(self):
        """Test omegaB97X-D3 exists"""
        assert "ωB97X-D3" in DFT_FUNCTIONALS

    def test_m11_exists(self):
        """Test M11 exists"""
        assert "M11" in DFT_FUNCTIONALS

    def test_dsd_pbep86_exists(self):
        """Test DSD-PBEP86 exists"""
        assert "DSD-PBEP86" in DFT_FUNCTIONALS


class TestNewPercentBlocks:
    def test_symmetry_block_exists(self):
        """Test %symmetry block exists"""
        assert "symmetry" in PERCENT_BLOCKS

    def test_rels_block_exists(self):
        """Test %rels block exists"""
        assert "rels" in PERCENT_BLOCKS

    def test_cis_block_exists(self):
        """Test %cis block exists"""
        assert "cis" in PERCENT_BLOCKS

    def test_tddft_block_exists(self):
        """Test %tddft block exists"""
        assert "tddft" in PERCENT_BLOCKS

    def test_mrcc_block_exists(self):
        """Test %mrcc block exists"""
        assert "mrcc" in PERCENT_BLOCKS
