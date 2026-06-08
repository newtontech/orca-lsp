"""Tests for the CodeActionProvider.

Each test exercises a before/after edit for a specific quick fix,
verifying that the code action produces the correct text replacement.
"""

from __future__ import annotations

from typing import List, Optional

import pytest
from lsprotocol.types import (
    CodeAction,
    CodeActionKind,
    Diagnostic,
    DiagnosticSeverity,
    Position,
    Range,
)

from orca_lsp.features.code_actions import CodeActionProvider
from orca_lsp.features.lint import (
    RULE_DUPLICATE_BLOCK,
    RULE_DUPLICATE_TOKEN,
    RULE_MISSING_MAXCORE,
    RULE_UNCLOSED_BLOCK,
    RULE_UNKNOWN_BLOCK,
    RULE_UNKNOWN_TOKEN,
)

# Rule codes from typecheck provider (defined locally to avoid import).
RULE_INVALID_ENUM = "TC-E002"
RULE_MISSING_SECTION = "TC-W001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_diagnostic(
    message: str,
    code: str,
    line: int = 0,
    col_start: int = 0,
    col_end: int = 10,
    severity: DiagnosticSeverity = DiagnosticSeverity.Error,
    source: str = "orca-lsp-lint",
) -> Diagnostic:
    """Create a Diagnostic with the given fields."""
    return Diagnostic(
        range=Range(
            start=Position(line=line, character=col_start),
            end=Position(line=line, character=col_end),
        ),
        message=message,
        severity=severity,
        source=source,
        code=code,
    )


def _apply_action(source: str, action: CodeAction) -> str:
    """Apply a CodeAction's workspace edit to *source* and return the result.

    Assumes a single change with key "document".
    """
    assert action.edit is not None
    changes = action.edit.changes
    assert changes is not None
    assert "document" in changes
    edits = changes["document"]
    assert len(edits) == 1

    edit = edits[0]
    lines = source.split("\n")

    # Build character-offset mapping
    line_offsets: List[int] = [0]
    for line in lines:
        line_offsets.append(line_offsets[-1] + len(line) + 1)

    start_offset = line_offsets[edit.range.start.line] + edit.range.start.character
    end_offset = line_offsets[edit.range.end.line] + edit.range.end.character

    full = "\n".join(lines)
    result = full[:start_offset] + edit.new_text + full[end_offset:]
    return result


def _find_diagnostic_action(
    actions: List[CodeAction], diag: Diagnostic,
) -> Optional[CodeAction]:
    """Find the action attached to a specific diagnostic."""
    for action in actions:
        if action.diagnostics and diag in action.diagnostics:
            return action
    return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def provider() -> CodeActionProvider:
    """Create a CodeActionProvider instance."""
    return CodeActionProvider()


# ---------------------------------------------------------------------------
# Unknown token fix (ORCA-E001)
# ---------------------------------------------------------------------------

class TestFixUnknownToken:
    """Tests for the unknown-token quick fix (ORCA-E001)."""

    def test_suggests_b3lyp_from_typo(self, provider: CodeActionProvider) -> None:
        """'b3lypp' should be corrected to 'B3LYP'."""
        source = "! b3lypp def2-SVP OPT\n"
        diag = _make_diagnostic(
            "Unknown token in simple input: 'b3lypp'",
            RULE_UNKNOWN_TOKEN,
            line=0,
            col_start=2,
            col_end=8,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        assert action.kind == CodeActionKind.QuickFix
        assert "b3lypp" in action.title
        assert "B3LYP" in action.title

        result = _apply_action(source, action)
        assert "B3LYP" in result
        assert "b3lypp" not in result

    def test_suggests_method_from_levenshtein(self, provider: CodeActionProvider) -> None:
        """A close misspelling should suggest a valid keyword."""
        source = "! B3LY def2-SVP OPT\n"
        diag = _make_diagnostic(
            "Unknown token in simple input: 'B3LY'",
            RULE_UNKNOWN_TOKEN,
            line=0,
            col_start=2,
            col_end=6,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None
        assert "B3LYP" in action.title

    def test_no_action_for_very_short_token(self, provider: CodeActionProvider) -> None:
        """Single-character tokens should not get a suggestion."""
        source = "! B def2-SVP OPT\n"
        diag = _make_diagnostic(
            "Unknown token in simple input: 'B'",
            RULE_UNKNOWN_TOKEN,
            line=0,
            col_start=2,
            col_end=3,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is None


# ---------------------------------------------------------------------------
# Unknown block fix (ORCA-E002)
# ---------------------------------------------------------------------------

class TestFixUnknownBlock:
    """Tests for the unknown-%block quick fix (ORCA-E002)."""

    def test_suggests_scf_from_typo(self, provider: CodeActionProvider) -> None:
        """'%sfc' should be corrected to '%scf'."""
        source = "%sfc\n  maxiter 100\nend\n"
        diag = _make_diagnostic(
            "Unknown % block: '%sfc'",
            RULE_UNKNOWN_BLOCK,
            line=0,
            col_start=0,
            col_end=4,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        assert "scf" in action.title.lower()

        result = _apply_action(source, action)
        assert "%scf" in result
        assert "%sfc" not in result

    def test_no_action_for_very_distant_block(self, provider: CodeActionProvider) -> None:
        """A block name that is very far from any valid block should not get a fix."""
        source = "%zzzzzzzzzzzzz\nend\n"
        diag = _make_diagnostic(
            "Unknown % block: '%zzzzzzzzzzzzz'",
            RULE_UNKNOWN_BLOCK,
            line=0,
            col_start=0,
            col_end=14,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is None


# ---------------------------------------------------------------------------
# Unclosed block fix (ORCA-E003)
# ---------------------------------------------------------------------------

class TestFixUnclosedBlock:
    """Tests for the unclosed-block quick fix (ORCA-E003)."""

    def test_adds_end_after_block_content(self, provider: CodeActionProvider) -> None:
        """Unclosed %scf block should get an 'end' inserted."""
        source = "! B3LYP def2-SVP OPT\n%scf\n  maxiter 100\n\n"
        diag = _make_diagnostic(
            "Unclosed % block: '%scf'",
            RULE_UNCLOSED_BLOCK,
            line=1,
            col_start=0,
            col_end=4,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        assert "end" in action.title.lower()
        assert "scf" in action.title.lower()

        result = _apply_action(source, action)
        assert "end" in result

    def test_adds_end_at_eof(self, provider: CodeActionProvider) -> None:
        """Unclosed block at end of file should get 'end' appended."""
        source = "! B3LYP def2-SVP\n%scf\n  maxiter 100"
        diag = _make_diagnostic(
            "Unclosed % block: '%scf'",
            RULE_UNCLOSED_BLOCK,
            line=1,
            col_start=0,
            col_end=4,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        result = _apply_action(source, action)
        assert result.endswith("end")


# ---------------------------------------------------------------------------
# Duplicate block fix (ORCA-E004)
# ---------------------------------------------------------------------------

class TestFixDuplicateBlock:
    """Tests for the duplicate-block quick fix (ORCA-E004)."""

    def test_removes_duplicate_block(self, provider: CodeActionProvider) -> None:
        """Second occurrence of a duplicate block should be removed."""
        source = "%scf\n  maxiter 100\nend\n%scf\n  maxiter 200\nend\n"
        diag = _make_diagnostic(
            "Duplicate % block: '%scf'",
            RULE_DUPLICATE_BLOCK,
            line=3,
            col_start=0,
            col_end=4,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        assert "Remove" in action.title
        assert "duplicate" in action.title.lower()

        result = _apply_action(source, action)
        # The first %scf block should remain
        assert result.count("maxiter 100") == 1
        # The duplicate should be gone
        assert "maxiter 200" not in result


# ---------------------------------------------------------------------------
# Missing maxcore fix (ORCA-W001)
# ---------------------------------------------------------------------------

class TestFixMissingMaxcore:
    """Tests for the missing-%maxcore quick fix (ORCA-W001)."""

    def test_adds_maxcore_after_simple_input(self, provider: CodeActionProvider) -> None:
        """Missing %maxcore diagnostic should produce an insertion fix."""
        source = "! B3LYP def2-SVP OPT\n\n* xyz 0 1\n  H 0 0 0\n*\n"
        diag = _make_diagnostic(
            "Missing %maxcore setting. Recommended: %maxcore 2000-4000 (MB per core)",
            RULE_MISSING_MAXCORE,
            line=0,
            severity=DiagnosticSeverity.Warning,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        result = _apply_action(source, action)
        assert "%maxcore 4000" in result


# ---------------------------------------------------------------------------
# Duplicate token fix (ORCA-W003)
# ---------------------------------------------------------------------------

class TestFixDuplicateToken:
    """Tests for the duplicate-token quick fix (ORCA-W003)."""

    def test_removes_duplicate_token(self, provider: CodeActionProvider) -> None:
        """Second occurrence of a duplicate token should be removed."""
        source = "! B3LYP B3LYP def2-SVP OPT\n"
        diag = _make_diagnostic(
            "Duplicate token in simple input: 'B3LYP'",
            RULE_DUPLICATE_TOKEN,
            line=0,
            col_start=7,
            col_end=12,
            severity=DiagnosticSeverity.Warning,
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        assert "Remove" in action.title
        assert "duplicate" in action.title.lower()

        result = _apply_action(source, action)
        assert result.count("B3LYP") == 1


# ---------------------------------------------------------------------------
# Invalid enum fix (TC-E002)
# ---------------------------------------------------------------------------

class TestFixInvalidEnum:
    """Tests for the invalid-enum quick fix (TC-E002)."""

    def test_suggests_basis_from_typo(self, provider: CodeActionProvider) -> None:
        """Misspelled basis set should be corrected via TC-E002."""
        source = "! B3LYP def2-TZV OPT\n"
        diag = _make_diagnostic(
            "Unknown keyword 'def2-TZV'. Did you mean 'def2-TZVP'?",
            RULE_INVALID_ENUM,
            line=0,
            col_start=8,
            col_end=16,
            source="orca-lsp-typecheck",
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        assert "def2-TZVP" in action.title

        result = _apply_action(source, action)
        assert "def2-TZVP" in result
        assert "def2-TZV " not in result  # space ensures not a substring of TZVP


# ---------------------------------------------------------------------------
# Missing section fix (TC-W001)
# ---------------------------------------------------------------------------

class TestFixMissingSection:
    """Tests for the missing-section quick fix (TC-W001)."""

    def test_adds_simple_input_line(self, provider: CodeActionProvider) -> None:
        """Missing simple input line should produce a stub insertion."""
        source = "* xyz 0 1\n  H 0 0 0\n*\n"
        diag = _make_diagnostic(
            "Missing required simple input line (e.g. '! B3LYP def2-TZVP OPT')",
            RULE_MISSING_SECTION,
            line=0,
            severity=DiagnosticSeverity.Warning,
            source="orca-lsp-typecheck",
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        assert "simple input" in action.title.lower()

        result = _apply_action(source, action)
        assert "! B3LYP def2-SVP OPT" in result

    def test_adds_geometry_section(self, provider: CodeActionProvider) -> None:
        """Missing geometry section should produce a stub insertion."""
        source = "! B3LYP def2-SVP OPT\n"
        diag = _make_diagnostic(
            "Missing required geometry section (e.g. '* xyz 0 1\\n  H 0 0 0\\n*')",
            RULE_MISSING_SECTION,
            line=0,
            severity=DiagnosticSeverity.Warning,
            source="orca-lsp-typecheck",
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is not None

        assert "geometry" in action.title.lower()

        result = _apply_action(source, action)
        assert "* xyz 0 1" in result


# ---------------------------------------------------------------------------
# General actions (not tied to a diagnostic)
# ---------------------------------------------------------------------------

class TestGeneralActions:
    """Tests for general code actions not tied to specific diagnostics."""

    def test_adds_maxcore_when_absent(self, provider: CodeActionProvider) -> None:
        """When no %maxcore is present and no diagnostic, a general action is offered."""
        source = "! B3LYP def2-SVP OPT\n\n* xyz 0 1\n  H 0 0 0\n*\n"
        actions = provider.get_code_actions(source, [])

        maxcore_actions = [a for a in actions if "maxcore" in a.title.lower()]
        assert len(maxcore_actions) >= 1

        result = _apply_action(source, maxcore_actions[0])
        assert "%maxcore 4000" in result

    def test_no_maxcore_action_when_present(self, provider: CodeActionProvider) -> None:
        """When %maxcore is already present, no general action should be offered."""
        source = "! B3LYP def2-SVP OPT\n%maxcore 4000\n\n* xyz 0 1\n  H 0 0 0\n*\n"
        actions = provider.get_code_actions(source, [])

        maxcore_actions = [a for a in actions if "maxcore" in a.title.lower()]
        assert len(maxcore_actions) == 0


# ---------------------------------------------------------------------------
# No-op cases
# ---------------------------------------------------------------------------

class TestNoActionCases:
    """Tests for diagnostics that should not produce a quick fix."""

    def test_no_action_for_unsupported_rule_code(
        self, provider: CodeActionProvider,
    ) -> None:
        """A diagnostic with an unrecognized rule code should not produce a fix."""
        source = "! B3LYP def2-SVP\n"
        diag = _make_diagnostic(
            "Some unsupported diagnostic",
            "ORCA-X999",
        )

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is None

    def test_no_action_for_diagnostic_without_code(
        self, provider: CodeActionProvider,
    ) -> None:
        """A diagnostic without a code should not produce a fix."""
        source = "! B3LYP def2-SVP\n"
        diag = _make_diagnostic("Some message", "")
        diag.code = None

        actions = provider.get_code_actions(source, [diag])
        action = _find_diagnostic_action(actions, diag)
        assert action is None


# ---------------------------------------------------------------------------
# Multiple diagnostics
# ---------------------------------------------------------------------------

class TestMultipleDiagnostics:
    """Tests for handling multiple diagnostics at once."""

    def test_produces_fix_for_each_supported_diagnostic(
        self, provider: CodeActionProvider,
    ) -> None:
        """Multiple diagnostics should each produce their own fix."""
        source = "! b3lypp B3LYP def2-SVP OPT\n%scf\n  maxiter 100\n"
        diags = [
            _make_diagnostic(
                "Unknown token in simple input: 'b3lypp'",
                RULE_UNKNOWN_TOKEN,
                line=0,
                col_start=2,
                col_end=8,
            ),
            _make_diagnostic(
                "Unclosed % block: '%scf'",
                RULE_UNCLOSED_BLOCK,
                line=1,
                col_start=0,
                col_end=4,
            ),
        ]

        actions = provider.get_code_actions(source, diags)
        fix_actions = [a for a in actions if a.diagnostics]
        assert len(fix_actions) == 2


# ---------------------------------------------------------------------------
# Similarity score
# ---------------------------------------------------------------------------

class TestSimilarityScore:
    """Tests for the internal similarity scoring."""

    def test_identical_strings(self, provider: CodeActionProvider) -> None:
        """Identical strings should have a score of 1.0."""
        score = provider._similarity_score("b3lyp", "b3lyp")
        assert score == 1.0

    def test_empty_strings(self, provider: CodeActionProvider) -> None:
        """Empty strings should have a score of 1.0."""
        score = provider._similarity_score("", "")
        assert score == 1.0

    def test_completely_different(self, provider: CodeActionProvider) -> None:
        """Completely different strings should have a low score."""
        score = provider._similarity_score("abc", "xyz")
        assert score == 0.0

    def test_near_match(self, provider: CodeActionProvider) -> None:
        """A near-match should have a high score."""
        score = provider._similarity_score("b3lypp", "b3lyp")
        assert score > 0.7


# ---------------------------------------------------------------------------
# Typo table coverage
# ---------------------------------------------------------------------------

class TestTypoTable:
    """Tests for common ORCA typos in the explicit mapping."""

    @pytest.mark.parametrize(
        "typo,expected",
        [
            ("b3lypp", "B3LYP"),
            ("bp68", "BP86"),
            ("def2svp", "def2-SVP"),
            ("m062x", "M06-2X"),
            ("camb3lyp", "CAM-B3LYP"),
            ("sto-3g", "STO-3G"),
            ("cc-pvdz", "cc-pVDZ"),
        ],
    )
    def test_common_typo_corrected(
        self, provider: CodeActionProvider, typo: str, expected: str,
    ) -> None:
        """Common ORCA typos should be corrected via the typo table."""
        result = provider._find_closest_keyword(typo)
        assert result == expected
