"""Tests to achieve 100% coverage - targeting specific missing lines."""

import pytest
from unittest.mock import MagicMock, PropertyMock, patch

from orca_lsp.parser import ORCAParser
from orca_lsp.server import ORCALanguageServer
from lsprotocol.types import (
    HoverParams,
    Position,
    TextDocumentIdentifier,
)


class TestParserMissingCoverage:
    """Test specific missing coverage lines in parser.py."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_case_insensitive_method_with_correct_case_in_list(self, parser):
        """Test case-insensitive lookup when method is found in all_methods.

        This covers lines 160->145: the break after finding the correct case method.
        """
        # Use a method that exists but with different case
        # B3LYP exists, so we use b3lyp (lowercase)
        result = parser.parse_simple_input("! b3lyp", 0)
        # Should find B3LYP case-insensitively
        assert len(result.methods) >= 1
        # The method found should be B3LYP (correct case)
        assert any("b3lyp" in m.lower() for m in result.methods)

    def test_case_insensitive_basis_with_correct_case_in_list(self, parser):
        """Test case-insensitive lookup when basis is found in basis_sets.

        This covers lines 165->145: the break after finding the correct case basis.
        """
        # Use a basis set that exists but with different case
        result = parser.parse_simple_input("! B3LYP DEF2-SVP", 0)
        # Should find def2-SVP case-insensitively
        assert len(result.basis_sets) >= 1

    def test_unknown_keyword_other_keywords_append(self, parser):
        """Test that unknown keywords go to other_keywords.

        This covers lines 170-173: the else branch that appends to other_keywords.
        """
        result = parser.parse_simple_input("! TotallyUnknownKeyword12345", 0)
        # Should go to other_keywords
        assert "TotallyUnknownKeyword12345" in result.other_keywords
        assert len(result.methods) == 0
        assert len(result.basis_sets) == 0
        assert len(result.job_types) == 0

    def test_multiple_unknown_keywords(self, parser):
        """Test multiple unknown keywords."""
        result = parser.parse_simple_input("! UnknownA UnknownB UnknownC", 0)
        assert "UnknownA" in result.other_keywords
        assert "UnknownB" in result.other_keywords
        assert "UnknownC" in result.other_keywords

    def test_percent_block_single_line_no_end_no_numeric(self, parser):
        """Test single-line block with non-numeric value that fails int().

        This covers the except ValueError pass branch around line 258->255.
        """
        lines = ["%maxcore notanumber"]
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "maxcore"
        # Should not have memory set due to ValueError
        assert "memory" not in block.parameters

    def test_geometry_no_end_marker_fallback(self, parser):
        """Test geometry parsing when no end marker is found.

        This covers the fallback path at line 278->274.
        """
        # Geometry without trailing * and without reaching end of file naturally
        lines = [
            "* xyz 0 1",
            "H 0.0 0.0 0.0",
            "O 1.0 0.0 0.0",
        ]  # No * at end
        geom, end_line = parser.parse_geometry(lines, 0)
        # Should still parse and return atoms
        assert geom is not None
        assert len(geom.atoms) >= 1


class TestServerMissingCoverage:
    """Test specific missing coverage lines in server.py."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_hover_unknown_keyword_returns_none(self, server):
        """Test hover on unknown keyword returns None.

        This covers lines 265-266: the final return None in _on_hover.
        """
        mock_doc = MagicMock()
        mock_doc.lines = ["! UNKNOWN_KEYWORD_XYZ"]
        mock_doc.source = "! UNKNOWN_KEYWORD_XYZ"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.inp"),
                position=Position(line=0, character=4),  # Position at UNKNOWN
            )

            result = server._on_hover(params)
            # Should return None for unknown keyword
            assert result is None

    def test_hover_empty_word_returns_none(self, server):
        """Test hover with empty word returns None."""
        mock_doc = MagicMock()
        mock_doc.lines = ["!    "]
        mock_doc.source = "!    "

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.inp"),
                position=Position(line=0, character=3),  # Position at space
            )

            result = server._on_hover(params)
            # Empty word should return None
            assert result is None


class TestParserFullCoverageExtras:
    """Additional tests for complete parser coverage."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_parse_with_all_block_types(self, parser):
        """Test parsing with all major block types."""
        content = """! B3LYP def2-SVP Opt
%maxcore 4000
%pal nprocs 4 end
%scf
  maxiter 100
end
%method
  d3bj
end
* xyz 0 1
H 0.0 0.0 0.0
H 0.75 0.0 0.0
*
"""
        result = parser.parse(content)
        assert result.simple_input is not None
        assert any(b.name == "maxcore" for b in result.percent_blocks)
        assert any(b.name == "pal" for b in result.percent_blocks)
        assert any(b.name == "scf" for b in result.percent_blocks)
        assert any(b.name == "method" for b in result.percent_blocks)
        assert result.geometry is not None

    def test_parse_wavefunction_method_mp2(self, parser):
        """Test parsing MP2 wavefunction method."""
        content = "! MP2 cc-pVTZ\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any("MP2" in m for m in result.simple_input.methods)

    def test_parse_job_type_freq(self, parser):
        """Test parsing FREQ job type."""
        content = "! B3LYP def2-SVP FREQ\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert any("FREQ" in j for j in result.simple_input.job_types)

    def test_parse_case_insensitive_job_opt(self, parser):
        """Test case-insensitive job type parsing."""
        content = "! B3LYP def2-SVP opt\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.simple_input.job_types) >= 1
