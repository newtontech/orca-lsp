"""Tests for the RenameProvider.

Each test exercises prepare_rename, get_rename_edits, and edge cases
for renaming ORCA symbols.
"""

from __future__ import annotations

from typing import Dict, List, Optional

import pytest
from lsprotocol.types import Position, Range, TextEdit, WorkspaceEdit

from orca_lsp.features.rename import RenameProvider

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _apply_edit(source: str, edit: TextEdit) -> str:
    """Apply a single TextEdit to source and return the result."""
    lines = source.split("\n")
    line_offsets: List[int] = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line) + 1)

    start_offset = line_offsets[edit.range.start.line] + edit.range.start.character
    end_offset = line_offsets[edit.range.end.line] + edit.range.end.character

    full = "\n".join(lines)
    return full[:start_offset] + edit.new_text + full[end_offset:]


def _apply_workspace_edit(source: str, ws_edit: WorkspaceEdit) -> str:
    """Apply all edits in a WorkspaceEdit to source and return the result."""
    assert ws_edit.changes is not None
    # Collect all edits and apply in reverse order to preserve offsets
    all_edits: List[TextEdit] = []
    for edits in ws_edit.changes.values():
        all_edits.extend(edits)

    # Sort by position (reverse order for safe application)
    all_edits.sort(
        key=lambda e: (e.range.start.line, e.range.start.character),
        reverse=True,
    )

    result = source
    for edit in all_edits:
        result = _apply_edit(result, edit)
    return result


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def provider() -> RenameProvider:
    """Create a RenameProvider instance."""
    return RenameProvider()


# ---------------------------------------------------------------------------
# Simple-input keyword rename
# ---------------------------------------------------------------------------


class TestSimpleInputKeywordRename:
    """Tests for renaming keywords in ! simple-input lines."""

    def test_prepare_rename_on_method(self, provider: RenameProvider) -> None:
        """Cursor on B3LYP in simple input should return a valid Range."""
        source = "! B3LYP def2-SVP OPT\n"
        pos = Position(line=0, character=4)  # on "B3LYP"

        result = provider.prepare_rename(source, pos)
        assert result is not None
        assert result.start.character == 2
        assert result.end.character == 7

    def test_rename_method_updates_all_occurrences(
        self, provider: RenameProvider,
    ) -> None:
        """Renaming B3LYP to PBE0 should update all occurrences in ! lines."""
        source = "! B3LYP def2-SVP OPT\n! B3LYP def2-TZVP\n"
        pos = Position(line=0, character=4)

        edit = provider.get_rename_edits(source, "file:///test.orca", pos, "PBE0")
        assert edit is not None

        result = _apply_workspace_edit(source, edit)
        assert "B3LYP" not in result
        assert result.count("PBE0") == 2

    def test_rename_basis_set(self, provider: RenameProvider) -> None:
        """Renaming def2-SVP to def2-TZVP should update occurrences."""
        source = "! B3LYP def2-SVP OPT\n"
        pos = Position(line=0, character=10)  # on "def2-SVP"

        edit = provider.get_rename_edits(source, "file:///test.orca", pos, "def2-TZVP")
        assert edit is not None

        result = _apply_workspace_edit(source, edit)
        assert "def2-SVP" not in result
        assert "def2-TZVP" in result

    def test_rename_job_type(self, provider: RenameProvider) -> None:
        """Renaming OPT to FREQ should update occurrences."""
        source = "! B3LYP def2-SVP OPT\n"
        pos = Position(line=0, character=18)  # on "OPT"

        edit = provider.get_rename_edits(source, "file:///test.orca", pos, "FREQ")
        assert edit is not None

        result = _apply_workspace_edit(source, edit)
        assert "OPT" not in result
        assert "FREQ" in result

    def test_prepare_rename_returns_none_on_empty_line(
        self, provider: RenameProvider,
    ) -> None:
        """Cursor on empty line should return None."""
        source = "! B3LYP def2-SVP OPT\n\n"
        pos = Position(line=1, character=0)

        result = provider.prepare_rename(source, pos)
        assert result is None


# ---------------------------------------------------------------------------
# % block name rename
# ---------------------------------------------------------------------------


class TestBlockNameRename:
    """Tests for renaming % block names."""

    def test_prepare_rename_rejects_reserved_block_name(
        self, provider: RenameProvider,
    ) -> None:
        """Cursor on reserved %scf block name should be rejected."""
        source = "%scf\n  maxiter 100\nend\n"
        pos = Position(line=0, character=2)  # on "scf"

        result = provider.prepare_rename(source, pos)
        assert result is None

    def test_prepare_rename_rejects_reserved_block_maxcore(
        self, provider: RenameProvider,
    ) -> None:
        """Cursor on reserved %maxcore block name should be rejected."""
        source = "%maxcore 4000\n"
        pos = Position(line=0, character=2)  # on "maxcore"

        result = provider.prepare_rename(source, pos)
        assert result is None

    def test_get_rename_edits_rejects_reserved_block(
        self, provider: RenameProvider,
    ) -> None:
        """Renaming a reserved %scf block should return None."""
        source = "%scf\n  maxiter 100\nend\n"
        pos = Position(line=0, character=2)

        edit = provider.get_rename_edits(source, "file:///test.orca", pos, "scf2")
        assert edit is None


# ---------------------------------------------------------------------------
# % block parameter rename
# ---------------------------------------------------------------------------


class TestBlockParamRename:
    """Tests for renaming % block parameter keywords."""

    def test_prepare_rename_on_block_param_keyword(
        self, provider: RenameProvider,
    ) -> None:
        """Cursor on 'nprocs' inside %pal block should return a Range."""
        source = "%pal\n  nprocs 4\nend\n"
        pos = Position(line=1, character=4)  # on "nprocs"

        result = provider.prepare_rename(source, pos)
        # nprocs is not in ALL_KEYWORDS, so it should be renameable
        assert result is not None

    def test_rename_nprocs_updates_all_occurrences(
        self, provider: RenameProvider,
    ) -> None:
        """Renaming nprocs to numcores should update all occurrences."""
        source = "%pal\n  nprocs 4\nend\n"
        pos = Position(line=1, character=4)

        edit = provider.get_rename_edits(
            source, "file:///test.orca", pos, "numcores",
        )
        assert edit is not None

        result = _apply_workspace_edit(source, edit)
        assert "nprocs" not in result
        assert "numcores" in result

    def test_rename_maxiter_updates_all_occurrences(
        self, provider: RenameProvider,
    ) -> None:
        """Renaming maxiter to max_iterations should update occurrences."""
        source = "%scf\n  maxiter 100\nend\n"
        pos = Position(line=1, character=4)  # on "maxiter"

        edit = provider.get_rename_edits(
            source, "file:///test.orca", pos, "max_iterations",
        )
        assert edit is not None

        result = _apply_workspace_edit(source, edit)
        assert "maxiter" not in result
        assert "max_iterations" in result


# ---------------------------------------------------------------------------
# Rejected targets
# ---------------------------------------------------------------------------


class TestRejectedTargets:
    """Tests for targets that should be rejected."""

    def test_reject_end_keyword(self, provider: RenameProvider) -> None:
        """Renaming 'end' keyword should be rejected."""
        source = "%scf\n  maxiter 100\nend\n"
        pos = Position(line=2, character=0)  # on "end"

        result = provider.prepare_rename(source, pos)
        assert result is None

    def test_reject_geometry_element(self, provider: RenameProvider) -> None:
        """Renaming element symbol in geometry should be rejected."""
        source = "! B3LYP def2-SVP OPT\n\n* xyz 0 1\n  H 0.0 0.0 0.0\n*\n"
        pos = Position(line=3, character=2)  # on "H"

        result = provider.prepare_rename(source, pos)
        assert result is None

    def test_reject_out_of_range_line(self, provider: RenameProvider) -> None:
        """Position beyond file length should return None."""
        source = "! B3LYP def2-SVP\n"
        pos = Position(line=99, character=0)

        result = provider.prepare_rename(source, pos)
        assert result is None

    def test_reject_negative_line(self, provider: RenameProvider) -> None:
        """Position on a line that is just whitespace should return None."""
        source = "\n\n\n"
        pos = Position(line=0, character=0)

        result = provider.prepare_rename(source, pos)
        assert result is None

    def test_reject_empty_new_name(self, provider: RenameProvider) -> None:
        """Empty new name should be rejected."""
        source = "! B3LYP def2-SVP OPT\n"
        pos = Position(line=0, character=4)

        edit = provider.get_rename_edits(source, "file:///test.orca", pos, "")
        assert edit is None

    def test_reject_new_name_starting_with_digit(
        self, provider: RenameProvider,
    ) -> None:
        """New name starting with a digit should be rejected."""
        source = "! B3LYP def2-SVP OPT\n"
        pos = Position(line=0, character=4)

        edit = provider.get_rename_edits(source, "file:///test.orca", pos, "3LYP")
        assert edit is None


# ---------------------------------------------------------------------------
# Multi-occurrence rename
# ---------------------------------------------------------------------------


class TestMultiOccurrenceRename:
    """Tests for renaming symbols that appear in multiple locations."""

    def test_rename_keyword_in_multiple_simple_input_lines(
        self, provider: RenameProvider,
    ) -> None:
        """Renaming a keyword should update all ! lines."""
        source = "! B3LYP def2-SVP OPT\n! B3LYP def2-TZVP SP\n"
        pos = Position(line=0, character=4)  # on first "B3LYP"

        edit = provider.get_rename_edits(
            source, "file:///test.orca", pos, "PBE0",
        )
        assert edit is not None

        result = _apply_workspace_edit(source, edit)
        assert result.count("B3LYP") == 0
        assert result.count("PBE0") == 2

    def test_rename_block_param_in_multiple_blocks(
        self, provider: RenameProvider,
    ) -> None:
        """Renaming a block parameter should update all block occurrences."""
        source = "%scf\n  maxiter 100\nend\n%scf\n  maxiter 200\nend\n"
        pos = Position(line=1, character=4)  # on first "maxiter"

        edit = provider.get_rename_edits(
            source, "file:///test.orca", pos, "max_iterations",
        )
        assert edit is not None

        result = _apply_workspace_edit(source, edit)
        assert "maxiter" not in result
        assert result.count("max_iterations") == 2


# ---------------------------------------------------------------------------
# is_valid_rename
# ---------------------------------------------------------------------------


class TestIsValidRename:
    """Tests for the is_valid_rename helper."""

    def test_valid_rename_on_simple_input_keyword(
        self, provider: RenameProvider,
    ) -> None:
        """Valid rename on a simple-input keyword should return True."""
        source = "! B3LYP def2-SVP OPT\n"
        pos = Position(line=0, character=4)

        assert provider.is_valid_rename(source, pos, "PBE0") is True

    def test_invalid_rename_on_end_keyword(
        self, provider: RenameProvider,
    ) -> None:
        """Rename on 'end' keyword should return False."""
        source = "%scf\n  maxiter 100\nend\n"
        pos = Position(line=2, character=0)

        assert provider.is_valid_rename(source, pos, "finish") is False

    def test_invalid_rename_empty_new_name(
        self, provider: RenameProvider,
    ) -> None:
        """Empty new name should return False."""
        source = "! B3LYP def2-SVP OPT\n"
        pos = Position(line=0, character=4)

        assert provider.is_valid_rename(source, pos, "") is False


# ---------------------------------------------------------------------------
# Workspace edit structure
# ---------------------------------------------------------------------------


class TestWorkspaceEditStructure:
    """Tests for the structure of returned WorkspaceEdit objects."""

    def test_edits_target_correct_uri(
        self, provider: RenameProvider,
    ) -> None:
        """Workspace edit changes should target the provided URI."""
        source = "! B3LYP def2-SVP OPT\n"
        uri = "file:///path/to/test.orca"
        pos = Position(line=0, character=4)

        edit = provider.get_rename_edits(source, uri, pos, "PBE0")
        assert edit is not None
        assert edit.changes is not None
        assert uri in edit.changes

    def test_edit_ranges_are_correct(
        self, provider: RenameProvider,
    ) -> None:
        """TextEdits should have correct ranges."""
        source = "! B3LYP def2-SVP OPT\n"
        pos = Position(line=0, character=4)

        edit = provider.get_rename_edits(
            source, "file:///test.orca", pos, "PBE0",
        )
        assert edit is not None
        assert edit.changes is not None
        edits = list(edit.changes.values())[0]
        assert len(edits) == 1

        text_edit = edits[0]
        assert text_edit.range.start.line == 0
        assert text_edit.range.start.character == 2  # after "! "
        assert text_edit.range.end.character == 7  # end of "B3LYP"
        assert text_edit.new_text == "PBE0"


# ---------------------------------------------------------------------------
# No-op / edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_cursor_on_whitespace(self, provider: RenameProvider) -> None:
        """Cursor on whitespace should return None."""
        source = "! B3LYP  def2-SVP\n"
        pos = Position(line=0, character=8)  # on the extra space

        result = provider.prepare_rename(source, pos)
        assert result is None

    def test_cursor_at_line_end(self, provider: RenameProvider) -> None:
        """Cursor at the end of a line should return None or handle gracefully."""
        source = "! B3LYP\n"
        pos = Position(line=0, character=7)  # just past "B3LYP"

        # Should not crash; may return None since cursor is past the word
        result = provider.prepare_rename(source, pos)
        # Either None or a valid range is acceptable here

    def test_single_line_block_param_rename(
        self, provider: RenameProvider,
    ) -> None:
        """Renaming a param in a single-line % block should work."""
        source = "%maxcore 4000\n"
        pos = Position(line=0, character=2)  # on "maxcore"

        # maxcore is a reserved block name, so it should be rejected
        result = provider.prepare_rename(source, pos)
        assert result is None

    def test_rename_preserves_line_structure(
        self, provider: RenameProvider,
    ) -> None:
        """After renaming, line structure should be preserved."""
        source = "! B3LYP def2-SVP OPT\n\n* xyz 0 1\n  H 0 0 0\n*\n"
        pos = Position(line=0, character=4)

        edit = provider.get_rename_edits(
            source, "file:///test.orca", pos, "PBE0",
        )
        assert edit is not None

        result = _apply_workspace_edit(source, edit)
        result_lines = result.split("\n")
        assert len(result_lines) == source.split("\n").__len__()
        assert result_lines[1] == ""  # blank line preserved
        assert result_lines[2] == "* xyz 0 1"  # geometry preserved
