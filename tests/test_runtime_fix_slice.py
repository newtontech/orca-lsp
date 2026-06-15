"""Backend runtime/fix-preview vertical slice for ORCA input and log diagnostics (#93)."""

from __future__ import annotations

import json
from pathlib import Path

from orca_lsp.agent_operations import operation_path
from orca_lsp.tool import _collect_diagnostics, check_path, main, parse_log_path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestInputFailureModes:
    """CLI check covers malformed resource blocks, basis/ECP, and charge/multiplicity."""

    def test_malformed_pal_blocks_check(self) -> None:
        path = FIXTURES_DIR / "invalid" / "malformed_pal.inp"
        payload = check_path(path)
        codes = {item["code"] for item in payload["diagnostics"]}
        assert payload["ok"] is False
        assert "ORCA-E020" in codes

    def test_malformed_maxcore_blocks_check(self) -> None:
        path = FIXTURES_DIR / "invalid" / "malformed_maxcore.inp"
        payload = check_path(path)
        codes = {item["code"] for item in payload["diagnostics"]}
        assert payload["ok"] is False
        assert "ORCA-E027" in codes

    def test_missing_ecp_for_heavy_element(self) -> None:
        path = FIXTURES_DIR / "invalid" / "missing_ecp.inp"
        payload = check_path(path)
        codes = {item["code"] for item in payload["diagnostics"]}
        assert payload["ok"] is False
        assert "ORCA-E028" in codes
        ecp = next(item for item in payload["diagnostics"] if item["code"] == "ORCA-E028")
        assert ecp["blocking"] is True
        assert ecp["category"] == "cross-file reference"

    def test_charge_multiplicity_mismatch(self) -> None:
        path = FIXTURES_DIR / "invalid" / "charge_multiplicity_mismatch.inp"
        payload = check_path(path)
        codes = {item["code"] for item in payload["diagnostics"]}
        assert payload["ok"] is False
        assert "ORCA-E007" in codes

    def test_ri_missing_auxiliary_basis_warning(self) -> None:
        path = FIXTURES_DIR / "warnings" / "ri_missing_aux.inp"
        payload = check_path(path)
        codes = {item["code"] for item in payload["diagnostics"]}
        assert "ORCA-W021" in codes


class TestLogFailureModes:
    """parse-log and check on runtime snippets cover SCF, error termination, and basis errors."""

    def test_parse_log_scf_convergence(self) -> None:
        path = FIXTURES_DIR / "log" / "scf_convergence_failure.log"
        payload = parse_log_path(path)
        assert payload["operation"] == "parse-log"
        assert payload["diagnostic_engine"] == "1.0"
        codes = {item["code"] for item in payload["diagnostics"]}
        assert "ORCA-E024" in codes

    def test_parse_log_error_termination(self) -> None:
        path = FIXTURES_DIR / "log" / "error_termination.log"
        payload = parse_log_path(path)
        codes = {item["code"] for item in payload["diagnostics"]}
        assert "ORCA-E025" in codes

    def test_parse_log_basis_not_found(self) -> None:
        path = FIXTURES_DIR / "log" / "basis_set_not_found.log"
        payload = parse_log_path(path)
        codes = {item["code"] for item in payload["diagnostics"]}
        assert "ORCA-E026" in codes
        basis = next(item for item in payload["diagnostics"] if item["code"] == "ORCA-E026")
        assert basis["source_provenance"]["schema_source"] == "raw/assets/orca-basis-sets-reference.md"

    def test_cli_parse_log_exit_code(self) -> None:
        path = FIXTURES_DIR / "log" / "error_termination.log"
        assert main(["parse-log", str(path), "--fail-on-blocking"]) == 1


class TestFixPreviewAndRefusal:
    """CLI fix returns preview edits or explicit refusal reasons for unsafe diagnostics."""

    def test_missing_basis_fix_preview(self) -> None:
        path = FIXTURES_DIR / "invalid" / "missing_basis.inp"
        payload = operation_path(
            path,
            "fix",
            software="orca",
            file_type_func=lambda p: p.suffix.lstrip("."),
            collect_diagnostics=_collect_diagnostics,
        )
        previews = [action for action in payload["actions"] if action.get("preview_only")]
        assert previews, "Expected preview fix for missing basis"
        assert "def2-SVP" in json.dumps(previews[0]["edit"])

    def test_malformed_maxcore_fix_preview(self) -> None:
        path = FIXTURES_DIR / "invalid" / "malformed_maxcore.inp"
        payload = operation_path(
            path,
            "fix",
            software="orca",
            file_type_func=lambda p: p.suffix.lstrip("."),
            collect_diagnostics=_collect_diagnostics,
        )
        previews = [action for action in payload["actions"] if action.get("preview_only")]
        assert previews
        assert "4000" in json.dumps(previews[0]["edit"])

    def test_charge_multiplicity_fix_refusal(self) -> None:
        path = FIXTURES_DIR / "invalid" / "charge_multiplicity_mismatch.inp"
        payload = operation_path(
            path,
            "fix",
            software="orca",
            file_type_func=lambda p: p.suffix.lstrip("."),
            collect_diagnostics=_collect_diagnostics,
        )
        refusals = [action for action in payload["actions"] if action.get("kind") == "refusal"]
        assert refusals
        assert refusals[0]["diagnostic_code"] == "ORCA-E007"
        assert "refusal_reason" in refusals[0]

    def test_missing_ecp_fix_refusal(self) -> None:
        path = FIXTURES_DIR / "invalid" / "missing_ecp.inp"
        payload = operation_path(
            path,
            "fix",
            software="orca",
            file_type_func=lambda p: p.suffix.lstrip("."),
            collect_diagnostics=_collect_diagnostics,
        )
        refusals = [action for action in payload["actions"] if action.get("kind") == "refusal"]
        codes = {item["diagnostic_code"] for item in refusals}
        assert "ORCA-E028" in codes

    def test_log_scf_fix_refusal_via_check(self) -> None:
        path = FIXTURES_DIR / "log" / "scf_convergence_failure.log"
        payload = operation_path(
            path,
            "fix",
            software="orca",
            file_type_func=lambda p: p.suffix.lstrip("."),
            collect_diagnostics=lambda p: check_path(p)["diagnostics"],
        )
        refusals = [action for action in payload["actions"] if action.get("kind") == "refusal"]
        assert any(item["diagnostic_code"] == "ORCA-E024" for item in refusals)
