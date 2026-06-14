from __future__ import annotations

import json
from pathlib import Path

import pytest

from orca_lsp import tool
from orca_lsp.preflight import (
    ALL_ROLES,
    CODE_KEYWORD_VERSION_MISMATCH,
    CODE_LOW_MAXITER,
    CODE_MISSING_BASIS_CONFIG,
    CODE_MISSING_GEOMETRY,
    CODE_UNRESOLVED_WFN_REFERENCE,
    CODE_VERSION_ASSUMPTION,
    DEFAULT_MAXITER_WARNING,
    ArtifactGraph,
    build_artifact_graph,
    fleet_manifest,
    resolve_version_assumption,
)
from orca_lsp.tool import (
    check_path,
    manifest_path,
    preflight_path,
)

FIXTURES = Path(__file__).parent / "fixtures" / "preflight"

# Envelope fields the issue acceptance criteria require on failing fixtures.
REQUIRED_FAILING_FIELDS = {
    "code",
    "severity",
    "path",
    "range",
    "blocking",
    "category",
    "source_provenance",
}


def _envelope_codes(payload: dict) -> set[str]:
    return {item["code"] for item in payload["diagnostics"]}


# --- Envelope shape --------------------------------------------------------


def test_agent_check_payload_carries_diagnostic_envelope_v1(capsys) -> None:
    # exercise the real CLI path so the capabilities block is attached
    rc = tool.main(["check", str(FIXTURES / "basis_missing")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["diagnostic_engine"] == "1.0"
    assert payload["software"] == "orca"
    # capabilities block is attached by the CLI wrapper
    assert payload["capabilities"]["operation"] == "check"
    # version assumption is surfaced at top level so the parent probe can branch
    assert "version_assumption" in payload
    assert payload["version_assumption"]["software"] == "orca"
    # cross-artifact graph is serialized for the fleet report workflow
    assert isinstance(payload.get("artifacts"), list)
    assert payload["artifacts"]


def test_failing_diagnostics_carry_required_envelope_fields() -> None:
    payload = preflight_path(FIXTURES / "basis_missing")
    failing = [item for item in payload["diagnostics"] if item["code"] == CODE_MISSING_BASIS_CONFIG]
    assert failing, "basis_missing fixture must emit ORCA606"
    item = failing[0]
    for field in REQUIRED_FAILING_FIELDS:
        assert field in item, f"missing required envelope field: {field}"
    # Richer envelope fields used by the parent fleet probe
    assert item["confidence"] >= 0.0
    assert "actions" in item and item["actions"]
    assert "fix_hints" in item and item["fix_hints"]
    assert "facts" in item
    assert item["facts"]["has_basis_block"] is False
    assert "artifact_roles" in item
    # range is a proper LSP-style start/end object
    assert item["range"]["start"]["line"] >= 0
    assert "character" in item["range"]["start"]


# --- Fixture behavior ------------------------------------------------------


@pytest.mark.parametrize(
    "fixture, expected_ok, must_include, must_exclude_blocking",
    [
        ("valid_sp", True, set(), set()),
        ("basis_missing", False, {CODE_MISSING_BASIS_CONFIG}, set()),
        ("keyword_method_mismatch", False, {CODE_KEYWORD_VERSION_MISMATCH}, set()),
        ("low_maxiter", True, {CODE_LOW_MAXITER}, set()),
        ("missing_geometry", False, {CODE_MISSING_GEOMETRY}, set()),
        ("unresolved_moinp", True, {CODE_UNRESOLVED_WFN_REFERENCE}, set()),
    ],
)
def test_preflight_fixture_expectations(
    fixture: str,
    expected_ok: bool,
    must_include: set[str],
    must_exclude_blocking: set[str],
) -> None:
    payload = preflight_path(FIXTURES / fixture)
    codes = _envelope_codes(payload)
    assert (
        payload["ok"] is expected_ok
    ), f"{fixture}: expected ok={expected_ok}, got codes={sorted(codes)}"
    assert must_include <= codes, f"{fixture}: expected codes {must_include}, got {sorted(codes)}"
    blocking_codes = {item["code"] for item in payload["diagnostics"] if item["blocking"]}
    assert not (must_exclude_blocking & blocking_codes)


def test_valid_sp_fixture_has_no_blocking_or_error_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "valid_sp")
    assert payload["summary"]["errors"] == 0
    assert payload["summary"]["blocking"] == 0
    # valid fixture must not carry the preflight error codes
    error_codes = {
        CODE_MISSING_GEOMETRY,
        CODE_MISSING_BASIS_CONFIG,
        CODE_KEYWORD_VERSION_MISMATCH,
    }
    assert not (_envelope_codes(payload) & error_codes)


def test_low_maxiter_is_non_blocking_warning_with_threshold_fact() -> None:
    payload = preflight_path(FIXTURES / "low_maxiter")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_LOW_MAXITER)
    assert item["severity"] == "warning"
    assert item["blocking"] is False
    assert item["facts"]["maxiter"] == 10
    assert item["facts"]["threshold"] == DEFAULT_MAXITER_WARNING


def test_low_maxiter_intent_override_changes_threshold(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "tight.inp").write_text(
        "! B3LYP def2-TZVP SP\n"
        "%scf\n  maxiter 40\nend\n"
        "* xyz 0 1\n  O 0 0 0\n  H 0.7 0.5 0\n  H -0.7 0.5 0\n*\n",
        encoding="utf-8",
    )
    # No intent: default threshold 50 -> maxiter 40 is below -> warning fires.
    base = preflight_path(case)
    assert CODE_LOW_MAXITER in _envelope_codes(base)

    cfg = case / ".orca-lsp"
    cfg.mkdir()
    (cfg / "intent.json").write_text(json.dumps({"scf_maxiter_warning": 30}), encoding="utf-8")
    overridden = preflight_path(case)
    assert CODE_LOW_MAXITER not in _envelope_codes(overridden)


# --- version-aware-keywords ------------------------------------------------


def test_version_assumption_unknown_when_intent_absent() -> None:
    assumption = resolve_version_assumption(None)
    assert assumption["exact_runtime_known"] is False
    assert assumption["declared_by"] == "fallback"
    assert assumption["software_version"] == "unknown"


def test_version_assumption_known_when_intent_declares_version() -> None:
    assumption = resolve_version_assumption(
        {"software_version": "orca >=5.0", "runtime_image": "img:5.0"}
    )
    assert assumption["exact_runtime_known"] is True
    assert assumption["declared_by"] == "intent"
    assert assumption["software_version"] == "orca >=5.0"


def test_version_assumption_information_diagnostic_when_unknown(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "water.inp").write_text(
        "! B3LYP def2-TZVP SP\n"
        "%maxcore 4000\n"
        "* xyz 0 1\n  O 0 0 0\n  H 0.7 0.5 0\n  H -0.7 0.5 0\n*\n",
        encoding="utf-8",
    )
    payload = preflight_path(case)
    item = next(
        (d for d in payload["diagnostics"] if d["code"] == CODE_VERSION_ASSUMPTION),
        None,
    )
    assert item is not None
    assert item["severity"] == "information"
    assert item["blocking"] is False
    assert item["version_assumption"]["exact_runtime_known"] is False


def test_version_assumption_silent_when_intent_declares_version(tmp_path: Path) -> None:
    case = tmp_path / "case"
    case.mkdir()
    (case / "water.inp").write_text(
        "! B3LYP def2-TZVP SP\n"
        "%maxcore 4000\n"
        "* xyz 0 1\n  O 0 0 0\n  H 0.7 0.5 0\n  H -0.7 0.5 0\n*\n",
        encoding="utf-8",
    )
    cfg = case / ".orca-lsp"
    cfg.mkdir()
    (cfg / "intent.json").write_text(
        json.dumps({"software_version": "orca >=5.0"}), encoding="utf-8"
    )
    payload = preflight_path(case)
    assert CODE_VERSION_ASSUMPTION not in _envelope_codes(payload)
    assert payload["version_assumption"]["exact_runtime_known"] is True


def test_keyword_method_mismatch_carries_version_assumption() -> None:
    payload = preflight_path(FIXTURES / "keyword_method_mismatch")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_KEYWORD_VERSION_MISMATCH)
    assert item["facts"]["double_hybrid"] is True
    assert item["facts"]["explicit_mp2"] is True
    assert "version-aware" in item["domain_tags"]
    assert "version_assumption" in item


# --- cross-artifact-graph --------------------------------------------------


def test_artifact_graph_uses_generic_roles() -> None:
    from orca_lsp.parser import ORCAParser

    case_dir = (FIXTURES / "valid_sp").resolve()
    input_path = case_dir / "water.inp"
    text = input_path.read_text(encoding="utf-8")
    result = ORCAParser().parse(text)
    graph = build_artifact_graph(case_dir, input_path, result)
    roles = {node.role for node in graph.nodes}
    assert roles <= set(ALL_ROLES)
    # primary-input, simple-keywords, geometry are always present for a valid case
    for required in ("primary-input", "simple-keywords", "geometry"):
        assert graph.by_role(required), f"missing required role: {required}"
    # serialized graph is JSON-friendly and stable
    serialized = graph.to_json()
    assert isinstance(serialized, list)
    assert all("role" in node and "path" in node and "exists" in node for node in serialized)


def test_missing_geometry_records_primary_input_provenance() -> None:
    payload = preflight_path(FIXTURES / "missing_geometry")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_MISSING_GEOMETRY)
    prov = item["source_provenance"]
    assert prov["role"] == "geometry"
    assert prov["reason"].startswith("no '* xyz")


def test_unresolved_moinp_is_non_blocking_warning() -> None:
    payload = preflight_path(FIXTURES / "unresolved_moinp")
    item = next(d for d in payload["diagnostics"] if d["code"] == CODE_UNRESOLVED_WFN_REFERENCE)
    assert item["severity"] == "warning"
    assert item["blocking"] is False
    assert item["artifact_roles"] == ["wavefunction-reference"]


# --- code-actions / blocking gate -----------------------------------------


def test_check_fail_on_blocking_exits_nonzero_on_failing_fixture() -> None:
    rc = tool.main(["check", str(FIXTURES / "basis_missing"), "--fail-on-blocking"])
    assert rc == 1


def test_check_fail_on_blocking_exits_zero_on_valid_fixture(capsys) -> None:
    rc = tool.main(["check", str(FIXTURES / "valid_sp"), "--fail-on-blocking"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True


def test_preflight_subcommand_emits_envelope(capsys) -> None:
    rc = tool.main(["preflight", str(FIXTURES / "low_maxiter")])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["operation"] == "preflight"
    assert payload["diagnostic_envelope"] == "v1"
    assert payload["capabilities"]["operation"] == "preflight"


def test_actions_present_on_blocking_diagnostics() -> None:
    payload = preflight_path(FIXTURES / "basis_missing")
    blocking = [d for d in payload["diagnostics"] if d["blocking"]]
    assert blocking
    for item in blocking:
        assert item.get("actions"), f"blocking diagnostic {item['code']} must carry actions"
        assert all("kind" in action for action in item["actions"])


# --- fleet-regression-fixtures / manifest ---------------------------------


def test_manifest_lists_all_four_capabilities() -> None:
    manifest = manifest_path(FIXTURES / "valid_sp")
    capabilities = manifest["capabilities"]
    for cap in (
        "version-aware-keywords",
        "cross-artifact-graph",
        "code-actions",
        "fleet-regression-fixtures",
    ):
        assert cap in capabilities, f"missing capability: {cap}"
        assert capabilities[cap]["status"] == "available"
    # artifact roles are the generic fleet model, not MatMaster policy
    assert set(manifest["artifact_roles"]) == set(ALL_ROLES)
    assert manifest["preflight_envelope"] == "DiagnosticEnvelope/v1"


def test_manifest_without_path_still_describes_surface() -> None:
    manifest = manifest_path(None)
    assert set(manifest["codes"])
    assert manifest["capabilities"]["code-actions"]["blocking_gate"]


def test_manifest_merges_fixture_expectations() -> None:
    manifest = manifest_path(FIXTURES / "valid_sp")
    fixtures = manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]
    names = {item["name"] for item in fixtures}
    assert {
        "valid_sp",
        "basis_missing",
        "keyword_method_mismatch",
        "low_maxiter",
        "missing_geometry",
        "unresolved_moinp",
    } <= names


def test_fleet_manifest_helper_pure_data() -> None:
    manifest = fleet_manifest(fixtures=[{"name": "x", "expect_ok": True}])
    assert manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"] == [
        {"name": "x", "expect_ok": True}
    ]
    # every code entry is self-describing for the parent probe
    for body in manifest["codes"].values():
        assert body["severity"] in {"error", "warning", "information", "hint"}
        assert "capability" in body
        assert "summary" in body


def test_fixture_expectations_match_actual_preflight() -> None:
    """The fleet manifest's declared fixture expectations must match reality.

    This is the regression-evidence contract: the parent ``bohrium_skills``
    probe consumes the manifest and replays these fixtures, so the declared
    expectations have to agree with what the preflight actually emits.
    """
    manifest = manifest_path(FIXTURES / "valid_sp")
    repo_root = Path(__file__).resolve().parent.parent
    for fixture in manifest["capabilities"]["fleet-regression-fixtures"]["fixtures"]:
        payload = preflight_path(repo_root / fixture["path"])
        assert payload["ok"] is fixture["expect_ok"], (
            f"{fixture['name']}: manifest expects ok={fixture['expect_ok']}, "
            f"got ok={payload['ok']}"
        )
        if fixture["expect_codes"]:
            assert set(fixture["expect_codes"]) <= _envelope_codes(payload), (
                f"{fixture['name']}: expected codes {fixture['expect_codes']}, "
                f"got {sorted(_envelope_codes(payload))}"
            )


# --- workspace detection ---------------------------------------------------


def test_looks_like_workspace_requires_orca_input(tmp_path: Path) -> None:
    from orca_lsp.tool import _looks_like_workspace

    assert _looks_like_workspace(tmp_path) is False
    (tmp_path / "notes.txt").write_text("not an input", encoding="utf-8")
    assert _looks_like_workspace(tmp_path) is False
    (tmp_path / "water.inp").write_text("! B3LYP def2-TZVP SP\n", encoding="utf-8")
    assert _looks_like_workspace(tmp_path) is True


def test_check_on_single_input_file_does_not_run_preflight(tmp_path: Path) -> None:
    # A bare input file path must keep the legacy single-file behavior and
    # NOT flood with blocking missing-artifact preflight errors.
    input_path = tmp_path / "water.inp"
    input_path.write_text("! B3LYP def2-TZVP SP\n", encoding="utf-8")
    payload = check_path(input_path)
    preflight_codes = {
        CODE_MISSING_GEOMETRY,
        CODE_MISSING_BASIS_CONFIG,
        CODE_KEYWORD_VERSION_MISMATCH,
    }
    assert not (_envelope_codes(payload) & preflight_codes)


def test_check_on_full_workspace_merges_preflight() -> None:
    payload = check_path(FIXTURES / "basis_missing")
    codes = _envelope_codes(payload)
    assert CODE_MISSING_BASIS_CONFIG in codes
    assert payload["diagnostic_envelope"] == "v1"


def test_artifact_graph_is_json_serializable_for_fleet_report() -> None:
    payload = preflight_path(FIXTURES / "valid_sp")
    # artifacts must round-trip through json.dumps cleanly for the parent probe
    serialized = json.dumps(payload["artifacts"], sort_keys=True)
    assert "primary-input" in serialized
    assert "simple-keywords" in serialized
    assert "geometry" in serialized


def test_artifact_graph_class_smoke() -> None:
    graph = ArtifactGraph(case_dir=Path("/tmp"))
    assert graph.nodes == []
    assert graph.by_role("geometry") == []
    assert graph.to_json() == []
