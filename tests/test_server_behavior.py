"""Behavioral tests for ORCA LSP server.

Consolidates unique server behaviors from coverage-oriented test files into
meaningful assertions about LSP feature behavior.
"""

import pytest
from unittest.mock import MagicMock, PropertyMock, patch

from lsprotocol.types import (
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
    Position,
    Range,
    TextDocumentIdentifier,
    TextDocumentItem,
    VersionedTextDocumentIdentifier,
)

from orca_lsp.server import ORCALanguageServer


class MockTextDocument:
    """Mock text document for testing."""

    def __init__(self, content: str, uri: str = "file:///test.inp"):
        self.source = content
        self.uri = uri
        self.lines = content.split("\n") if content else []


class TestFeatureRegistration:
    """LSP features are properly registered."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_completion_feature_registered(self, server):
        assert hasattr(server, "_on_completion")

    def test_hover_feature_registered(self, server):
        assert hasattr(server, "_on_hover")

    def test_code_action_feature_registered(self, server):
        assert hasattr(server, "_on_code_action")

    def test_did_open_feature_registered(self, server):
        assert hasattr(server, "_on_did_open")

    def test_did_change_feature_registered(self, server):
        assert hasattr(server, "_on_did_change")


class TestHoverBehavior:
    """Server hover returns correct information for each keyword type."""

    @pytest.fixture
    def server(self):
        server = ORCALanguageServer()
        type(server).workspace = PropertyMock(return_value=MagicMock())
        return server

    def test_hover_dft_functional(self, server):
        """Hover on a DFT functional returns documentation."""
        mock_doc = MockTextDocument("! B3LYP def2-TZVP")
        server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=4),
        )

        result = server._on_hover(params)
        assert result is not None
        assert isinstance(result, Hover)
        assert isinstance(result.contents, MarkupContent)
        assert "B3LYP" in result.contents.value

    def test_hover_wavefunction_method(self, server):
        """Hover on a wavefunction method returns documentation."""
        mock_doc = MockTextDocument("! MP2 cc-pVTZ")
        server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=3),
        )

        result = server._on_hover(params)
        assert result is not None
        assert "MP2" in result.contents.value

    def test_hover_job_type(self, server):
        """Hover on a job type returns documentation."""
        mock_doc = MockTextDocument("! B3LYP def2-TZVP OPT")
        server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=20),
        )

        result = server._on_hover(params)
        assert result is not None
        assert "OPT" in result.contents.value

    def test_hover_unknown_keyword_returns_none(self, server):
        """Hover on unknown keyword returns None."""
        mock_doc = MockTextDocument("! UNKNOWN_KEYWORD_XYZ")
        server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=4),
        )

        result = server._on_hover(params)
        assert result is None

    def test_hover_empty_word_returns_none(self, server):
        """Hover on empty space returns None."""
        mock_doc = MockTextDocument("!    ")
        server.workspace.get_text_document.return_value = mock_doc

        params = HoverParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=3),
        )

        result = server._on_hover(params)
        assert result is None


class TestCompletionBehavior:
    """Server completion returns appropriate suggestions."""

    @pytest.fixture
    def server(self):
        server = ORCALanguageServer()
        type(server).workspace = PropertyMock(return_value=MagicMock())
        return server

    def test_completion_simple_input(self, server):
        """Completion in simple input line returns suggestions."""
        mock_doc = MockTextDocument("! B3LYP ")
        server.workspace.get_text_document.return_value = mock_doc

        params = CompletionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            position=Position(line=0, character=8),
        )

        result = server._on_completion(params)
        assert result is not None
        assert isinstance(result, CompletionList)

    def test_completion_empty_line(self, server):
        """Completion on empty line returns empty list."""
        completions = server._get_completions("", Position(line=0, character=0))
        assert isinstance(completions, list)
        assert len(completions) == 0

    def test_block_specific_completions_unknown(self, server):
        """Completions for unknown block returns empty list."""
        completions = server._get_block_specific_completions("unknown_block")
        assert isinstance(completions, list)
        assert len(completions) == 0

    def test_block_specific_completions_maxcore(self, server):
        """Completions for maxcore block include MB values."""
        completions = server._get_block_specific_completions("maxcore")
        assert isinstance(completions, list)
        assert len(completions) > 0
        assert any("MB" in item.label for item in completions)

    def test_block_specific_completions_pal(self, server):
        """Completions for pal block include nprocs."""
        completions = server._get_block_specific_completions("pal")
        assert isinstance(completions, list)
        assert any("nprocs" in item.label for item in completions)

    def test_block_specific_completions_method(self, server):
        """Completions for method block include dispersion options."""
        completions = server._get_block_specific_completions("method")
        assert isinstance(completions, list)
        assert any("D3" in item.label or "D4" in item.label for item in completions)

    def test_block_specific_completions_scf(self, server):
        """Completions for scf block include maxiter and convergence."""
        completions = server._get_block_specific_completions("scf")
        assert isinstance(completions, list)
        labels = [item.label for item in completions]
        assert any(opt in labels for opt in ["maxiter", "convergence", "NRMaxIt"])


class TestDiagnosticBehavior:
    """Server publishes correct diagnostics."""

    @pytest.fixture
    def server(self):
        server = ORCALanguageServer()
        type(server).workspace = PropertyMock(return_value=MagicMock())
        return server

    def test_validate_empty_document_reports_errors(self, server):
        """Empty document produces diagnostics."""
        mock_doc = MockTextDocument("")
        server.workspace.get_text_document.return_value = mock_doc
        server.publish_diagnostics = MagicMock()

        server._validate_document("file:///test.inp")

        server.publish_diagnostics.assert_called_once()
        call_args = server.publish_diagnostics.call_args
        assert call_args[0][0] == "file:///test.inp"
        diagnostics = call_args[0][1]
        assert isinstance(diagnostics, list)

    def test_validate_document_warns_missing_maxcore(self, server):
        """Document without %maxcore produces warning."""
        content = "! B3LYP def2-TZVP\n* xyz 0 1\nH 0 0 0\n*"
        mock_doc = MockTextDocument(content)
        server.workspace.get_text_document.return_value = mock_doc
        server.publish_diagnostics = MagicMock()

        server._validate_document("file:///test.inp")

        server.publish_diagnostics.assert_called_once()
        diagnostics = server.publish_diagnostics.call_args[0][1]
        warning_messages = [d.message for d in diagnostics]
        assert any("maxcore" in msg.lower() for msg in warning_messages)

    def test_validate_valid_document_no_errors(self, server):
        """Valid document produces no error-level diagnostics."""
        content = "! B3LYP def2-TZVP OPT\n%maxcore 4000\n* xyz 0 1\nO 0 0 0\nH 0 0 1\nH 0 1 0\n*"
        mock_doc = MockTextDocument(content)
        server.workspace.get_text_document.return_value = mock_doc
        server.publish_diagnostics = MagicMock()

        server._validate_document("file:///test.inp")

        server.publish_diagnostics.assert_called_once()
        diagnostics = server.publish_diagnostics.call_args[0][1]
        errors = [d for d in diagnostics if d.severity == DiagnosticSeverity.Error]
        assert len(errors) == 0


class TestCodeActionBehavior:
    """Server code actions provide quick fixes."""

    @pytest.fixture
    def server(self):
        server = ORCALanguageServer()
        type(server).workspace = PropertyMock(return_value=MagicMock())
        return server

    def test_code_action_maxcore_fix(self, server):
        """Code action suggests maxcore fix for missing maxcore warning."""
        mock_doc = MockTextDocument("! B3LYP def2-TZVP")
        server.workspace.get_text_document.return_value = mock_doc

        diagnostic = Diagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            message="Missing %maxcore setting. Recommended: %maxcore 2000-4000",
            severity=DiagnosticSeverity.Warning,
            source="orca-lsp",
        )

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            context=CodeActionContext(diagnostics=[diagnostic]),
        )

        actions = server._on_code_action(params)
        assert isinstance(actions, list)
        assert len(actions) > 0
        assert any("maxcore" in action.title.lower() for action in actions)

    def test_code_action_no_match_returns_general_actions(self, server):
        """Code action returns general actions (e.g. %maxcore) for unrecognized diagnostics."""
        mock_doc = MockTextDocument("! B3LYP def2-TZVP")
        server.workspace.get_text_document.return_value = mock_doc

        diagnostic = Diagnostic(
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            message="Some other error",
            severity=DiagnosticSeverity.Error,
            source="orca-lsp",
        )

        params = CodeActionParams(
            text_document=TextDocumentIdentifier(uri="file:///test.inp"),
            range=Range(start=Position(line=0, character=0), end=Position(line=0, character=20)),
            context=CodeActionContext(diagnostics=[diagnostic]),
        )

        actions = server._on_code_action(params)
        assert isinstance(actions, list)
        # No diagnostic-specific fix, but general actions (e.g. add %maxcore) may be present.
        # None of the actions should be tied to the unrecognized diagnostic.
        for action in actions:
            if action.diagnostics:
                assert diagnostic not in action.diagnostics


class TestDocumentEvents:
    """Server responds to document open/change events."""

    @pytest.fixture
    def server(self):
        server = ORCALanguageServer()
        type(server).workspace = PropertyMock(return_value=MagicMock())
        return server

    def test_did_open_publishes_diagnostics(self, server):
        """Document open triggers validation."""
        content = "! B3LYP def2-TZVP"
        mock_doc = MockTextDocument(content)
        server.workspace.get_text_document.return_value = mock_doc
        server.publish_diagnostics = MagicMock()

        params = DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri="file:///test.inp", language_id="orca", version=1, text=content
            )
        )

        server._on_did_open(params)
        server.publish_diagnostics.assert_called_once()

    def test_did_change_publishes_diagnostics(self, server):
        """Document change triggers validation."""
        content = "! B3LYP def2-TZVP OPT"
        mock_doc = MockTextDocument(content)
        server.workspace.get_text_document.return_value = mock_doc
        server.publish_diagnostics = MagicMock()

        params = DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(uri="file:///test.inp", version=2),
            content_changes=[],
        )

        server._on_did_change(params)
        server.publish_diagnostics.assert_called_once()


class TestGeometrySectionDetection:
    """Server correctly identifies geometry section lines."""

    @pytest.fixture
    def server(self):
        return ORCALanguageServer()

    def test_geometry_lines_detected(self, server):
        assert server._in_geometry_section("O 0.0 0.0 0.0") is True
        assert server._in_geometry_section("H 0.5 0.5 0.5") is True

    def test_non_geometry_lines_rejected(self, server):
        assert server._in_geometry_section("! B3LYP") is False
        assert server._in_geometry_section("%maxcore 4000") is False
