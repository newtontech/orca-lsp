"""Tests for ORCA keywords."""
import pytest

from orca_lsp.keywords import (
    DFT_FUNCTIONALS,
    WAVEFUNCTION_METHODS,
    BASIS_SETS,
    JOB_TYPES,
    PERCENT_BLOCKS,
    ELEMENTS,
)


class TestKeywords:
    """Test keyword definitions."""

    def test_dft_functionals(self):
        """Test DFT functionals are defined."""
        assert isinstance(DFT_FUNCTIONALS, dict)
        assert len(DFT_FUNCTIONALS) > 0

    def test_wavefunction_methods(self):
        """Test wavefunction methods are defined."""
        assert isinstance(WAVEFUNCTION_METHODS, dict)

    def test_basis_sets(self):
        """Test basis sets are defined."""
        assert isinstance(BASIS_SETS, dict)
        assert len(BASIS_SETS) > 0

    def test_job_types(self):
        """Test job types are defined."""
        assert isinstance(JOB_TYPES, dict)
        assert len(JOB_TYPES) > 0

    def test_percent_blocks(self):
        """Test percent blocks are defined."""
        assert isinstance(PERCENT_BLOCKS, dict)
        assert len(PERCENT_BLOCKS) > 0

    def test_elements(self):
        """Test elements are defined."""
        assert isinstance(ELEMENTS, list)
        assert len(ELEMENTS) > 0
        assert "H" in ELEMENTS
        assert "C" in ELEMENTS
        assert "O" in ELEMENTS
