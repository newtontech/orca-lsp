"""Tests that run the agent CLI against fixtures to verify DiagnosticEnvelope/v1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from orca_lsp.tool import check_path, main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_fixtures() -> list[Path]:
    return sorted((FIXTURES_DIR / "valid").glob("*.inp"))


@pytest.fixture
def invalid_fixtures() -> list[Path]:
    return sorted((FIXTURES_DIR / "invalid").glob("*.inp"))


@pytest.fixture
def log_fixtures() -> list[Path]:
    return sorted((FIXTURES_DIR / "log").glob("*.log"))


class TestValidFixtures:
    def test_valid_fixtures_exist(self, valid_fixtures: list[Path]) -> None:
        assert len(valid_fixtures) > 0, "No valid fixtures found"

    def test_valid_fixtures_pass_check(self, valid_fixtures: list[Path]) -> None:
        for fixture in valid_fixtures:
            payload = check_path(fixture)
            assert payload["ok"] is True, (
                f"Valid fixture {fixture.name} failed check: "
                f"{[d['code'] for d in payload['diagnostics'] if d['blocking']]}"
            )

    def test_valid_fixtures_have_no_blocking_diagnostics(self, valid_fixtures: list[Path]) -> None:
        for fixture in valid_fixtures:
            payload = check_path(fixture)
            blocking = [d for d in payload["diagnostics"] if d["blocking"]]
            assert (
                len(blocking) == 0
            ), f"Valid fixture {fixture.name} has blocking diagnostics: {blocking}"

    def test_valid_fixtures_diagnostic_envelope_v1(self, valid_fixtures: list[Path]) -> None:
        for fixture in valid_fixtures:
            payload = check_path(fixture)
            assert (
                payload["diagnostic_engine"] == "1.0"
            ), f"Fixture {fixture.name} missing DiagnosticEnvelope/v1"
            for diag in payload["diagnostics"]:
                assert "code" in diag
                assert "severity" in diag
                assert "blocking" in diag
                assert "source" in diag
                assert "range" in diag


class TestInvalidFixtures:
    def test_invalid_fixtures_exist(self, invalid_fixtures: list[Path]) -> None:
        assert len(invalid_fixtures) > 0, "No invalid fixtures found"

    def test_invalid_fixtures_fail_check(self, invalid_fixtures: list[Path]) -> None:
        for fixture in invalid_fixtures:
            payload = check_path(fixture)
            assert (
                payload["ok"] is False
            ), f"Invalid fixture {fixture.name} should have failed check"

    def test_invalid_fixtures_have_blocking_diagnostics(self, invalid_fixtures: list[Path]) -> None:
        for fixture in invalid_fixtures:
            payload = check_path(fixture)
            blocking = [d for d in payload["diagnostics"] if d["blocking"]]
            assert (
                len(blocking) > 0
            ), f"Invalid fixture {fixture.name} should have blocking diagnostics"

    def test_invalid_fixtures_diagnostic_envelope_v1(self, invalid_fixtures: list[Path]) -> None:
        for fixture in invalid_fixtures:
            payload = check_path(fixture)
            assert payload["diagnostic_engine"] == "1.0"
            for diag in payload["diagnostics"]:
                assert "code" in diag
                assert "severity" in diag
                assert "blocking" in diag
                assert "source" in diag
                assert "range" in diag


class TestLogFixtures:
    def test_log_fixtures_exist(self, log_fixtures: list[Path]) -> None:
        assert len(log_fixtures) > 0, "No log fixtures found"

    def test_log_fixtures_are_readabable(self, log_fixtures: list[Path]) -> None:
        for fixture in log_fixtures:
            content = fixture.read_text(encoding="utf-8")
            assert len(content) > 0, f"Log fixture {fixture.name} is empty"


class TestCLIFixtureIntegration:
    def test_cli_check_valid_fixture(self, valid_fixtures: list[Path]) -> None:
        if not valid_fixtures:
            pytest.skip("No valid fixtures")
        fixture = valid_fixtures[0]
        result = main(["check", str(fixture)])
        assert result == 0

    def test_cli_check_invalid_fixture(self, invalid_fixtures: list[Path]) -> None:
        if not invalid_fixtures:
            pytest.skip("No invalid fixtures")
        fixture = invalid_fixtures[0]
        result = main(["check", str(fixture), "--fail-on-blocking"])
        assert result == 1

    def test_cli_context_operation(self, valid_fixtures: list[Path]) -> None:
        if not valid_fixtures:
            pytest.skip("No valid fixtures")
        fixture = valid_fixtures[0]
        result = main(["context", str(fixture)])
        assert result == 0

    def test_cli_complete_operation(self, valid_fixtures: list[Path]) -> None:
        if not valid_fixtures:
            pytest.skip("No valid fixtures")
        fixture = valid_fixtures[0]
        result = main(["complete", str(fixture)])
        assert result == 0

    def test_cli_hover_operation(self, valid_fixtures: list[Path]) -> None:
        if not valid_fixtures:
            pytest.skip("No valid fixtures")
        fixture = valid_fixtures[0]
        result = main(["hover", str(fixture)])
        assert result == 0

    def test_cli_symbols_operation(self, valid_fixtures: list[Path]) -> None:
        if not valid_fixtures:
            pytest.skip("No valid fixtures")
        fixture = valid_fixtures[0]
        result = main(["symbols", str(fixture)])
        assert result == 0

    def test_cli_fix_operation(self, invalid_fixtures: list[Path]) -> None:
        if not invalid_fixtures:
            pytest.skip("No invalid fixtures")
        fixture = invalid_fixtures[0]
        result = main(["fix", str(fixture)])
        assert result == 0


class TestOpenQCCompatibility:
    def test_openqc_smoke_from_cli(self, valid_fixtures: list[Path]) -> None:
        if not valid_fixtures:
            pytest.skip("No valid fixtures")
        from orca_lsp.features.agent_api import AgentAPIProvider

        provider = AgentAPIProvider()
        smoke = provider.openqc_smoke()
        assert smoke["ok"] is True
        assert len(smoke["checks"]) > 0
        for check in smoke["checks"]:
            assert "name" in check
            assert "ok" in check
            assert "detail" in check

    def test_rule_manifest_completeness(self) -> None:
        from orca_lsp.features.agent_api import AgentAPIProvider

        provider = AgentAPIProvider()
        manifest = provider.get_rule_manifest()
        assert len(manifest) > 0
        for rule in manifest:
            assert "code" in rule
            assert "severity" in rule
            assert "description" in rule
