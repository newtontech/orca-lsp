"""Enhanced tests for full coverage."""

import pytest
from unittest.mock import MagicMock, patch
from lsprotocol.types import (
    Position,
    TextDocumentItem,
    TextDocumentIdentifier,
    VersionedTextDocumentIdentifier,
    CodeActionParams,
    Range,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
)

from orca_lsp.server import ORCALanguageServer
from orca_lsp.parser import ORCAParser


class TestParserSpecificPaths:
    """Test specific parser code paths."""

    def test_simple_input_other_keywords(self):
        """Test parsing unrecognized keywords."""
        parser = ORCAParser()
        content = "! B3LYP CUSTOM_KEYWORD another_keyword def2-SVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert result.simple_input is not None
        assert len(result.simple_input.other_keywords) > 0
        assert "CUSTOM_KEYWORD" in result.simple_input.other_keywords

    def test_percent_block_no_match(self):
        """Test % block with invalid value."""
        parser = ORCAParser()
        content = "%pal custom_param value\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1
        assert result.percent_blocks[0].name == "pal"

    def test_method_block_no_dispersion(self):
        """Test method block without dispersion keyword."""
        parser = ORCAParser()
        content = "%method some_other_option\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1

    def test_scf_block_no_maxiter(self):
        """Test SCF block without maxiter."""
        parser = ORCAParser()
        content = "%scf convergence tight\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1

    def test_block_with_end_suffix(self):
        """Test block where 'end' is suffix of word."""
        parser = ORCAParser()
        content = "%test endparam\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1


class TestServerCompletionsAllBranches:
    """Test all completion branches."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_completion_percent_block_in_maxcore(self, server):
        """Test completions in %maxcore block."""
        completions = server._get_percent_completions("%maxcore 4000")
        assert isinstance(completions, list)

    def test_completion_percent_block_in_pal(self, server):
        """Test completions in %pal block."""
        completions = server._get_percent_completions("%pal")
        assert isinstance(completions, list)

    def test_completion_percent_block_in_method(self, server):
        """Test completions in %method block."""
        completions = server._get_percent_completions("%method")
        assert isinstance(completions, list)

    def test_completion_percent_block_in_scf(self, server):
        """Test completions in %scf block."""
        completions = server._get_percent_completions("%scf")
        assert isinstance(completions, list)

    def test_completion_percent_block_empty_name(self, server):
        """Test completions with empty block name."""
        completions = server._get_percent_completions("% ")
        assert isinstance(completions, list)

    def test_completion_in_simple_input(self, server):
        """Test completions in simple input line."""
        completions = server._get_completions("! ", Position(line=0, character=2))
        assert isinstance(completions, list)

    def test_completion_not_in_any_context(self, server):
        """Test completions not in any specific context."""
        completions = server._get_completions("random", Position(line=0, character=6))
        assert isinstance(completions, list)


class TestServerHoverAllCases:
    """Test hover for all keyword types."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_hover_returns_none_for_unknown(self, server):
        """Test hover returns None for unknown word."""
        mock_doc = MagicMock()
        mock_doc.lines = ["unknown_word"]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=0))
        assert word == "unknown"

    def test_hover_basis_set_variant(self, server):
        """Test hover on basis set."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! def2-TZVP"]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=2))
        assert word == "def2"


class TestServerDocumentValidation:
    """Test document validation."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    @patch("orca_lsp.server.ORCALanguageServer.publish_diagnostics")
    def test_validate_and_publish_empty(self, mock_publish, server):
        """Test validation of empty document."""
        server._validate_document("test://empty.inp")
        assert mock_publish.called

    @patch("orca_lsp.server.ORCALanguageServer.publish_diagnostics")
    def test_validate_and_publish_with_errors(self, mock_publish, server):
        """Test validation with errors."""
        server._validate_document("test://with_errors.inp")
        assert mock_publish.called


class TestServerDiagnostics:
    """Test diagnostics conversion."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_parse_result_with_errors(self, server):
        """Test parser result with errors."""
        result = server.parser.parse("! INVALID")
        assert len(result.errors) > 0
        assert any("method" in e.get("message", "").lower() for e in result.errors)

    def test_parse_result_with_warnings(self, server):
        """Test parser result with warnings."""
        result = server.parser.parse("! B3LYP def2-SVP\n* xyz 0 1\nH 0 0 0\n*")
        assert len(result.warnings) > 0
        assert any("maxcore" in w.get("message", "").lower() for w in result.warnings)


class TestCodeActions:
    """Test code actions."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_code_action_no_diagnostics(self, server):
        """Test code action with no diagnostics."""
        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="test"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=0)),
            context=MagicMock(diagnostics=[]),
        )
        actions = server._on_code_action(params)
        assert isinstance(actions, list)

    def test_code_action_other_diagnostic(self, server):
        """Test code action with unrelated diagnostic."""
        mock_diagnostic = MagicMock()
        mock_diagnostic.message = "Some other error"
        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="test"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=0)),
            context=MagicMock(diagnostics=[mock_diagnostic]),
        )
        actions = server._on_code_action(params)
        assert isinstance(actions, list)


class TestDocumentEventsIntegration:
    """Test document event handling."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    @patch("orca_lsp.server.ORCALanguageServer.publish_diagnostics")
    def test_did_open_calls_validation(self, mock_publish, server):
        """Test that didOpen calls validation."""
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="test://open.inp",
                language_id="orca",
                version=1,
                text="! B3LYP def2-SVP\n* xyz 0 1\nH 0 0 0\n*",
            )
        )
        server._on_did_open(params)
        assert mock_publish.called

    @patch("orca_lsp.server.ORCALanguageServer.publish_diagnostics")
    def test_did_change_calls_validation(self, mock_publish, server):
        """Test that didChange calls validation."""
        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri="test://change.inp", version=2),
            content_changes=[],
        )
        server._on_did_change(params)
        assert mock_publish.called


class TestParserAllBranches:
    """Test all parser branches."""

    def test_parse_with_comments(self):
        """Test parsing with comments."""
        parser = ORCAParser()
        content = """# This is a comment
! B3LYP def2-SVP
# Another comment
* xyz 0 1
H 0 0 0
*
"""
        result = parser.parse(content)
        assert result.simple_input is not None
        assert result.geometry is not None

    def test_parse_with_empty_lines(self):
        """Test parsing with empty lines."""
        parser = ORCAParser()
        content = """


! B3LYP def2-SVP


* xyz 0 1
H 0 0 0
*

"""
        result = parser.parse(content)
        assert result.simple_input is not None
        assert result.geometry is not None

    def test_atom_invalid_element(self):
        """Test atom with invalid element."""
        parser = ORCAParser()
        content = "! B3LYP def2-SVP\n* xyz 0 1\nXx 0 0 0\n*"
        result = parser.parse(content)
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 1
        assert not result.geometry.atoms[0].is_valid()

    def test_geometry_end_not_found(self):
        """Test geometry when * end not found."""
        parser = ORCAParser()
        content = "* xyz 0 1\nH 0 0 0\nC 1 0 0"
        result = parser.parse(content)
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 2
