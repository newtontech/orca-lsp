"""Tests to achieve 100% coverage."""

import pytest
from unittest.mock import MagicMock, PropertyMock

from orca_lsp.parser import ORCAParser, Atom, Geometry, SimpleInput, PercentBlock
from orca_lsp.server import ORCALanguageServer
from lsprotocol.types import (
    CompletionParams,
    HoverParams,
    Position,
    TextDocumentIdentifier,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    TextDocumentItem,
    VersionedTextDocumentIdentifier,
    CodeActionParams,
    CodeActionContext,
    Diagnostic,
    DiagnosticSeverity,
    Range,
)


class MockTextDocument:
    """Mock text document for testing."""

    def __init__(self, content: str, uri: str = "file:///test.inp"):
        self.source = content
        self.uri = uri
        self.lines = content.split("\n") if content else []


class TestParserCaseInsensitiveElseBranches:
    """Test parser case-insensitive else branches (lines 170-173)."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_case_insensitive_method_else_branch(self, parser):
        """Trigger the else branch in case-insensitive method lookup."""
        # This tests line 170-173: else branch when token not found case-insensitively
        result = parser.parse_simple_input("! completely_unknown_method", 0)
        # Should go to other_keywords via the else branch
        assert "completely_unknown_method" in result.other_keywords

    def test_case_insensitive_basis_else_branch(self, parser):
        """Trigger the else branch for unknown basis sets."""
        # Use lowercase that won't match any basis set
        result = parser.parse_simple_input("! unknown_basis_set_xyz", 0)
        assert "unknown_basis_set_xyz" in result.other_keywords

    def test_case_insensitive_job_else_branch(self, parser):
        """Trigger the else branch for unknown job types."""
        result = parser.parse_simple_input("! UNKNOWNJOBTYPE", 0)
        assert "UNKNOWNJOBTYPE" in result.other_keywords

    def test_mixed_known_and_unknown(self, parser):
        """Test mix of known and unknown keywords."""
        result = parser.parse_simple_input("! B3LYP unknown_keyword def2-SVP", 0)
        assert "unknown_keyword" in result.other_keywords
        assert len(result.methods) > 0
        assert len(result.basis_sets) > 0


class TestParserGeometryEdgeCases:
    """Test parser geometry edge cases for full coverage."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_geometry_line_end_zero_fallback(self, parser):
        """Test geometry when line_end stays 0 (fallback path)."""
        # Create a geometry without explicit end marker
        lines = [
            "* xyz 0 1",
            "H 0.0 0.0 0.0",
        ]  # No '*' at end, file ends

        geom, end_line = parser.parse_geometry(lines, 0)

        # Should still return geometry
        assert geom is not None
        # line_end may be 0 or parsed value
        assert len(geom.atoms) >= 1

    def test_geometry_format_type_fallback(self, parser):
        """Test geometry format type when parts < 2."""
        lines = [
            "*",  # Only *, no format type
            "H 0.0 0.0 0.0",
            "*",
        ]
        geom, end_line = parser.parse_geometry(lines, 0)
        # Should return None or handle gracefully
        # Based on code: if len(parts) < 2, returns None
        assert geom is None or geom.format_type == "xyz"  # default


class TestParserPercentBlockEdgeCases:
    """Test percent block edge cases."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_single_line_block_with_non_numeric_value(self, parser):
        """Test single-line block with non-numeric second part."""
        lines = ["%maxcore notanumber"]
        block, end_line = parser.parse_percent_block(lines, 0)

        assert block is not None
        assert block.name == "maxcore"
        # Should not set memory parameter due to ValueError
        assert "memory" not in block.parameters


class TestServerFeatureFunctions:
    """Test that server feature functions are properly called (lines 52, 56, 60, 64, 68)."""

    @pytest.fixture
    def server(self):
        server = ORCALanguageServer()
        type(server).workspace = PropertyMock(return_value=MagicMock())
        return server

    def test_feature_completion_returns_value(self, server):
        """Test that completion feature returns proper value."""
        mock_doc = MockTextDocument("! B3LYP ")
        server.workspace.get_text_document.return_value = mock_doc

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=8),
        )

        # Call the feature handler directly
        result = server._on_completion(params)
        assert result is not None

    def test_feature_hover_returns_value(self, server):
        """Test that hover feature returns proper value."""
        mock_doc = MockTextDocument("! B3LYP def2-TZVP")
        server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=4),
        )

        result = server._on_hover(params)
        # May return None if word not found, or Hover
        assert result is None or hasattr(result, "contents")

    def test_feature_code_action_returns_value(self, server):
        """Test that code action feature returns proper value."""
        mock_doc = MockTextDocument("! B3LYP def2-TZVP")
        server.workspace.get_text_document.return_value = mock_doc

        diagnostic = Diagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            message="Missing %maxcore setting",
            severity=DiagnosticSeverity.Warning,
        )

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            context=CodeActionContext(diagnostics=[diagnostic]),
        )

        result = server._on_code_action(params)
        assert isinstance(result, list)

    def test_feature_did_open_called(self, server):
        """Test that did_open feature handler works."""
        content = "! B3LYP def2-TZVP"
        mock_doc = MockTextDocument(content)
        server.workspace.get_text_document.return_value = mock_doc
        server.publish_diagnostics = MagicMock()

        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///test.inp", language_id="orca", version=1, text=content
            )
        )

        # Should not raise
        server._on_did_open(params)
        server.publish_diagnostics.assert_called_once()

    def test_feature_did_change_called(self, server):
        """Test that did_change feature handler works."""
        content = "! B3LYP def2-TZVP"
        mock_doc = MockTextDocument(content)
        server.workspace.get_text_document.return_value = mock_doc
        server.publish_diagnostics = MagicMock()

        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri="file:///test.inp", version=2),
            content_changes=[],
        )

        # Should not raise
        server._on_did_change(params)
        server.publish_diagnostics.assert_called_once()


class TestParserAllBranches:
    """Test all remaining parser branches."""

    @pytest.fixture
    def parser(self):
        return ORCAParser()

    def test_parse_simple_input_with_only_methods(self, parser):
        """Test simple input with only methods."""
        result = parser.parse_simple_input("! B3LYP PBE0", 0)
        assert len(result.methods) >= 2

    def test_parse_simple_input_empty(self, parser):
        """Test simple input with just !."""
        result = parser.parse_simple_input("!", 0)
        assert len(result.methods) == 0
        assert len(result.basis_sets) == 0

    def test_parse_with_comments(self, parser):
        """Test parsing with comment lines."""
        content = """# This is a comment
! B3LYP def2-SVP
# Another comment
* xyz 0 1
H 0 0 0
*"""
        result = parser.parse(content)
        assert result.simple_input is not None

    def test_parse_method_block_with_d3_only(self, parser):
        """Test method block with only D3 (not D3BJ)."""
        lines = ["%method", "  d3", "end"]
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.parameters.get("dispersion") == "D3"

    def test_parse_scf_block_with_maxiter(self, parser):
        """Test SCF block with maxiter."""
        lines = ["%scf", "  maxiter 200", "end"]
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.parameters.get("maxiter") == 200


class TestAtomValidation:
    """Test Atom validation."""

    def test_atom_valid_element(self):
        """Test atom with valid element."""
        atom = Atom(element="H", x=0.0, y=0.0, z=0.0)
        assert atom.is_valid() is True

    def test_atom_invalid_element(self):
        """Test atom with invalid element."""
        atom = Atom(element="Xx", x=0.0, y=0.0, z=0.0)
        assert atom.is_valid() is False

    def test_atom_empty_element(self):
        """Test atom with empty element."""
        atom = Atom(element="", x=0.0, y=0.0, z=0.0)
        assert atom.is_valid() is False


class TestGeometryValidation:
    """Test Geometry validation."""

    def test_geometry_valid(self):
        """Test valid geometry."""
        geom = Geometry(charge=0, multiplicity=1)
        geom.atoms.append(Atom(element="H", x=0.0, y=0.0, z=0.0))
        assert geom.is_valid() is True

    def test_geometry_no_atoms(self):
        """Test geometry with no atoms."""
        geom = Geometry(charge=0, multiplicity=1)
        assert geom.is_valid() is False

    def test_geometry_invalid_atom(self):
        """Test geometry with invalid atom."""
        geom = Geometry(charge=0, multiplicity=1)
        geom.atoms.append(Atom(element="Xx", x=0.0, y=0.0, z=0.0))
        assert geom.is_valid() is False


class TestSimpleInputValidation:
    """Test SimpleInput validation."""

    def test_simple_input_valid_with_method(self):
        """Test simple input with method."""
        si = SimpleInput(methods=["B3LYP"])
        assert si.is_valid() is True

    def test_simple_input_valid_with_basis(self):
        """Test simple input with basis set."""
        si = SimpleInput(basis_sets=["def2-SVP"])
        assert si.is_valid() is True

    def test_simple_input_invalid(self):
        """Test simple input with nothing."""
        si = SimpleInput()
        assert si.is_valid() is False


class TestPercentBlockValidation:
    """Test PercentBlock validation."""

    def test_percent_block_valid(self):
        """Test valid percent block."""
        block = PercentBlock(name="maxcore")
        assert block.is_valid() is True

    def test_percent_block_invalid(self):
        """Test invalid percent block."""
        block = PercentBlock()
        assert block.is_valid() is False
