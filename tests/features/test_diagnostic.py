"""Tests for DiagnosticProvider."""

import json

import pytest

from orca_lsp.features.diagnostic import DiagnosticProvider
from orca_lsp.parser import ORCAParser


@pytest.fixture
def provider() -> DiagnosticProvider:
    """Create a DiagnosticProvider with a fresh parser."""
    return DiagnosticProvider(ORCAParser())


class TestDiagnosticProvider:
    """Tests for DiagnosticProvider."""

    def test_provider_exists(self, provider: DiagnosticProvider) -> None:
        """Test that provider can be created."""
        assert provider is not None

    def test_get_diagnostics_empty(self, provider: DiagnosticProvider) -> None:
        """Test diagnostics for empty document.

        Empty input should report errors (missing simple input, missing
        geometry) but should not crash.
        """
        diagnostics = provider.get_diagnostics("")
        assert isinstance(diagnostics, list)
        assert len(diagnostics) > 0

    def test_get_diagnostics_valid_input(self, provider: DiagnosticProvider) -> None:
        """Test diagnostics for a valid minimal ORCA input.

        A well-formed input should produce at most warnings (e.g. missing
        %maxcore), but no errors.
        """
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "  H 0.0 0.0 0.74\n"
            "*\n"
        )
        diagnostics = provider.get_diagnostics(text)
        errors = [d for d in diagnostics if d.severity == 1]  # Error = 1
        assert len(errors) == 0, f"Unexpected errors: {[d.message for d in errors]}"

    def test_get_diagnostics_missing_simple_input(self, provider: DiagnosticProvider) -> None:
        """Test detection of missing simple input line."""
        text = "* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("simple input" in m.lower() for m in messages), (
            f"Expected 'simple input' error, got: {messages}"
        )

    def test_get_diagnostics_missing_geometry(self, provider: DiagnosticProvider) -> None:
        """Test detection of missing geometry section."""
        text = "! B3LYP def2-TZVP\n"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("geometry" in m.lower() for m in messages), (
            f"Expected 'geometry' error, got: {messages}"
        )

    def test_get_diagnostics_no_method(self, provider: DiagnosticProvider) -> None:
        """Test detection of missing method in simple input."""
        text = "! def2-TZVP\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("method" in m.lower() for m in messages), (
            f"Expected 'method' error, got: {messages}"
        )

    def test_get_diagnostics_no_basis_set(self, provider: DiagnosticProvider) -> None:
        """Test detection of missing basis set in simple input."""
        text = "! B3LYP\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("basis" in m.lower() for m in messages), (
            f"Expected 'basis' error, got: {messages}"
        )

    def test_warning_missing_maxcore(self, provider: DiagnosticProvider) -> None:
        """Test warning when %maxcore is not specified."""
        text = "! B3LYP def2-TZVP SP\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.get_diagnostics(text)
        warnings = [
            d for d in diagnostics if d.severity == 2  # Warning = 2
        ]
        messages = [d.message for d in warnings]
        assert any("maxcore" in m.lower() for m in messages), (
            f"Expected 'maxcore' warning, got: {messages}"
        )

    def test_warning_invalid_element(self, provider: DiagnosticProvider) -> None:
        """Test error for invalid element symbol in geometry."""
        text = "! B3LYP def2-TZVP SP\n* xyz 0 1\n  Xx 0 0 0\n*\n"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("invalid element" in m.lower() for m in messages), (
            f"Expected 'invalid element' error, got: {messages}"
        )

    def test_error_mutually_exclusive_scf_types(self, provider: DiagnosticProvider) -> None:
        """Test error for mutually exclusive SCF types."""
        text = "! RHF UHF def2-TZVP\n* xyz 0 1\n  H 0 0 0\n*\n"
        diagnostics = provider.get_diagnostics(text)
        messages = [d.message for d in diagnostics]
        assert any("mutually exclusive" in m.lower() for m in messages), (
            f"Expected 'mutually exclusive' error, got: {messages}"
        )

    def test_diagnostic_has_source(self, provider: DiagnosticProvider) -> None:
        """Test that every diagnostic has source='orca-lsp'."""
        text = "! INVALID_KEYWORD\n"
        diagnostics = provider.get_diagnostics(text)
        for d in diagnostics:
            assert d.source == "orca-lsp", f"Expected source 'orca-lsp', got '{d.source}'"

    def test_diagnostic_has_range(self, provider: DiagnosticProvider) -> None:
        """Test that every diagnostic has a valid range."""
        text = "! B3LYP\n"
        diagnostics = provider.get_diagnostics(text)
        for d in diagnostics:
            assert d.range is not None
            assert d.range.start.line >= 0
            assert d.range.end.line >= 0


class TestDiagnosticSnapshot:
    """Tests for the JSON snapshot API."""

    def test_snapshot_is_list_of_dicts(self, provider: DiagnosticProvider) -> None:
        """Test that snapshot returns a list of dicts."""
        text = "! B3LYP\n"
        snapshot = provider.get_diagnostics_snapshot(text)
        assert isinstance(snapshot, list)
        for entry in snapshot:
            assert isinstance(entry, dict)

    def test_snapshot_entry_keys(self, provider: DiagnosticProvider) -> None:
        """Test that each snapshot entry has the expected keys."""
        text = "! B3LYP\n"
        snapshot = provider.get_diagnostics_snapshot(text)
        expected_keys = {
            "line",
            "character",
            "end_line",
            "end_character",
            "severity",
            "source",
            "message",
        }
        for entry in snapshot:
            assert set(entry.keys()) == expected_keys

    def test_snapshot_is_json_serializable(self, provider: DiagnosticProvider) -> None:
        """Test that the snapshot can be serialized to JSON without errors."""
        text = "! B3LYP def2-TZVP\n* xyz 0 1\n  H 0 0 0\n*\n"
        snapshot = provider.get_diagnostics_snapshot(text)
        serialized = json.dumps(snapshot)
        assert isinstance(serialized, str)
        deserialized = json.loads(serialized)
        assert deserialized == snapshot

    def test_snapshot_deterministic(self, provider: DiagnosticProvider) -> None:
        """Test that snapshots are deterministic across calls."""
        text = "! B3LYP def2-TZVP SP\n* xyz 0 1\n  H 0 0 0\n  H 0 0 0.74\n*\n"
        snap1 = provider.get_diagnostics_snapshot(text)
        snap2 = provider.get_diagnostics_snapshot(text)
        assert snap1 == snap2

    def test_get_diagnostics_json(self, provider: DiagnosticProvider) -> None:
        """Test the convenience JSON string method."""
        text = "! B3LYP\n"
        json_str = provider.get_diagnostics_json(text)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert isinstance(parsed, list)

    def test_snapshot_empty_input(self, provider: DiagnosticProvider) -> None:
        """Test snapshot for empty input has entries."""
        snapshot = provider.get_diagnostics_snapshot("")
        assert len(snapshot) > 0
        # Empty input produces errors (missing simple input, missing geometry)
        # and warnings (missing %maxcore)
        errors = [e for e in snapshot if e["severity"] == "error"]
        assert len(errors) > 0, "Expected at least one error for empty input"

    def test_snapshot_valid_input_no_errors(self, provider: DiagnosticProvider) -> None:
        """Test snapshot for valid input has no error-severity entries."""
        text = (
            "! B3LYP def2-TZVP SP\n"
            "%maxcore 4000\n"
            "* xyz 0 1\n"
            "  H 0.0 0.0 0.0\n"
            "  H 0.0 0.0 0.74\n"
            "*\n"
        )
        snapshot = provider.get_diagnostics_snapshot(text)
        errors = [e for e in snapshot if e["severity"] == "error"]
        assert len(errors) == 0, f"Unexpected errors in snapshot: {errors}"

    def test_snapshot_sorted_order(self, provider: DiagnosticProvider) -> None:
        """Test that snapshot entries are sorted by line, character, severity."""
        text = (
            "! RHF UHF def2-TZVP\n"
            "* xyz 0 1\n"
            "  H 0 0 0\n"
            "*\n"
        )
        snapshot = provider.get_diagnostics_snapshot(text)
        for i in range(1, len(snapshot)):
            prev = snapshot[i - 1]
            curr = snapshot[i]
            key_prev = (prev["line"], prev["character"], prev["severity"])
            key_curr = (curr["line"], curr["character"], curr["severity"])
            assert key_prev <= key_curr, (
                f"Snapshot not sorted at index {i}: {key_prev} > {key_curr}"
            )
