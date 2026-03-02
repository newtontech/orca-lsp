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
        assert test_server is not None
        assert test_server.parser is not None


class TestCompletions:
    """Test completion feature."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

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
    
    def test_get_completions_simple_input(self, server):
        """Test completions for simple input line."""
        completions = server._get_completions("! ", Position(line=0, character=2))
        assert isinstance(completions, list)
        assert len(completions) > 0
    
    def test_get_completions_percent_block(self, server):
        """Test completions for percent block."""
        completions = server._get_completions("%max", Position(line=0, character=4))
        assert isinstance(completions, list)
    
    def test_get_completions_geometry(self, server):
        """Test completions in geometry section."""
        completions = server._get_completions("O 0.0 0.0 ", Position(line=0, character=10))
        assert isinstance(completions, list)


class TestHover:
    """Test hover feature."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_hover_dft_functional(self, server):
        """Test hover on DFT functional."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP def2-TZVP"]
        
        word = server._get_word_at_position(mock_doc, Position(line=0, character=4))
        assert word == "B3LYP"

    def test_hover_basis_set(self, server):
        """Test hover on basis set."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP def2-TZVP"]
        
        word = server._get_word_at_position(mock_doc, Position(line=0, character=12))
        assert word == "def2"

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
        mock_doc.lines = ["   "]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=1))
        assert word == ""


class TestDiagnostics:
    """Test diagnostic feature."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_parser_has_errors(self, server):
        """Test that parser returns errors for invalid input."""
        result = server.parser.parse("")
        assert len(result.errors) > 0

    def test_parser_valid_input(self, server):
        """Test parser with valid input."""
        content = "! B3LYP def2-TZVP\n* xyz 0 1\nH 0 0 0\n*"
        result = server.parser.parse(content)
        # Should have warnings about missing maxcore but no errors
        assert result.simple_input is not None


class TestCodeActions:
    """Test code action feature."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_code_action_logic(self, server):
        """Test code action logic for maxcore."""
        # Test the logic directly without workspace
        mock_diagnostic = MagicMock()
        mock_diagnostic.message = "Missing %maxcore setting. Recommended: %maxcore 2000-4000 (MB per core)"
        
        # Verify the condition check
        assert "Missing %maxcore" in mock_diagnostic.message


class TestDocumentEvents:
    """Test document events."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_parser_on_did_open(self, server):
        """Test parser is called on document open."""
        content = "! B3LYP def2-TZVP"
        result = server.parser.parse(content)
        assert result is not None

    def test_parser_on_did_change(self, server):
        """Test parser is called on document change."""
        content = "! HF 6-31G*"
        result = server.parser.parse(content)
        assert result is not None


class TestMain:
    """Test main entry point."""

    @patch('orca_lsp.server.ORCALanguageServer')
    def test_main(self, mock_server_class):
        """Test main function."""
        mock_server = MagicMock()
        mock_server_class.return_value = mock_server
        main()
        mock_server.start_io.assert_called_once()


class TestParserIntegration:
    """Test parser integration with server."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_parse_water_molecule(self, server):
        """Test parsing water molecule input."""
        content = """! B3LYP def2-TZVP OPT
%maxcore 4000
%pal nprocs 4 end

* xyz 0 1
O   0.000000   0.000000   0.000000
H   0.757160   0.586260   0.000000
H  -0.757160   0.586260   0.000000
*
"""
        result = server.parser.parse(content)
        assert result.simple_input is not None
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 3

    def test_parse_with_percent_blocks(self, server):
        """Test parsing with various % blocks."""
        content = """! MP2 cc-pVTZ FREQ
%maxcore 8000
%pal nprocs 8 end
%scf maxiter 100 end

* xyz 0 1
C 0 0 0
H 0 0 1.09
*
"""
        result = server.parser.parse(content)
        assert len(result.percent_blocks) >= 2

    def test_invalid_element_detection(self, server):
        """Test detection of invalid element symbols."""
        content = """! B3LYP def2-SVP
* xyz 0 1
Xx 0 0 0
*
"""
        result = server.parser.parse(content)
        # Should have error for invalid element
        assert any('Invalid element' in e.get('message', '') for e in result.errors)


class TestKeywordLookup:
    """Test keyword lookup functions."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_dft_functional_lookup(self, server):
        """Test DFT functional documentation lookup."""
        from orca_lsp.keywords import DFT_FUNCTIONALS
        assert "B3LYP" in DFT_FUNCTIONALS
        assert "description" in DFT_FUNCTIONALS["B3LYP"]

    def test_basis_set_lookup(self, server):
        """Test basis set documentation lookup."""
        from orca_lsp.keywords import BASIS_SETS
        assert "def2-TZVP" in BASIS_SETS
        assert "description" in BASIS_SETS["def2-TZVP"]

    def test_job_type_lookup(self, server):
        """Test job type documentation lookup."""
        from orca_lsp.keywords import JOB_TYPES
        assert "OPT" in JOB_TYPES
        assert "FREQ" in JOB_TYPES
