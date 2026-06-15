"""Closed-loop log diagnostics and preview fix evidence for OpenQC maturity."""

from __future__ import annotations

import json
import re
from pathlib import Path

from orca_lsp.agent_operations import operation_path
from orca_lsp.tool import _collect_diagnostics, check_path, main

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestLogDiagnosticsCLI:
    def test_log_fixture_emits_scf_diagnostic(self) -> None:
        log_path = FIXTURES_DIR / "log" / "scf_convergence_failure.log"
        payload = check_path(log_path)
        assert payload["ok"] is False
        assert payload["diagnostic_engine"] == "1.0"
        codes = {item["code"] for item in payload["diagnostics"]}
        assert "ORCA-E024" in codes

    def test_log_fixture_has_source_provenance(self) -> None:
        log_path = FIXTURES_DIR / "log" / "scf_convergence_failure.log"
        payload = check_path(log_path)
        scf = next(item for item in payload["diagnostics"] if item["code"] == "ORCA-E024")
        provenance = scf["source_provenance"]
        assert provenance["id"] == "orca-official-docs"
        assert provenance["url"] == "https://www.faccts.de/docs/orca/"

    def test_cli_check_log_fixture(self) -> None:
        log_path = FIXTURES_DIR / "log" / "scf_convergence_failure.log"
        assert main(["check", str(log_path), "--fail-on-blocking"]) == 1


class TestPreviewFixActions:
    def test_unclosed_block_fix_preview(self) -> None:
        fixture = FIXTURES_DIR / "invalid" / "unclosed_block.inp"
        payload = operation_path(
            fixture,
            "fix",
            software="orca",
            file_type_func=lambda path: path.suffix.lstrip("."),
            collect_diagnostics=_collect_diagnostics,
        )
        actions = payload["actions"]
        assert actions, "Expected preview fix actions for unclosed % block"
        preview = next(action for action in actions if action.get("preview_only"))
        assert preview["edit"] is not None
        assert "end" in json.dumps(preview["edit"])

    def test_missing_coord_terminator_fix_preview(self) -> None:
        fixture = FIXTURES_DIR / "invalid" / "missing_xyz_terminator.inp"
        payload = operation_path(
            fixture,
            "fix",
            software="orca",
            file_type_func=lambda path: path.suffix.lstrip("."),
            collect_diagnostics=_collect_diagnostics,
        )
        actions = payload["actions"]
        assert actions, "Expected preview fix actions for missing coordinate terminator"
        preview = next(action for action in actions if action.get("preview_only"))
        assert preview["edit"] is not None
        assert "*" in json.dumps(preview["edit"])

    def test_cli_fix_invalid_fixture(self) -> None:
        fixture = FIXTURES_DIR / "invalid" / "unclosed_block.inp"
        assert main(["fix", str(fixture)]) == 0


class TestReleaseProvenance:
    def test_version_file_matches_capabilities(self) -> None:
        version_text = Path("VERSION").read_text(encoding="utf-8").strip()
        capabilities = json.loads(Path("lsp-capabilities.json").read_text(encoding="utf-8"))
        assert version_text == capabilities["version"]
        assert capabilities["release_provenance"]["version_file"] == "VERSION"

    def test_pyproject_version_matches_version_file(self) -> None:
        version_text = Path("VERSION").read_text(encoding="utf-8").strip()
        pyproject_text = Path("pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject_text, re.MULTILINE)
        assert match is not None, "Expected project.version in pyproject.toml"
        assert match.group(1) == version_text

    def test_capabilities_fixture_matches_repo_manifest(self) -> None:
        repo = json.loads(Path("lsp-capabilities.json").read_text(encoding="utf-8"))
        fixture = json.loads(
            (FIXTURES_DIR / "capabilities" / "lsp_capabilities.json").read_text(encoding="utf-8")
        )
        assert fixture["release_provenance"] == repo["release_provenance"]
        assert fixture["openqc_compatibility"] == repo["openqc_compatibility"]
