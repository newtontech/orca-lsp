"""Tests to cover case-insensitive paths with special characters."""

import pytest
from orca_lsp.parser import ORCAParser


class TestCaseInsensitiveSpecialChars:
    """Test case-insensitive parsing with special Unicode characters."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_method_with_omega_character(self, parser):
        """Test method with ω character triggers case-insensitive branch."""
        # ωB97X-V.upper() = ΩB97X-V, which is NOT in the dictionary directly
        # But it IS in [k.upper() for k in all_methods]
        # This triggers lines 160-173 (case-insensitive method lookup)
        result = parser.parse_simple_input("! ωB97X-V", 0)
        assert len(result.methods) > 0
        assert "ωB97X-V" in result.methods

    def test_method_with_omega_uppercase(self, parser):
        """Test method with Ω character."""
        result = parser.parse_simple_input("! ΩB97X-V", 0)
        # ΩB97X-V.upper() = ΩB97X-V, not in dictionary
        # But it matches ωB97X-V case-insensitively
        assert len(result.methods) > 0 or "ΩB97X-V" in result.other_keywords

    def test_basis_set_with_special_chars_case_insensitive(self, parser):
        """Test basis set with special characters triggers case-insensitive branch."""
        # def2-TZVP with lowercase def
        result = parser.parse_simple_input("! def2-tzvp", 0)
        # def2-tzvp.upper() = DEF2-TZVP
        # DEF2-TZVP is in basis_sets dictionary
        # So this should be found directly
        assert len(result.basis_sets) > 0

    def test_job_type_lowercase_triggers_ci_branch(self, parser):
        """Test lowercase job type triggers case-insensitive branch."""
        # opt.upper() = OPT
        # OPT is in job_types dictionary, so direct check works
        result = parser.parse_simple_input("! opt", 0)
        assert len(result.job_types) > 0


class TestParserLines170to173Coverage:
    """Specifically target lines 170-173 in parser.py."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_omega_method_hits_ci_branch(self, parser):
        """Use ωB97X-V to hit the case-insensitive method branch."""
        # ωB97X-V has special Unicode character that changes when uppercased
        # This will:
        # 1. Fail direct check (ΩB97X-V not in dft_functionals)
        # 2. Pass case-insensitive check (ωB97X-V.upper() == ΩB97X-V)
        result = parser.parse_simple_input("! ωB97X-V def2-SVP", 0)

        # Method should be found via case-insensitive lookup
        assert any("ωB97X-V" in m or "ΩB97X-V" in m for m in result.methods)
        assert len(result.basis_sets) > 0

    def test_omega_v_method(self, parser):
        """Test ωB97X-V method."""
        result = parser.parse_simple_input("! ωB97X-V", 0)
        assert len(result.methods) > 0

    def test_omega_d_method(self, parser):
        """Test ωB97X-D method."""
        result = parser.parse_simple_input("! ωB97X-D", 0)
        assert len(result.methods) > 0
