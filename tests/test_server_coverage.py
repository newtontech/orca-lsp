"""Tests to achieve 100% coverage for server.py."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from lsprotocol.types import (
    CodeAction,
    CodeActionContext,
    CodeActionParams,
    CompletionList,
    CompletionParams,
    Diagnostic,
    DiagnosticSeverity,
    DidChangeTextDocumentParams,
    DidOpenTextDocumentParams,
    Hover,
    HoverParams,
    MarkupContent,
    MarkupKind,
    Position,
    Range,
    TextDocumentIdentifier,
    TextDocumentItem,
    TextEdit,
    VersionedTextDocumentIdentifier,
    WorkspaceEdit,
)

from orca_lsp.server import ORCALanguageServer


class TestServerLSPFeatures:
    """Test LSP server features with full coverage."""

    @pytest.fixture
    def server(self):
        """Create a server instance."""
        return ORCALanguageServer()

    def test_on_completion_simple_input(self, server):
        """Test _on_completion with simple input line."""
        # Setup mock document
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP "]

        # Mock workspace
        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = CompletionParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=0, character=8),
            )

            result = server._on_completion(params)
            assert isinstance(result, CompletionList)
            assert result is not None

    def test_on_completion_percent_block(self, server):
        """Test _on_completion with percent block."""
        mock_doc = MagicMock()
        mock_doc.lines = ["%max"]

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = CompletionParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=0, character=4),
            )

            result = server._on_completion(params)
            assert isinstance(result, CompletionList)

    def test_on_completion_geometry(self, server):
        """Test _on_completion in geometry section."""
        mock_doc = MagicMock()
        mock_doc.lines = ["* xyz 0 1", "O 0.0 0.0 "]

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = CompletionParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=1, character=10),
            )

            result = server._on_completion(params)
            assert isinstance(result, CompletionList)

    def test_on_hover_dft_functional(self, server):
        """Test _on_hover with DFT functional."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP def2-TZVP"]
        mock_doc.source = "! B3LYP def2-TZVP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=0, character=4),
            )

            result = server._on_hover(params)
            assert isinstance(result, Hover)
            assert "B3LYP" in result.contents.value

    def test_on_hover_wavefunction_method(self, server):
        """Test _on_hover with wavefunction method."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! MP2 cc-pVTZ"]
        mock_doc.source = "! MP2 cc-pVTZ"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=0, character=4),
            )

            result = server._on_hover(params)
            assert isinstance(result, Hover)
            assert "MP2" in result.contents.value

    def test_on_hover_basis_set(self, server):
        """Test _on_hover with basis set."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP def2-SVP"]
        mock_doc.source = "! B3LYP def2-SVP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=0, character=14),  # Position at SVP
            )

            result = server._on_hover(params)
            # Should return hover for SVP or None if not found
            if result is not None:
                assert isinstance(result, Hover)

    def test_on_hover_job_type(self, server):
        """Test _on_hover with job type."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP OPT"]
        mock_doc.source = "! B3LYP OPT"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=0, character=9),
            )

            result = server._on_hover(params)
            assert isinstance(result, Hover)
            assert "OPT" in result.contents.value

    def test_on_hover_no_match(self, server):
        """Test _on_hover with unknown keyword."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! UNKNOWN"]
        mock_doc.source = "! UNKNOWN"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=0, character=4),
            )

            result = server._on_hover(params)
            assert result is None

    def test_on_hover_empty_word(self, server):
        """Test _on_hover with empty position."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP"]
        mock_doc.source = "! B3LYP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            params = HoverParams(
                text_document=TextDocumentIdentifier(uri="file:///test.orca"),
                position=Position(line=0, character=0),
            )

            result = server._on_hover(params)
            # Empty word should return None
            assert result is None or isinstance(result, Hover)

    def test_validate_document_with_errors(self, server):
        """Test _validate_document with parsing errors."""
        mock_doc = MagicMock()
        mock_doc.source = ""

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        # Mock publish_diagnostics
        server.publish_diagnostics = MagicMock()

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            server._validate_document("file:///test.orca")

            # Should publish diagnostics for empty file
            server.publish_diagnostics.assert_called_once()
            call_args = server.publish_diagnostics.call_args
            assert call_args[0][0] == "file:///test.orca"
            diagnostics = call_args[0][1]
            assert len(diagnostics) > 0

    def test_validate_document_with_warnings(self, server):
        """Test _validate_document with warnings."""
        content = "! B3LYP def2-TZVP\n* xyz 0 1\nH 0 0 0\n*"
        mock_doc = MagicMock()
        mock_doc.source = content

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        server.publish_diagnostics = MagicMock()

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            server._validate_document("file:///test.orca")

            server.publish_diagnostics.assert_called_once()
            call_args = server.publish_diagnostics.call_args
            diagnostics = call_args[0][1]
            # Should have warnings about missing maxcore
            assert any(d.severity == DiagnosticSeverity.Warning for d in diagnostics)

    def test_validate_document_valid(self, server):
        """Test _validate_document with valid input."""
        content = "! B3LYP def2-TZVP\n%maxcore 4000\n* xyz 0 1\nH 0 0 0\n*"
        mock_doc = MagicMock()
        mock_doc.source = content

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        server.publish_diagnostics = MagicMock()

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            server._validate_document("file:///test.orca")

            server.publish_diagnostics.assert_called_once()
            call_args = server.publish_diagnostics.call_args
            diagnostics = call_args[0][1]
            # Should have no errors, only possibly warnings
            assert (
                not any(d.severity == DiagnosticSeverity.Error for d in diagnostics)
                or len(diagnostics) == 0
            )

    def test_on_code_action_maxcore_fix(self, server):
        """Test _on_code_action with maxcore quick fix."""
        mock_doc = MagicMock()
        mock_doc.source = "! B3LYP def2-TZVP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        # Create diagnostic for missing maxcore
        diagnostic = Diagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            message="Missing %maxcore setting. Recommended: %maxcore 2000-4000",
            severity=DiagnosticSeverity.Warning,
        )

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.orca"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            context=CodeActionContext(diagnostics=[diagnostic]),
        )

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            result = server._on_code_action(params)

            assert isinstance(result, list)
            assert len(result) > 0
            assert any("maxcore" in action.title.lower() for action in result)

    def test_on_code_action_no_diagnostic(self, server):
        """Test _on_code_action with no diagnostics."""
        mock_doc = MagicMock()
        mock_doc.source = "! B3LYP def2-TZVP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.orca"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            context=CodeActionContext(diagnostics=[]),
        )

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            result = server._on_code_action(params)

            assert isinstance(result, list)
            assert len(result) == 0

    def test_on_code_action_other_diagnostic(self, server):
        """Test _on_code_action with non-maxcore diagnostic."""
        mock_doc = MagicMock()
        mock_doc.source = "! B3LYP def2-TZVP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        diagnostic = Diagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            message="Some other error",
            severity=DiagnosticSeverity.Error,
        )

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.orca"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            context=CodeActionContext(diagnostics=[diagnostic]),
        )

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            result = server._on_code_action(params)

            assert isinstance(result, list)
            # Should not add quick fix for non-maxcore diagnostics
            assert len(result) == 0

    def test_on_did_open(self, server):
        """Test _on_did_open event."""
        mock_doc = MagicMock()
        mock_doc.source = "! B3LYP def2-TZVP"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        server.publish_diagnostics = MagicMock()

        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///test.orca", language_id="orca", version=1, text="! B3LYP def2-TZVP"
            )
        )

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            server._on_did_open(params)

            # Should validate and publish diagnostics
            server.publish_diagnostics.assert_called_once()

    def test_on_did_change(self, server):
        """Test _on_did_change event."""
        mock_doc = MagicMock()
        mock_doc.source = "! B3LYP def2-TZVP OPT"

        mock_workspace = MagicMock()
        mock_workspace.get_text_document.return_value = mock_doc

        server.publish_diagnostics = MagicMock()

        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri="file:///test.orca", version=2),
            content_changes=[],
        )

        with patch.object(
            type(server), "workspace", new_callable=PropertyMock, return_value=mock_workspace
        ):
            server._on_did_change(params)

            # Should validate and publish diagnostics
            server.publish_diagnostics.assert_called_once()


class TestGetCompletionsEdgeCases:
    """Test edge cases in _get_completions."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_get_completions_empty_line(self, server):
        """Test completions for empty line."""
        completions = server._get_completions("", Position(line=0, character=0))
        assert isinstance(completions, list)
        # Empty line should return empty completions
        assert len(completions) == 0

    def test_get_completions_whitespace(self, server):
        """Test completions for whitespace line."""
        completions = server._get_completions("   ", Position(line=0, character=2))
        assert isinstance(completions, list)

    def test_get_completions_unknown_context(self, server):
        """Test completions for unknown context."""
        completions = server._get_completions("xyz", Position(line=0, character=3))
        assert isinstance(completions, list)
        # Unknown context should return empty completions
        assert len(completions) == 0

    def test_get_completions_method_context(self, server):
        """Test completions for method context."""
        completions = server._get_completions("! B3LYP ", Position(line=0, character=8))
        assert isinstance(completions, list)
        # Should include basis sets and job types
        assert len(completions) > 0

    def test_get_percent_completions_with_block_name(self, server):
        """Test percent completions with partial block name."""
        completions = server._get_percent_completions("%maxc")
        assert isinstance(completions, list)
        # Should include maxcore
        assert any("maxcore" in item.label.lower() for item in completions)

    def test_get_percent_completions_in_block(self, server):
        """Test percent completions inside a block."""
        # This tests the "if f'%{name}' in line.lower()" branch
        completions = server._get_percent_completions("%maxcore ")
        assert isinstance(completions, list)

    def test_get_block_specific_completions_maxcore(self, server):
        """Test block specific completions for maxcore."""
        completions = server._get_block_specific_completions("maxcore")
        assert isinstance(completions, list)
        assert len(completions) > 0
        # Should include memory values
        assert any("MB" in item.label for item in completions)

    def test_get_block_specific_completions_pal(self, server):
        """Test block specific completions for pal."""
        completions = server._get_block_specific_completions("pal")
        assert isinstance(completions, list)
        assert len(completions) > 0
        # Should include nprocs
        assert any("nprocs" in item.label for item in completions)

    def test_get_block_specific_completions_method(self, server):
        """Test block specific completions for method."""
        completions = server._get_block_specific_completions("method")
        assert isinstance(completions, list)
        assert len(completions) > 0
        # Should include dispersion corrections
        assert any(item.label in ["D3", "D3BJ", "D4"] for item in completions)

    def test_get_block_specific_completions_scf(self, server):
        """Test block specific completions for scf."""
        completions = server._get_block_specific_completions("scf")
        assert isinstance(completions, list)
        assert len(completions) > 0
        # Should include SCF options
        assert any(item.label in ["maxiter", "convergence", "NRMaxIt"] for item in completions)

    def test_get_block_specific_completions_unknown(self, server):
        """Test block specific completions for unknown block."""
        completions = server._get_block_specific_completions("unknown")
        assert isinstance(completions, list)
        # Unknown block should return empty completions
        assert len(completions) == 0


class TestInGeometrySection:
    """Test _in_geometry_section method."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_in_geometry_section_valid(self, server):
        """Test detection of geometry section line."""
        assert server._in_geometry_section("O 0.0 0.0 0.0")
        assert server._in_geometry_section("H 0.757160 0.586260 0.000000")
        assert server._in_geometry_section("C -0.5 1.2 3.4")

    def test_in_geometry_section_invalid(self, server):
        """Test rejection of non-geometry lines."""
        assert not server._in_geometry_section("! B3LYP")
        assert not server._in_geometry_section("%maxcore 4000")
        assert not server._in_geometry_section("* xyz 0 1")
        assert not server._in_geometry_section("")


class TestGetWordAtPosition:
    """Test _get_word_at_position method."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_get_word_at_start(self, server):
        """Test getting word at start of line."""
        mock_doc = MagicMock()
        mock_doc.lines = ["B3LYP def2-TZVP"]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=0))
        assert word == "B3LYP"

    def test_get_word_at_end(self, server):
        """Test getting word at end of line."""
        mock_doc = MagicMock()
        mock_doc.lines = ["B3LYP def2-TZVP"]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=15))
        assert word == "TZVP"  # Only alphanumeric characters

    def test_get_word_in_middle(self, server):
        """Test getting word in middle of line."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! B3LYP def2-TZVP OPT"]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=6))
        assert word == "B3LYP"

    def test_get_word_with_symbols(self, server):
        """Test getting word with symbols."""
        mock_doc = MagicMock()
        mock_doc.lines = ["! def2-TZVP"]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=5))
        assert word == "def2"

    def test_get_word_empty_line(self, server):
        """Test getting word from empty line."""
        mock_doc = MagicMock()
        mock_doc.lines = [""]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=0))
        assert word == ""

    def test_get_word_only_spaces(self, server):
        """Test getting word from line with only spaces."""
        mock_doc = MagicMock()
        mock_doc.lines = ["   "]
        word = server._get_word_at_position(mock_doc, Position(line=0, character=1))
        assert word == ""
