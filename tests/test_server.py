"""Tests for ORCA LSP server."""
import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from lsprotocol.types import (
    CompletionParams,
    CompletionItem,
    CompletionItemKind,
    CompletionList,
    HoverParams,
    Hover,
    MarkupContent,
    MarkupKind,
    Position,
    DidOpenTextDocumentParams,
    DidChangeTextDocumentParams,
    TextDocumentItem,
    TextDocumentIdentifier,
    VersionedTextDocumentIdentifier,
    Diagnostic,
    DiagnosticSeverity,
    Range,
    CodeActionParams,
)

from orca_lsp.server import ORCALanguageServer, main


class TestORCALanguageServer:
    """Test ORCA Language Server."""

    def test_server_initialization(self):
        """Test server initialization."""
        test_server = ORCALanguageServer()
        assert test_server.name == "orca-lsp"
        assert test_server.version == "0.1.0"
        assert test_server.parser is not None

    @patch('orca_lsp.server.ORCALanguageServer._setup_features')
    def test_setup_features_called(self, mock_setup):
        """Test that setup_features is called during init."""
        ORCALanguageServer()
        mock_setup.assert_called_once()


class TestCompletions:
    """Test completion feature."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    @patch.object(ORCALanguageServer, 'workspace')
    def test_completion_with_document(self, mock_workspace, server):
        """Test completion with document."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! "]
        mock_workspace.get_text_document.return_value = mock_doc
        
        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=2),
        )
        result = server._on_completion(params)
        assert isinstance(result, CompletionList)

    @patch.object(ORCALanguageServer, 'workspace')
    def test_completion_percent_block(self, mock_workspace, server):
        """Test completion for percent blocks."""
        mock_doc = MagicMock()
        mock_doc.lines = ["%max"]
        mock_workspace.get_text_document.return_value = mock_doc
        
        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=4),
        )
        result = server._on_completion(params)
        assert isinstance(result, CompletionList)

    def test_get_percent_completions(self, server):
        """Test percent block completions."""
        completions = server._get_percent_completions("% max")
        assert isinstance(completions, list)

    def test_get_method_completions(self, server):
        """Test method completions."""
        completions = server._get_method_completions()
        assert isinstance(completions, list)
        assert len(completions) > 0

    def test_get_basis_completions(self, server):
        """Test basis set completions."""
        completions = server._get_basis_completions()
        assert isinstance(completions, list)
        assert len(completions) > 0

    def test_get_job_completions(self, server):
        """Test job type completions."""
        completions = server._get_job_completions()
        assert isinstance(completions, list)
        assert len(completions) > 0

    def test_get_element_completions(self, server):
        """Test element completions."""
        completions = server._get_element_completions()
        assert isinstance(completions, list)
        assert len(completions) > 0


class TestHover:
    """Test hover feature."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    @patch.object(ORCALanguageServer, 'workspace')
    def test_hover_with_word(self, mock_workspace, server):
        """Test hover with valid word."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP"]
        mock_workspace.get_text_document.return_value = mock_doc
        
        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=4),
        )
        result = server._on_hover(params)
        assert result is None or isinstance(result, Hover)

    @patch.object(ORCALanguageServer, 'workspace')
    def test_hover_no_word(self, mock_workspace, server):
        """Test hover with no word at position."""
        mock_doc = MagicMock()
        mock_doc.lines = ["!   "
        mock_workspace.get_text_document.return_value = mock_doc
        
        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=2),
        )
        result = server._on_hover(params)
        assert result is None

    def test_get_word_at_position(self, server):
        """Test getting word at position."""
        mock_doc = MagicMock()
        mock_doc.lines = ["hello world"]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=0))
        assert word == "hello"

    def test_get_word_at_position_middle(self, server):
        """Test getting word at middle position."""
        mock_doc = MagicMock()
        mock_doc.lines = ["hello world"]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=6))
        assert word == "world"

    def test_get_word_at_position_empty(self, server):
        """Test getting word at empty position."""
        mock_doc = MagicMock()
        mock_doc.lines = ["   "
        word = server._get_word_at_position(mock_doc, Position(line=0, character=1))
        assert word == ""


class TestDiagnostics:
    """Test diagnostic feature."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_diagnostic_handler(self, server):
        """Test diagnostic handler."""
        result = server._on_diagnostic(MagicMock())
        assert result == []

    @patch.object(ORCALanguageServer, 'publish_diagnostics')
    @patch.object(ORCALanguageServer, 'workspace')
    def test_validate_document(self, mock_workspace, mock_publish, server):
        """Test document validation."""
        mock_doc = MagicMock()
        mock_doc.source = "test"
        mock_workspace.get_text_document.return_value = mock_doc
        
        mock_result = MagicMock()
        mock_result.errors = []
        mock_result.warnings = []
        server.parser.parse.return_value = mock_result
        
        server._validate_document("file:///test.inp")


class TestCodeActions:
    """Test code action feature."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_code_action_with_maxcore(self, server):
        """Test code action for maxcore warning."""
        mock_diagnostic = MagicMock()
        mock_diagnostic.message = "Missing %maxcore"
        
        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=10),
            ),
            context=MagicMock(diagnostics=[mock_diagnostic]),
        )
        actions = server._on_code_action(params)
        assert isinstance(actions, list)

    def test_code_action_empty(self, server):
        """Test code action with no diagnostics."""
        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(
                start=Position(line=0, character=0),
                end=Position(line=0, character=10),
            ),
            context=MagicMock(diagnostics=[]),
        )
        actions = server._on_code_action(params)
        assert actions == []


class TestDocumentEvents:
    """Test document events."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    @patch.object(ORCALanguageServer, '_validate_document')
    def test_did_open(self, mock_validate, server):
        """Test document open event."""
        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///test.inp",
                language_id="orca",
                version=1,
                text="test",
            )
        )
        server._on_did_open(params)
        mock_validate.assert_called_once_with("file:///test.inp")

    @patch.object(ORCALanguageServer, '_validate_document')
    def test_did_change(self, mock_validate, server):
        """Test document change event."""
        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(
                uri="file:///test.inp",
                version=2,
            ),
            content_changes=[MagicMock(text="new")],
        )
        server._on_did_change(params)
        mock_validate.assert_called_once_with("file:///test.inp")


class TestMain:
    """Test main entry point."""

    @patch('orca_lsp.server.ORCALanguageServer')
    def test_main(self, mock_server_class):
        """Test main function."""
        mock_server = MagicMock()
        mock_server_class.return_value = mock_server
        main()
        mock_server.start_io.assert_called_once()
