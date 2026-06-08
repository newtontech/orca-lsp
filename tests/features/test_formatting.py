"""Tests for FormattingProvider."""

from __future__ import annotations

from typing import List

import pytest

from lsprotocol.types import (
    DocumentFormattingParams,
    DocumentRangeFormattingParams,
    FormattingOptions,
    Position,
    Range,
    TextDocumentIdentifier,
    TextEdit,
)
from orca_lsp.features.formatting import FormattingProvider, get_formatting_provider


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def provider() -> FormattingProvider:
    """Create a FormattingProvider without a server."""
    return FormattingProvider()


def _format_params(tab_size: int = 2, insert_spaces: bool = True) -> DocumentFormattingParams:
    """Build a DocumentFormattingParams with the given indent settings."""
    return DocumentFormattingParams(
        text_document=TextDocumentIdentifier(uri="file:///test.inp"),
        options=FormattingOptions(tab_size=tab_size, insert_spaces=insert_spaces),
    )


def _range_params(
    start_line: int,
    start_char: int,
    end_line: int,
    end_char: int,
    tab_size: int = 2,
    insert_spaces: bool = True,
) -> DocumentRangeFormattingParams:
    """Build a DocumentRangeFormattingParams."""
    return DocumentRangeFormattingParams(
        text_document=TextDocumentIdentifier(uri="file:///test.inp"),
        range=Range(
            start=Position(line=start_line, character=start_char),
            end=Position(line=end_line, character=end_char),
        ),
        options=FormattingOptions(tab_size=tab_size, insert_spaces=insert_spaces),
    )


def _apply_edits(text: str, edits: List[TextEdit]) -> str:
    """Apply TextEdits to text for verification (single-edit helpers)."""
    if not edits:
        return text
    edit = edits[0]
    lines = text.splitlines()
    start = edit.range.start
    end = edit.range.end

    before = "\n".join(lines[: start.line])
    after_lines = lines[end.line:]
    if end.character > 0 and after_lines:
        after_lines[0] = after_lines[0][end.character:]
    after = "\n".join(after_lines)

    if before and after:
        return before + "\n" + edit.new_text + after
    return before + edit.new_text + after


# ---------------------------------------------------------------------------
# Document formatting tests
# ---------------------------------------------------------------------------


class TestFormatDocument:
    """Tests for full-document formatting."""

    def test_already_formatted_returns_empty(self, provider: FormattingProvider) -> None:
        """A perfectly formatted document should produce no edits."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "  H 0.0 0.0 0.74\n"
            "*\n"
        )
        params = _format_params()
        edits = provider.format_document(text, params)
        assert edits == []

    def test_strips_trailing_whitespace(self, provider: FormattingProvider) -> None:
        """Trailing whitespace should be removed."""
        text = "! B3LYP def2-TZVP   \n%maxcore 4000  \n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        assert edits[0].new_text == "! B3LYP def2-TZVP\n%maxcore 4000\n"

    def test_indents_geometry_atoms(self, provider: FormattingProvider) -> None:
        """Atoms inside a geometry section should be indented."""
        text = "! B3LYP def2-TZVP\n* xyz 0 1\nH 0.0 0.0 0.0\nH 0.0 0.0 0.74\n*\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        formatted = edits[0].new_text
        assert "  H 0.0 0.0 0.0\n" in formatted
        assert "  H 0.0 0.0 0.74\n" in formatted

    def test_indents_percent_block_body(self, provider: FormattingProvider) -> None:
        """Body of multi-line % blocks should be indented."""
        text = "%scf\nmaxiter 100\nconvergence tight\nend\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        formatted = edits[0].new_text
        assert "  maxiter 100\n" in formatted
        assert "  convergence tight\n" in formatted
        # 'end' should be unindented
        assert "end\n" in formatted

    def test_single_line_block_no_indent(self, provider: FormattingProvider) -> None:
        """Single-line % blocks should not increase indent."""
        text = "%maxcore 4000\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        # Already formatted.
        assert edits == []

    def test_single_line_block_with_end(self, provider: FormattingProvider) -> None:
        """Single-line % block with inline 'end' should not add indentation."""
        text = "%pal nprocs 4 end\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert edits == []

    def test_single_line_quoted_value(self, provider: FormattingProvider) -> None:
        """Single-line % block with quoted value should not add indentation."""
        text = '%moinp "previous.gbw"\n'
        params = _format_params()
        edits = provider.format_document(text, params)
        assert edits == []

    def test_comment_preserved(self, provider: FormattingProvider) -> None:
        """Comments should be preserved and stripped of trailing whitespace."""
        text = "# This is a comment   \n! B3LYP def2-TZVP\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        assert edits[0].new_text.startswith("# This is a comment\n")

    def test_blank_lines_stripped_to_empty(self, provider: FormattingProvider) -> None:
        """Whitespace-only lines become empty lines."""
        text = "! B3LYP def2-TZVP\n   \n%maxcore 4000\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        # The whitespace-only line becomes a blank line.
        assert edits[0].new_text == "! B3LYP def2-TZVP\n\n%maxcore 4000\n"

    def test_blank_lines_preserved(self, provider: FormattingProvider) -> None:
        """Empty blank lines are kept as-is (already formatted)."""
        text = "! B3LYP def2-TZVP\n\n%maxcore 4000\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert edits == []

    def test_nested_geometry_and_block(self, provider: FormattingProvider) -> None:
        """Full file with geometry and % blocks formats correctly."""
        text = (
            "! B3LYP def2-TZVP OPT\n"
            "%scf\n"
            "maxiter 200\n"
            "end\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "O     0.0  0.0  0.0\n"
            "H     0.0  0.0  0.96\n"
            "H     0.0  0.96 0.0\n"
            "*\n"
        )
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        formatted = edits[0].new_text
        # %scf body indented
        assert "  maxiter 200\n" in formatted
        # geometry atoms indented
        assert "  O     0.0  0.0  0.0\n" in formatted

    def test_tab_indentation(self, provider: FormattingProvider) -> None:
        """When insert_spaces is False, tabs are used for indentation."""
        text = "* xyz 0 1\nH 0 0 0\n*\n"
        params = _format_params(tab_size=4, insert_spaces=False)
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        assert "\tH 0 0 0\n" in edits[0].new_text

    def test_custom_tab_size(self, provider: FormattingProvider) -> None:
        """Custom tab_size controls indentation width."""
        text = "* xyz 0 1\nH 0 0 0\n*\n"
        params = _format_params(tab_size=4)
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        assert "    H 0 0 0\n" in edits[0].new_text

    def test_idempotent(self, provider: FormattingProvider) -> None:
        """Formatting twice should produce the same output."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "  %scf\n"
            "  maxiter 100\n"
            "  end\n"
            "* xyz 0 1\n"
            "H 0 0 0\n"
            "*\n"
        )
        params = _format_params()

        # First format pass.
        edits1 = provider.format_document(text, params)
        assert len(edits1) == 1
        formatted_once = _apply_edits(text, edits1)

        # Second format pass on the already-formatted text.
        edits2 = provider.format_document(formatted_once, params)
        assert edits2 == [], "Formatting should be idempotent"

    def test_idempotent_complex(self, provider: FormattingProvider) -> None:
        """Complex file with multiple blocks is idempotent."""
        text = (
            "! B3LYP def2-TZVP OPT FREQ\n"
            "%scf\n"
            "maxiter 200\n"
            "convergence tight\n"
            "end\n"
            "%pal nprocs 4 end\n"
            "%maxcore 4000\n"
            "\n"
            "# Geometry\n"
            "* xyz 0 1\n"
            "  O  0.0  0.0  0.0\n"
            "  H  0.0  0.0  0.96\n"
            "  H  0.0  0.96  0.0\n"
            "*\n"
        )
        params = _format_params()

        edits1 = provider.format_document(text, params)
        formatted_once = _apply_edits(text, edits1)
        edits2 = provider.format_document(formatted_once, params)
        assert edits2 == []

    def test_empty_file(self, provider: FormattingProvider) -> None:
        """Empty file returns no edits."""
        params = _format_params()
        edits = provider.format_document("", params)
        assert edits == []

    def test_malformed_unclosed_block(self, provider: FormattingProvider) -> None:
        """Unclosed % block should still format body lines."""
        text = "%scf\nmaxiter 100\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        formatted = edits[0].new_text
        assert "  maxiter 100\n" in formatted

    def test_geometry_with_internal_coords(self, provider: FormattingProvider) -> None:
        """Geometry with * int format indents body correctly."""
        text = "* int 0 1\nC\n1 0.0 0.0 0.0\n*\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        formatted = edits[0].new_text
        assert "  C\n" in formatted
        assert "  1 0.0 0.0 0.0\n" in formatted

    def test_multiple_blocks(self, provider: FormattingProvider) -> None:
        """Multiple sequential % blocks each get proper indentation."""
        text = (
            "%scf\nmaxiter 100\nend\n"
            "%pal\nnprocs 4\nend\n"
        )
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        formatted = edits[0].new_text
        assert "  maxiter 100\n" in formatted
        assert "  nprocs 4\n" in formatted

    def test_block_after_geometry(self, provider: FormattingProvider) -> None:
        """A % block after a closed geometry section is not indented."""
        text = "* xyz 0 1\nH 0 0 0\n*\n%maxcore 4000\n"
        params = _format_params()
        edits = provider.format_document(text, params)
        assert len(edits) == 1
        formatted = edits[0].new_text
        assert "%maxcore 4000\n" in formatted
        # Make sure %maxcore is NOT indented.
        assert "  %maxcore" not in formatted


# ---------------------------------------------------------------------------
# Range formatting tests
# ---------------------------------------------------------------------------


class TestFormatRange:
    """Tests for range formatting."""

    def test_range_already_formatted(self, provider: FormattingProvider) -> None:
        """A well-formatted range should produce no edits."""
        text = "! B3LYP def2-TZVP\n%maxcore 4000\n"
        params = _range_params(0, 0, 2, 0)
        edits = provider.format_range(text, params)
        assert edits == []

    def test_range_format_geometry_atoms(self, provider: FormattingProvider) -> None:
        """Range formatting only changes lines within the requested range."""
        text = "! B3LYP def2-TZVP\n* xyz 0 1\nH 0.0 0.0 0.0\nH 0.0 0.0 0.74\n*\n"
        # Format only the atom lines (lines 2-3).
        params = _range_params(2, 0, 4, 0)
        edits = provider.format_range(text, params)
        assert len(edits) == 1
        edit = edits[0]
        assert edit.range.start.line == 2
        assert edit.range.end.line == 4
        assert "  H 0.0 0.0 0.0\n  H 0.0 0.0 0.74" == edit.new_text

    def test_range_format_block_body(self, provider: FormattingProvider) -> None:
        """Range formatting works for % block body lines."""
        text = "%scf\nmaxiter 100\nend\n"
        params = _range_params(1, 0, 2, 0)
        edits = provider.format_range(text, params)
        assert len(edits) == 1
        assert edits[0].new_text == "  maxiter 100"

    def test_range_beyond_file(self, provider: FormattingProvider) -> None:
        """Range extending beyond the file should be clamped."""
        text = "! B3LYP\n"
        params = _range_params(0, 0, 100, 0)
        edits = provider.format_range(text, params)
        # Already formatted, so no edits.
        assert edits == []

    def test_range_empty_file(self, provider: FormattingProvider) -> None:
        """Range formatting on empty file returns no edits."""
        params = _range_params(0, 0, 0, 0)
        edits = provider.format_range("", params)
        assert edits == []

    def test_range_strips_trailing_whitespace(self, provider: FormattingProvider) -> None:
        """Range formatting strips trailing whitespace in the range."""
        text = "! B3LYP   \n%maxcore 4000  \n"
        params = _range_params(0, 0, 2, 0)
        edits = provider.format_range(text, params)
        assert len(edits) == 1
        assert edits[0].new_text == "! B3LYP\n%maxcore 4000"

    def test_range_preserves_surrounding(self, provider: FormattingProvider) -> None:
        """Lines outside the range should not be included in the edit."""
        text = "! B3LYP def2-TZVP\n* xyz 0 1\nH 0 0 0\nH 0 0 0.74\n*\n"
        # Only format lines 2-3 (atom lines).
        params = _range_params(2, 0, 4, 0)
        edits = provider.format_range(text, params)
        assert len(edits) == 1
        edit = edits[0]
        # The edit should not include line 0 or 1 content.
        assert edit.new_text.startswith("  H")

    def test_range_single_line(self, provider: FormattingProvider) -> None:
        """Range formatting of a single line."""
        text = "! B3LYP def2-TZVP   \n"
        params = _range_params(0, 0, 1, 0)
        edits = provider.format_range(text, params)
        assert len(edits) == 1
        assert edits[0].new_text == "! B3LYP def2-TZVP"


# ---------------------------------------------------------------------------
# Provider factory
# ---------------------------------------------------------------------------


class TestGetFormattingProvider:
    """Tests for the module-level factory function."""

    def test_creates_provider(self) -> None:
        """Factory function should return a FormattingProvider."""
        provider = get_formatting_provider()
        assert isinstance(provider, FormattingProvider)

    def test_creates_provider_with_server(self) -> None:
        """Factory should accept a server argument."""
        provider = get_formatting_provider(server=None)
        assert isinstance(provider, FormattingProvider)


# ---------------------------------------------------------------------------
# Indentation helper tests
# ---------------------------------------------------------------------------


class TestIndentHelpers:
    """Tests for indent size and indent string helpers."""

    def test_default_indent_size(self, provider: FormattingProvider) -> None:
        """None options should yield default indent size of 2."""
        assert provider._indent_size(None) == 2

    def test_custom_indent_size(self, provider: FormattingProvider) -> None:
        """Custom tab_size should be respected."""
        opts = FormattingOptions(tab_size=4, insert_spaces=True)
        assert provider._indent_size(opts) == 4

    def test_zero_indent_size_defaults_to_2(self, provider: FormattingProvider) -> None:
        """A zero tab_size should fall back to 2."""
        opts = FormattingOptions(tab_size=0, insert_spaces=True)
        assert provider._indent_size(opts) == 2

    def test_indent_str_spaces(self, provider: FormattingProvider) -> None:
        """insert_spaces=True should produce space strings."""
        opts = FormattingOptions(tab_size=3, insert_spaces=True)
        assert provider._indent_str(opts, 3) == "   "

    def test_indent_str_tabs(self, provider: FormattingProvider) -> None:
        """insert_spaces=False should produce a tab character."""
        opts = FormattingOptions(tab_size=4, insert_spaces=False)
        assert provider._indent_str(opts, 4) == "\t"

    def test_indent_str_none_defaults_to_spaces(self, provider: FormattingProvider) -> None:
        """None options should default to spaces."""
        assert provider._indent_str(None, 2) == "  "


# ---------------------------------------------------------------------------
# Single-line block detection
# ---------------------------------------------------------------------------


class TestIsSingleLineBlock:
    """Tests for _is_single_line_block."""

    def test_numeric_value(self) -> None:
        assert FormattingProvider._is_single_line_block("%maxcore 4000") is True

    def test_quoted_value(self) -> None:
        assert FormattingProvider._is_single_line_block('%moinp "file.gbw"') is True

    def test_end_keyword(self) -> None:
        assert FormattingProvider._is_single_line_block("%pal nprocs 4 end") is True

    def test_multi_line_header(self) -> None:
        assert FormattingProvider._is_single_line_block("%scf") is False

    def test_multi_line_header_with_body_on_same_line(self) -> None:
        """A % header with a non-numeric word but no 'end' is multi-line."""
        assert FormattingProvider._is_single_line_block("%scf maxiter") is False
