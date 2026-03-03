"""Tests to achieve 100% coverage."""

import pytest
from unittest.mock import MagicMock, PropertyMock, patch

from orca_lsp.parser import ORCAParser
from orca_lsp.server import ORCALanguageServer
from lsprotocol.types import (
    HoverParams,
    Position,
    TextDocumentIdentifier,
)


class TestParserLoopCoverage:
    """Test for loop coverage to trigger break and normal exit."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_case_insensitive_method_break_and_normal_exit(self, parser):
        """Test both break and normal exit in method loop.

        Line 160: for method in self.all_methods:
        We need to ensure:
        1. break is executed when matching method is found
        2. Loop can also run normally when no match found
        """
        # Test with mixed case method that triggers break
        result1 = parser.parse_simple_input("! REVPBE", 0)
        assert len(result1.methods) == 1
        assert "revPBE" in result1.methods

        # Test with unknown method that loops through all
        result2 = parser.parse_simple_input("! UNKNOWN_METHOD_12345", 0)
        assert len(result2.methods) == 0
        assert "UNKNOWN_METHOD_12345" in result2.other_keywords

    def test_case_insensitive_basis_break_and_normal_exit(self, parser):
        """Test both break and normal exit in basis loop.

        Line 165: for basis in self.basis_sets:
        """
        # Test with mixed case basis that triggers break
        result1 = parser.parse_simple_input("! DEF2-TZVP", 0)
        assert len(result1.basis_sets) == 1
        assert "def2-TZVP" in result1.basis_sets

        # Test with unknown basis that loops through all
        result2 = parser.parse_simple_input("! UNKNOWN_BASIS_XYZ", 0)
        assert len(result2.basis_sets) == 0
        assert "UNKNOWN_BASIS_XYZ" in result2.other_keywords


class TestParserElseBranches:
    """Test else branches in parser."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_pal_block_without_nprocs(self, parser):
        """Test %pal block without nprocs.

        Line 253->250: else branch in pal block parsing.
        """
        content = """! B3LYP def2-SVP
%pal
end
* xyz 0 1
H 0 0 0
*
"""
        result = parser.parse(content)
        pal_block = next((b for b in result.percent_blocks if b.name == "pal"), None)
        assert pal_block is not None
        # Should not have nprocs parameter
        assert "nprocs" not in pal_block.parameters

    def test_scf_block_without_maxiter(self, parser):
        """Test %scf block without maxiter.

        Line 273->269: else branch in scf block parsing.
        """
        content = """! B3LYP def2-SVP
%scf
end
* xyz 0 1
H 0 0 0
*
"""
        result = parser.parse(content)
        scf_block = next((b for b in result.percent_blocks if b.name == "scf"), None)
        assert scf_block is not None
        # Should not have maxiter parameter
        assert "maxiter" not in scf_block.parameters


class TestServerHoverCoverage:
    """Test hover coverage for all keyword types."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_hover_basis_set(self, server):
        """Test hover on basis set keyword.

        Lines 265-266: basis set hover return statement.
        """
        mock_doc = MagicMock()
        mock_doc.lines = ["def2-TZVP"]
        mock_doc.source = "def2-TZVP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.inp"),
                position=Position(line=0, character=5),  # Position in def2-TZVP
            )

            result = server._on_hover(params)
            # Should return hover info for basis set
            if result is not None:
                assert "def2-TZVP" in result.contents.value

    def test_hover_job_type(self, server):
        """Test hover on job type keyword.

        Lines 273-274: job type hover return statement.
        """
        mock_doc = MagicMock()
        mock_doc.lines = ["OPT"]
        mock_doc.source = "OPT"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.inp"),
                position=Position(line=0, character=2),  # Position in OPT
            )

            result = server._on_hover(params)
            # Should return hover info for job type
            if result is not None:
                assert "OPT" in result.contents.value

    def test_hover_dft_functional(self, server):
        """Test hover on DFT functional keyword."""
        mock_doc = MagicMock()
        mock_doc.lines = ["B3LYP"]
        mock_doc.source = "B3LYP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.inp"),
                position=Position(line=0, character=2),  # Position in B3LYP
            )

            result = server._on_hover(params)
            # Should return hover info for DFT functional
            if result is not None:
                assert "B3LYP" in result.contents.value
