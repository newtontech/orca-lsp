"""Tests for ORCA LSP server"""

import pytest
from orca_lsp.server import ORCALanguageServer
from orca_lsp.keywords import (
    DFT_FUNCTIONALS,
    WAVEFUNCTION_METHODS,
    BASIS_SETS,
    JOB_TYPES,
    PERCENT_BLOCKS,
)


class TestCompletions:
    """Tests for completion features"""
    
    def test_method_completions(self):
        server = ORCALanguageServer()
        completions = server._get_method_completions()
        
        labels = [c.label for c in completions]
        
        # Check DFT functionals
        assert "B3LYP" in labels
        assert "PBE" in labels
        
        # Check wavefunction methods
        assert "HF" in labels
        assert "MP2" in labels
    
    def test_basis_completions(self):
        server = ORCALanguageServer()
        completions = server._get_basis_completions()
        
        labels = [c.label for c in completions]
        
        assert "def2-SVP" in labels
        assert "6-31G*" in labels
        assert "cc-pVTZ" in labels
    
    def test_job_completions(self):
        server = ORCALanguageServer()
        completions = server._get_job_completions()
        
        labels = [c.label for c in completions]
        
        assert "OPT" in labels
        assert "FREQ" in labels
        assert "SP" in labels
    
    def test_percent_block_completions(self):
        server = ORCALanguageServer()
        
        # Test completing block name
        completions = server._get_percent_completions("%")
        
        labels = [c.label for c in completions]
        assert "maxcore" in labels
        assert "pal" in labels
        assert "method" in labels
    
    def test_simple_input_context(self):
        server = ORCALanguageServer()
        
        from lsprotocol.types import Position
        completions = server._get_completions("! ", Position(line=0, character=2))
        
        labels = [c.label for c in completions]
        assert "B3LYP" in labels or "HF" in labels


class TestHover:
    """Tests for hover documentation"""
    
    def test_get_word_at_position(self):
        server = ORCALanguageServer()
        
        # Create a mock document
        class MockDoc:
            lines = ["! B3LYP def2-SVP"]
            source = "! B3LYP def2-SVP"
        
        from lsprotocol.types import Position
        
        # Test getting word at different positions
        word = server._get_word_at_position(MockDoc(), Position(line=0, character=3))
        # This should get "B3LYP"
        assert word.isalpha()


class TestBlockSpecificCompletions:
    """Tests for % block specific completions"""
    
    def test_maxcore_completions(self):
        server = ORCALanguageServer()
        completions = server._get_block_specific_completions("maxcore")
        
        labels = [c.label for c in completions]
        assert any("MB" in label for label in labels)
    
    def test_pal_completions(self):
        server = ORCALanguageServer()
        completions = server._get_block_specific_completions("pal")
        
        labels = [c.label for c in completions]
        assert "nprocs" in labels
    
    def test_method_completions(self):
        server = ORCALanguageServer()
        completions = server._get_block_specific_completions("method")
        
        labels = [c.label for c in completions]
        assert "D3" in labels or "D3BJ" in labels or "D4" in labels
    
    def test_scf_completions(self):
        server = ORCALanguageServer()
        completions = server._get_block_specific_completions("scf")
        
        labels = [c.label for c in completions]
        assert "maxiter" in labels
