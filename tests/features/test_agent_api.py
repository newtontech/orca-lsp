import json
import os
from pathlib import Path

import pytest
from lsprotocol.types import Diagnostic, DiagnosticSeverity, Position, Range

from orca_lsp.features.agent_api import (
    AgentAPIProvider,
    AgentAPISnapshot,
    ORCA_EXAMPLES,
    SECTION_PARAMETERS,
)

FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "capabilities"


def _load_fixture(name: str) -> dict:
    path = FIXTURES_DIR / name
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# Existing tests (kept for backward compatibility)
# ---------------------------------------------------------------------------


class TestSnapshot:
    def test_to_json(self) -> None:
        s = AgentAPISnapshot(uri="test", diagnostics=[{"line": 0}])
        assert json.loads(s.to_json())["uri"] == "test"

    def test_to_json_contains_all_fields(self) -> None:
        s = AgentAPISnapshot(uri="u", version=3, metadata={"k": "v"})
        data = json.loads(s.to_json())
        assert data["version"] == 3
        assert data["metadata"] == {"k": "v"}


class TestProviderExisting:
    def test_empty(self) -> None:
        snap = AgentAPIProvider().get_snapshot("")
        assert snap.diagnostics == []

    def test_with_diagnostics(self) -> None:
        diags = [
            Diagnostic(
                range=Range(start=Position(0, 0), end=Position(0, 0)),
                message="err",
                severity=DiagnosticSeverity.Error,
                source="test",
                code="X1",
            )
        ]
        snap = AgentAPIProvider().get_snapshot("test", diagnostics=diags)
        assert len(snap.diagnostics) == 1

    def test_outline(self) -> None:
        snap = AgentAPIProvider().get_outline_json("title test\n")
        assert "outline" in snap

    def test_metadata(self) -> None:
        snap = AgentAPIProvider().get_snapshot("test")
        assert snap.metadata["language"] == "orca"

    def test_diags_json(self) -> None:
        r = AgentAPIProvider().get_diagnostics_json("test")
        assert "count" in r


# ---------------------------------------------------------------------------
# #52 — describe_domain_language
# ---------------------------------------------------------------------------


class TestDescribeDomainLanguage:
    def test_returns_dict(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        assert isinstance(result, dict)

    def test_top_level_keys(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        assert "language" in result
        assert "version" in result
        assert "structure" in result
        assert "file_types" in result

    def test_language_name(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        assert result["language"] == "ORCA Input"

    def test_structure_sections(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        structure = result["structure"]
        assert "route_line" in structure
        assert "key_blocks" in structure
        assert "coordinate_sections" in structure
        assert "output_blocks" in structure

    def test_route_line(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        route = result["structure"]["route_line"]
        assert route["prefix"] == "!"
        assert "components" in route
        component_names = [c["name"] for c in route["components"]]
        assert "method" in component_names
        assert "basis_set" in component_names
        assert "job_type" in component_names

    def test_key_blocks(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        blocks = result["structure"]["key_blocks"]
        assert blocks["prefix"] == "%"
        block_names = [b["name"] for b in blocks["blocks"]]
        assert "scf" in block_names
        assert "pal" in block_names
        assert "mp2" in block_names

    def test_coordinate_formats(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        coord = result["structure"]["coordinate_sections"]
        format_names = [f["name"] for f in coord["formats"]]
        assert "xyz" in format_names
        assert "int" in format_names

    def test_output_files(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        output = result["structure"]["output_blocks"]
        extensions = [f["extension"] for f in output["files"]]
        assert ".out" in extensions
        assert ".gbw" in extensions
        assert ".hessian" in extensions

    def test_file_types(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        ft = result["file_types"]
        assert ".inp" in ft["input"]
        assert ".out" in ft["output"]
        assert ".molden" in ft["output"]

    def test_matches_fixture(self) -> None:
        result = AgentAPIProvider().describe_domain_language()
        fixture = _load_fixture("domain_language.json")
        assert result["language"] == fixture["language"]
        assert result["version"] == fixture["version"]
        route_component_names = [c["name"] for c in result["structure"]["route_line"]["components"]]
        assert set(route_component_names) == set(fixture["structure"]["route_line"]["components"])


# ---------------------------------------------------------------------------
# #53 — lookup_section / lookup_keyword
# ---------------------------------------------------------------------------


class TestLookupSection:
    def test_lookup_scf(self) -> None:
        result = AgentAPIProvider().lookup_section("scf")
        assert result["found"] is True
        assert result["section"] == "scf"
        assert "description" in result
        assert "example" in result

    def test_lookup_scf_parameters(self) -> None:
        result = AgentAPIProvider().lookup_section("scf")
        assert "parameters" in result
        params = result["parameters"]
        assert "MaxIter" in params
        assert "Convergence" in params
        assert params["MaxIter"]["type"] == "integer"

    def test_lookup_pal(self) -> None:
        result = AgentAPIProvider().lookup_section("pal")
        assert result["found"] is True
        assert "nprocs" in result["parameters"]

    def test_lookup_mp2(self) -> None:
        result = AgentAPIProvider().lookup_section("mp2")
        assert result["found"] is True
        assert "RI" in result["parameters"]

    def test_lookup_nonexistent(self) -> None:
        result = AgentAPIProvider().lookup_section("nonexistent_block")
        assert result["found"] is False

    def test_case_insensitive(self) -> None:
        result = AgentAPIProvider().lookup_section("SCF")
        assert result["found"] is True

    def test_whitespace_handling(self) -> None:
        result = AgentAPIProvider().lookup_section("  scf  ")
        assert result["found"] is True

    def test_matches_fixture(self) -> None:
        fixture = _load_fixture("section_lookup.json")
        for section_key, expected in fixture.items():
            result = AgentAPIProvider().lookup_section(section_key)
            assert result["found"] == expected["found"]
            if expected["found"]:
                assert set(result["parameters"].keys()) == set(expected["parameters"])


class TestLookupKeyword:
    def test_lookup_scf_maxiter(self) -> None:
        result = AgentAPIProvider().lookup_keyword("scf", "MaxIter")
        assert result["found"] is True
        assert result["keyword"] == "MaxIter"
        assert result["definition"]["type"] == "integer"
        assert result["definition"]["min"] == 1

    def test_lookup_scf_convergence(self) -> None:
        result = AgentAPIProvider().lookup_keyword("scf", "Convergence")
        assert result["found"] is True
        assert result["definition"]["type"] == "enum"
        assert "Tight" in result["definition"]["values"]

    def test_lookup_pal_nprocs(self) -> None:
        result = AgentAPIProvider().lookup_keyword("pal", "nprocs")
        assert result["found"] is True
        assert result["definition"]["type"] == "integer"

    def test_case_insensitive_keyword(self) -> None:
        result = AgentAPIProvider().lookup_keyword("scf", "maxiter")
        assert result["found"] is True

    def test_not_found(self) -> None:
        result = AgentAPIProvider().lookup_keyword("scf", "nonexistent")
        assert result["found"] is False
        assert "message" in result

    def test_unknown_section(self) -> None:
        result = AgentAPIProvider().lookup_keyword("unknown", "anything")
        assert result["found"] is False

    def test_matches_fixture(self) -> None:
        fixture = _load_fixture("keyword_lookup.json")
        for key, expected in fixture.items():
            parts = key.split("_", 1)
            section, keyword = parts[0], parts[1]
            result = AgentAPIProvider().lookup_keyword(section, keyword)
            assert result["found"] == expected["found"]
            if expected["found"]:
                assert result["definition"]["type"] == expected["type"]


# ---------------------------------------------------------------------------
# #54 — get_examples / next_token_suggestions
# ---------------------------------------------------------------------------


class TestGetExamples:
    def test_returns_list(self) -> None:
        result = AgentAPIProvider().get_examples()
        assert isinstance(result, list)

    def test_count(self) -> None:
        result = AgentAPIProvider().get_examples()
        assert len(result) == 6

    def test_expected_keys(self) -> None:
        result = AgentAPIProvider().get_examples()
        keys = [ex["key"] for ex in result]
        assert "single_point" in keys
        assert "optimization" in keys
        assert "frequency" in keys
        assert "td_dft" in keys
        assert "mp2" in keys
        assert "ccsd" in keys

    def test_each_example_has_required_fields(self) -> None:
        for ex in AgentAPIProvider().get_examples():
            assert "key" in ex
            assert "title" in ex
            assert "description" in ex
            assert "input" in ex
            assert len(ex["input"]) > 0

    def test_single_point_example(self) -> None:
        result = AgentAPIProvider().get_examples()
        sp = [ex for ex in result if ex["key"] == "single_point"][0]
        assert "! B3LYP" in sp["input"]
        assert "* xyz" in sp["input"]

    def test_optimization_example(self) -> None:
        result = AgentAPIProvider().get_examples()
        opt = [ex for ex in result if ex["key"] == "optimization"][0]
        assert "! OPT" in opt["input"]
        assert "FREQ" in opt["input"]

    def test_td_dft_example(self) -> None:
        result = AgentAPIProvider().get_examples()
        td = [ex for ex in result if ex["key"] == "td_dft"][0]
        assert "TD-DFT" in td["input"] or "tddft" in td["input"].lower()

    def test_mp2_example(self) -> None:
        result = AgentAPIProvider().get_examples()
        mp2 = [ex for ex in result if ex["key"] == "mp2"][0]
        assert "MP2" in mp2["input"]

    def test_ccsd_example(self) -> None:
        result = AgentAPIProvider().get_examples()
        ccsd = [ex for ex in result if ex["key"] == "ccsd"][0]
        assert "CCSD" in ccsd["input"]

    def test_matches_fixture(self) -> None:
        fixture = _load_fixture("examples.json")
        result = AgentAPIProvider().get_examples()
        keys = [ex["key"] for ex in result]
        assert set(keys) == set(fixture["expected_keys"])
        assert len(result) == fixture["count"]


class TestNextTokenSuggestions:
    def test_after_bang_returns_suggestions(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("! ")
        assert len(result) > 0

    def test_after_bang_includes_functionals(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("! ")
        types = {item["type"] for item in result}
        assert "functional" in types

    def test_after_bang_includes_methods(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("! ")
        types = {item["type"] for item in result}
        assert "method" in types

    def test_after_bang_includes_basis_sets(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("! ")
        types = {item["type"] for item in result}
        assert "basis_set" in types

    def test_after_bang_includes_job_types(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("! ")
        types = {item["type"] for item in result}
        assert "job_type" in types

    def test_after_bang_with_prefix(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("! ", prefix="B3")
        tokens = [item["token"] for item in result]
        assert "B3LYP" in tokens
        # Should not include unrelated functionals
        for token in tokens:
            assert token.upper().startswith("B3")

    def test_after_percent_returns_blocks(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("% ")
        assert len(result) > 0
        types = {item["type"] for item in result}
        assert "block" in types

    def test_after_percent_specific_block(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("%sc")
        tokens = [item["token"] for item in result]
        assert "scf" in tokens

    def test_in_coordinates_returns_elements(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("O ")
        assert len(result) > 0
        types = {item["type"] for item in result}
        assert "element" in types

    def test_element_suggestion_filtering(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("C ", prefix="C")
        tokens = [item["token"] for item in result]
        assert "C" in tokens
        assert "Ca" in tokens
        for token in tokens:
            assert token.upper().startswith("C")

    def test_empty_context_returns_empty(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("")
        assert result == []

    def test_unknown_context_returns_empty(self) -> None:
        result = AgentAPIProvider().next_token_suggestions("random text")
        assert result == []


# ---------------------------------------------------------------------------
# #59 — get_code_intelligence_api
# ---------------------------------------------------------------------------


class TestGetCodeIntelligenceApi:
    def test_returns_dict(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        assert isinstance(result, dict)

    def test_top_level_fields(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        assert result["name"] == "orca-lsp"
        assert result["version"] == "1.0.0"
        assert result["language"] == "orca"

    def test_capabilities(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        caps = result["capabilities"]
        expected_caps = [
            "diagnostics",
            "completions",
            "navigation",
            "formatting",
            "rename",
            "hover",
            "domain_knowledge",
            "validation",
        ]
        for cap in expected_caps:
            assert cap in caps, f"Missing capability: {cap}"
            assert "description" in caps[cap]

    def test_diagnostics_capability(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        diag = result["capabilities"]["diagnostics"]
        assert "methods" in diag
        assert "checks" in diag
        assert len(diag["checks"]) > 0

    def test_completions_capability(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        comp = result["capabilities"]["completions"]
        assert "methods" in comp
        assert "next_token_suggestions" in comp["methods"]

    def test_api_methods(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        methods = result["api_methods"]
        method_names = [m["name"] for m in methods]
        assert "describe_domain_language" in method_names
        assert "lookup_section" in method_names
        assert "lookup_keyword" in method_names
        assert "get_examples" in method_names
        assert "next_token_suggestions" in method_names
        assert "get_code_intelligence_api" in method_names
        assert "validate_input" in method_names
        assert "dry_run_options" in method_names

    def test_each_method_has_description_and_params(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        for method in result["api_methods"]:
            assert "name" in method
            assert "description" in method
            assert "parameters" in method

    def test_agent_integration(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        integration = result["agent_integration"]
        assert "snapshot_usage" in integration
        assert "completion_usage" in integration
        assert "domain_usage" in integration

    def test_matches_fixture(self) -> None:
        result = AgentAPIProvider().get_code_intelligence_api()
        fixture = _load_fixture("code_intelligence_api.json")
        assert result["name"] == fixture["name"]
        assert result["version"] == fixture["version"]
        assert result["language"] == fixture["language"]
        assert len(result["api_methods"]) == fixture["api_method_count"]


# ---------------------------------------------------------------------------
# #60 — validate_input / dry_run_options
# ---------------------------------------------------------------------------

VALID_WATER_INPUT = (
    "! B3LYP def2-TZVP TightSCF\n"
    "%maxcore 4000\n"
    "\n"
    "* xyz 0 1\n"
    "  O   0.0000   0.0000   0.1173\n"
    "  H   0.0000   0.7572  -0.4692\n"
    "  H   0.0000  -0.7572  -0.4692\n"
    "*\n"
)

INVALID_INPUT_NO_METHOD = (
    "! def2-TZVP\n"
    "\n"
    "* xyz 0 1\n"
    "  O   0.0   0.0   0.0\n"
    "*\n"
)

INVALID_INPUT_NO_GEOMETRY = "! B3LYP def2-TZVP\n"


class TestValidateInput:
    def test_valid_input(self) -> None:
        result = AgentAPIProvider().validate_input(VALID_WATER_INPUT)
        assert isinstance(result, dict)
        assert result["valid"] is True
        assert result["error_count"] == 0
        assert result["errors"] == []

    def test_valid_input_has_sections(self) -> None:
        result = AgentAPIProvider().validate_input(VALID_WATER_INPUT)
        assert result["sections"]["has_simple_input"] is True
        assert result["sections"]["has_geometry"] is True

    def test_invalid_missing_method(self) -> None:
        result = AgentAPIProvider().validate_input(INVALID_INPUT_NO_METHOD)
        assert result["valid"] is False
        assert result["error_count"] >= 1
        messages = [e["message"] for e in result["errors"]]
        assert any("method" in m.lower() for m in messages)

    def test_invalid_missing_geometry(self) -> None:
        result = AgentAPIProvider().validate_input(INVALID_INPUT_NO_GEOMETRY)
        assert result["valid"] is False
        messages = [e["message"] for e in result["errors"]]
        assert any("geometry" in m.lower() or "Missing" in m for m in messages)

    def test_empty_input(self) -> None:
        result = AgentAPIProvider().validate_input("")
        assert result["valid"] is False
        assert result["error_count"] >= 1

    def test_warnings_for_missing_maxcore(self) -> None:
        result = AgentAPIProvider().validate_input("! B3LYP def2-TZVP\n\n* xyz 0 1\n  H 0 0 0\n*\n")
        # Should warn about missing maxcore
        warning_messages = [w["message"] for w in result["warnings"]]
        assert any("maxcore" in m.lower() for m in warning_messages)

    def test_returns_warning_count(self) -> None:
        result = AgentAPIProvider().validate_input(VALID_WATER_INPUT)
        assert "warning_count" in result
        assert isinstance(result["warning_count"], int)

    def test_matches_fixture(self) -> None:
        fixture = _load_fixture("validation.json")
        provider = AgentAPIProvider()
        valid_result = provider.validate_input(VALID_WATER_INPUT)
        assert valid_result["valid"] == fixture["valid_input"]["valid"]
        assert valid_result["error_count"] == fixture["valid_input"]["error_count"]


class TestDryRunOptions:
    def test_returns_dict(self) -> None:
        result = AgentAPIProvider().dry_run_options()
        assert isinstance(result, dict)

    def test_has_offline_validation(self) -> None:
        result = AgentAPIProvider().dry_run_options()
        assert "offline_validation" in result
        assert result["offline_validation"]["available"] is True
        assert result["offline_validation"]["requires_binary"] is False

    def test_has_binary_dry_run(self) -> None:
        result = AgentAPIProvider().dry_run_options()
        assert "binary_dry_run" in result
        assert result["binary_dry_run"]["requires_binary"] is True
        assert "config_fields" in result["binary_dry_run"]

    def test_has_log_parsing(self) -> None:
        result = AgentAPIProvider().dry_run_options()
        assert "log_parsing" in result
        assert result["log_parsing"]["available"] is True
        assert "ORCA-E024" in result["log_parsing"]["rule_codes"]

    def test_each_option_has_method_and_description(self) -> None:
        result = AgentAPIProvider().dry_run_options()
        for key, option in result.items():
            assert "method" in option
            assert "description" in option

    def test_matches_fixture(self) -> None:
        fixture = _load_fixture("validation.json")
        result = AgentAPIProvider().dry_run_options()
        assert set(result.keys()) == set(fixture["dry_run_options_keys"])


# ---------------------------------------------------------------------------
# #69 -- get_rule_manifest / openqc_smoke
# ---------------------------------------------------------------------------


class TestGetRuleManifest:
    def test_returns_list(self) -> None:
        result = AgentAPIProvider().get_rule_manifest()
        assert isinstance(result, list)

    def test_non_empty(self) -> None:
        result = AgentAPIProvider().get_rule_manifest()
        assert len(result) > 0

    def test_each_rule_has_required_fields(self) -> None:
        for rule in AgentAPIProvider().get_rule_manifest():
            assert "code" in rule, f"Missing 'code' in rule: {rule}"
            assert "severity" in rule, f"Missing 'severity' in rule: {rule}"
            assert "description" in rule, f"Missing 'description' in rule: {rule}"

    def test_codes_are_unique(self) -> None:
        result = AgentAPIProvider().get_rule_manifest()
        codes = [r["code"] for r in result]
        assert len(codes) == len(set(codes)), "Duplicate rule codes found"

    def test_severity_values(self) -> None:
        valid_severities = {"error", "warning", "information", "hint"}
        for rule in AgentAPIProvider().get_rule_manifest():
            assert rule["severity"] in valid_severities, f"Invalid severity: {rule['severity']}"

    def test_includes_lint_rules(self) -> None:
        result = AgentAPIProvider().get_rule_manifest()
        codes = {r["code"] for r in result}
        assert "ORCA-E001" in codes
        assert "ORCA-E002" in codes
        assert "ORCA-W001" in codes
        assert "ORCA-W020" in codes

    def test_includes_log_rules(self) -> None:
        result = AgentAPIProvider().get_rule_manifest()
        codes = {r["code"] for r in result}
        assert "ORCA-E024" in codes
        assert "ORCA-E025" in codes

    def test_matches_fixture_count(self) -> None:
        fixture = _load_fixture("openqc_smoke.json")
        result = AgentAPIProvider().get_rule_manifest()
        assert len(result) == fixture["expected_rule_count"]

    def test_matches_fixture_log_codes(self) -> None:
        fixture = _load_fixture("openqc_smoke.json")
        result = AgentAPIProvider().get_rule_manifest()
        log_codes = {r["code"] for r in result if r["code"].startswith("ORCA-E02")}
        for code in fixture["log_rule_codes"]:
            assert code in log_codes


class TestOpenqcSmoke:
    def test_returns_dict(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        assert isinstance(result, dict)

    def test_has_ok_flag(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        assert "ok" in result
        assert isinstance(result["ok"], bool)

    def test_has_checks_list(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        assert "checks" in result
        assert isinstance(result["checks"], list)

    def test_has_message(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        assert "message" in result
        assert isinstance(result["message"], str)

    def test_all_checks_pass(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        assert result["ok"] is True, (
            f"Smoke failed: {[c for c in result['checks'] if not c['ok']]}"
        )

    def test_check_names_match_fixture(self) -> None:
        fixture = _load_fixture("openqc_smoke.json")
        result = AgentAPIProvider().openqc_smoke()
        check_names = [c["name"] for c in result["checks"]]
        assert set(check_names) == set(fixture["smoke_checks"])

    def test_each_check_has_name_ok_detail(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        for check in result["checks"]:
            assert "name" in check
            assert "ok" in check
            assert "detail" in check

    def test_message_on_pass(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        if result["ok"]:
            assert "passed" in result["message"].lower()
        else:
            assert "fail" in result["message"].lower()

    def test_rule_manifest_check_present(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        manifest_check = [c for c in result["checks"] if c["name"] == "rule_manifest"]
        assert len(manifest_check) == 1
        assert manifest_check[0]["ok"] is True

    def test_lint_engine_valid_check(self) -> None:
        result = AgentAPIProvider().openqc_smoke()
        lint_check = [c for c in result["checks"] if c["name"] == "lint_engine_valid"]
        assert len(lint_check) == 1
        assert lint_check[0]["ok"] is True
