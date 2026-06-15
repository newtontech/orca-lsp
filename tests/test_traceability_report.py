"""Tests for the OpenQC v1 docstring/wiki/raw traceability report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add the scripts directory to path so we can import the module
SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from generate_traceability_report import (  # type: ignore[import]  # noqa: E402
    SCHEMA_VERSION,
    SERVER_ID,
    REPOSITORY,
    LANGUAGE_ID,
    LEGACY_CODE_MAP,
    WIKI_METADATA,
    WIKI_TO_RAW,
    build_docstrings,
    build_wiki_sources,
    build_rule_ids,
    build_source_urls,
    build_raw_manifest,
    generate_report,
    validate_report,
    write_report,
    find_project_root,
)


@pytest.fixture(scope="module")
def project_root() -> Path:
    """Return the project root directory."""
    return find_project_root()


@pytest.fixture(scope="module")
def report(project_root: Path) -> dict:
    """Generate the full report once for all tests."""
    return generate_report(project_root)


class TestReportSchema:
    """Tests for the top-level report schema and field requirements."""

    def test_schema_version(self, report):
        assert report["schemaVersion"] == SCHEMA_VERSION

    def test_server_id(self, report):
        assert report["serverId"] == SERVER_ID

    def test_repository(self, report):
        assert report["repository"] == REPOSITORY

    def test_language_id(self, report):
        assert report["languageId"] == LANGUAGE_ID

    def test_generated_at_non_empty(self, report):
        assert report["generatedAt"]
        assert "T" in report["generatedAt"]
        assert report["generatedAt"].endswith("Z")

    def test_summary_has_counts(self, report):
        summary = report["summary"]
        assert "docstringsTotal" in summary
        assert "docstringsLinked" in summary
        assert "brokenWikiLinks" in summary
        assert "wikiSourcesWithoutRaw" in summary
        assert "rawManifestFailures" in summary

    def test_summary_counts_match_arrays(self, report):
        s = report["summary"]
        assert s["docstringsTotal"] == len(report["docstrings"])
        assert s["docstringsLinked"] == len(report["docstrings"])
        assert s["brokenWikiLinks"] == 0
        assert s["wikiSourcesWithoutRaw"] == 0
        assert s["rawManifestFailures"] == 0


class TestDocstrings:
    """Tests for the docstrings[] array."""

    def test_docstrings_non_empty(self, report):
        assert len(report["docstrings"]) > 0

    def test_docstrings_have_required_fields(self, report):
        for i, ds in enumerate(report["docstrings"]):
            assert ds.get("path"), f"docstrings[{i}].path is empty"
            assert ds.get("wikiPath"), f"docstrings[{i}].wikiPath is empty"
            assert ds.get("symbol"), f"docstrings[{i}].symbol is empty"

    def test_docstrings_paths_are_repo_relative(self, report):
        for ds in report["docstrings"]:
            assert ds["path"].startswith(
                "src/"
            ), f"path should be repo-relative, got {ds['path']!r}"

    def test_docstrings_wiki_paths_start_with_wiki(self, report):
        for ds in report["docstrings"]:
            assert ds["wikiPath"].startswith(
                "wiki/"
            ), f"wikiPath should start with wiki/, got {ds['wikiPath']!r}"

    def test_docstrings_wiki_paths_exist(self, report, project_root):
        for ds in report["docstrings"]:
            wiki_full = project_root / ds["wikiPath"]
            assert wiki_full.exists(), f"Wiki page not found: {wiki_full}"

    def test_docstrings_source_paths_exist(self, report, project_root):
        for ds in report["docstrings"]:
            src_full = project_root / ds["path"]
            assert src_full.exists(), f"Source file not found: {src_full}"

    def test_docstrings_no_duplicates(self, report):
        seen: set[tuple[str, str]] = set()
        for ds in report["docstrings"]:
            key = (ds["path"], ds["wikiPath"])
            assert key not in seen, f"Duplicate docstring entry: {key}"
            seen.add(key)


class TestWikiSources:
    """Tests for the wikiSources[] array."""

    def test_wiki_sources_non_empty(self, report):
        assert len(report["wikiSources"]) > 0

    def test_wiki_sources_have_required_fields(self, report):
        for i, ws in enumerate(report["wikiSources"]):
            assert ws.get("wikiPath"), f"wikiSources[{i}].wikiPath is empty"
            assert ws.get("rawPath"), f"wikiSources[{i}].rawPath is empty"
            assert ws.get("sourceUrl"), f"wikiSources[{i}].sourceUrl is empty"

    def test_wiki_sources_wiki_paths_start_with_wiki(self, report):
        for ws in report["wikiSources"]:
            assert ws["wikiPath"].startswith(
                "wiki/"
            ), f"wikiPath should start with wiki/, got {ws['wikiPath']!r}"

    def test_wiki_sources_raw_paths_start_with_raw(self, report):
        for ws in report["wikiSources"]:
            assert ws["rawPath"].startswith(
                "raw/"
            ), f"rawPath should start with raw/, got {ws['rawPath']!r}"

    def test_wiki_sources_wiki_paths_exist(self, report, project_root):
        for ws in report["wikiSources"]:
            wiki_full = project_root / ws["wikiPath"]
            assert wiki_full.exists(), f"Wiki page not found: {wiki_full}"

    def test_wiki_sources_raw_paths_exist(self, report, project_root):
        for ws in report["wikiSources"]:
            raw_full = project_root / ws["rawPath"]
            assert raw_full.exists(), f"Raw asset not found: {raw_full}"

    def test_wiki_sources_urls_are_valid_github(self, report):
        for ws in report["wikiSources"]:
            assert ws["sourceUrl"].startswith(
                REPOSITORY
            ), f"sourceUrl should start with {REPOSITORY}, got {ws['sourceUrl']!r}"
            assert "/blob/main/" in ws["sourceUrl"]

    def test_wiki_sources_no_duplicates(self, report):
        seen: set[str] = set()
        for ws in report["wikiSources"]:
            assert ws["rawPath"] not in seen, f"Duplicate wiki source entry: {ws['rawPath']}"
            seen.add(ws["rawPath"])


class TestRuleIds:
    """Tests for the ruleIds[] array."""

    CODE_PATTERN = r"^[A-Z]+-[A-Z]+-[A-Z]+-\d+$"

    def test_rule_ids_non_empty(self, report):
        assert len(report["ruleIds"]) > 0

    def test_rule_ids_have_required_fields(self, report):
        for i, ri in enumerate(report["ruleIds"]):
            assert ri.get("code"), f"ruleIds[{i}].code is empty"
            assert ri.get("sourcePath"), f"ruleIds[{i}].sourcePath is empty"

    def test_rule_ids_code_format(self, report):
        for i, ri in enumerate(report["ruleIds"]):
            code = ri["code"]
            assert (
                len(code.split("-")) >= 4
            ), f"ruleIds[{i}].code {code!r} should have at least 4 parts"
            assert ri.get("sourcePath", "").startswith("src/"), (
                f"ruleIds[{i}].sourcePath should be repo-relative, "
                f"got {ri.get('sourcePath', '')!r}"
            )

    def test_rule_ids_no_duplicates(self, report):
        seen: set[str] = set()
        for ri in report["ruleIds"]:
            assert ri["code"] not in seen, f"Duplicate rule ID code: {ri['code']}"
            seen.add(ri["code"])

    def test_rule_ids_count_matches_legacy_map(self, report):
        # All legacy codes should be mapped
        mapped = set(LEGACY_CODE_MAP.values())
        reported = {ri["code"] for ri in report["ruleIds"]}
        assert reported == mapped, (
            f"Reported codes differ from LEGACY_CODE_MAP\n"
            f"Missing: {mapped - reported}\n"
            f"Extra: {reported - mapped}"
        )

    def test_rule_ids_source_paths_exist(self, report, project_root):
        for ri in report["ruleIds"]:
            src_full = project_root / ri["sourcePath"]
            assert src_full.exists(), f"Source file not found: {src_full}"


class TestSourceUrls:
    """Tests for the sourceUrls[] array."""

    def test_source_urls_non_empty(self, report):
        assert len(report["sourceUrls"]) > 0

    def test_source_urls_have_required_fields(self, report):
        for i, su in enumerate(report["sourceUrls"]):
            assert su.get("rawPath"), f"sourceUrls[{i}].rawPath is empty"
            assert su.get("url"), f"sourceUrls[{i}].url is empty"

    def test_source_urls_raw_paths_start_with_raw(self, report):
        for su in report["sourceUrls"]:
            assert su["rawPath"].startswith(
                "raw/"
            ), f"rawPath should start with raw/, got {su['rawPath']!r}"

    def test_source_urls_raw_paths_exist(self, report, project_root):
        for su in report["sourceUrls"]:
            raw_full = project_root / su["rawPath"]
            assert raw_full.exists(), f"Raw asset not found: {raw_full}"

    def test_source_urls_are_valid_github(self, report):
        for su in report["sourceUrls"]:
            assert su["url"].startswith(REPOSITORY)
            assert "/blob/main/" in su["url"]

    def test_source_urls_no_duplicates(self, report):
        seen: set[str] = set()
        for su in report["sourceUrls"]:
            assert su["rawPath"] not in seen, f"Duplicate source URL entry: {su['rawPath']}"
            seen.add(su["rawPath"])


class TestRawManifest:
    """Tests for the rawManifest object."""

    def test_raw_manifest_non_empty(self, report):
        assert len(report["rawManifest"]) > 0

    def test_raw_manifest_path_is_repo_relative(self, report):
        manifest_path = report["rawManifest"]["path"]
        assert manifest_path.startswith(
            "raw/assets/"
        ), f"rawManifest.path should start with raw/assets/, got {manifest_path!r}"

    def test_raw_manifest_ok_is_boolean(self, report):
        ok_val = report["rawManifest"]["ok"]
        assert isinstance(ok_val, bool), f"rawManifest.ok should be bool, got {type(ok_val).__name__}"

    def test_raw_manifest_paths_exist(self, report, project_root):
        full_path = project_root / report["rawManifest"]["path"]
        assert full_path.exists(), f"Raw manifest not found: {full_path}"

    def test_raw_manifest_all_ok(self, report):
        assert report["rawManifest"]["ok"] is True

    def test_raw_manifest_consistent_with_source_urls(self, report):
        manifest_paths = {report["rawManifest"]["path"]}
        source_url_paths = {su["rawPath"] for su in report["sourceUrls"]}
        assert manifest_paths <= source_url_paths


class TestBuilderFunctions:
    """Tests for individual builder functions."""

    def test_build_docstrings_returns_list_of_dicts(self, project_root):
        result = build_docstrings(project_root)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)

    def test_build_wiki_sources_returns_list_of_dicts(self, project_root):
        result = build_wiki_sources(project_root)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)

    def test_build_rule_ids_returns_list_of_dicts(self, project_root):
        result = build_rule_ids(project_root)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)

    def test_build_source_urls_returns_list_of_dicts(self, project_root):
        result = build_source_urls(project_root)
        assert isinstance(result, list)
        if result:
            assert isinstance(result[0], dict)

    def test_build_raw_manifest_returns_dict(self, project_root):
        result = build_raw_manifest(project_root)
        assert isinstance(result, dict)


class TestValidation:
    """Tests for the report validation function."""

    def test_valid_report_passes(self, report):
        errors = validate_report(report)
        assert errors == [], f"Validation errors: {errors}"

    def test_validation_fails_missing_field(self):
        report = {}
        errors = validate_report(report)
        assert len(errors) > 0
        assert any("schemaVersion" in e for e in errors)

    def test_validation_fails_wrong_schema_version(self, report):
        bad_report = dict(report)
        bad_report["schemaVersion"] = "wrong"
        errors = validate_report(bad_report)
        assert any("schemaVersion" in e for e in errors)

    def test_validation_fails_empty_docstrings(self, report):
        bad_report = dict(report)
        bad_report["docstrings"] = []
        errors = validate_report(bad_report)
        assert any("non-empty" in e.lower() for e in errors)

    def test_validation_fails_empty_wiki_sources(self, report):
        bad_report = dict(report)
        bad_report["wikiSources"] = []
        errors = validate_report(bad_report)
        assert any("non-empty" in e.lower() for e in errors)

    def test_validation_fails_empty_rule_ids(self, report):
        bad_report = dict(report)
        bad_report["ruleIds"] = []
        errors = validate_report(bad_report)
        assert any("non-empty" in e.lower() for e in errors)

    def test_validation_fails_empty_source_urls(self, report):
        bad_report = dict(report)
        bad_report["sourceUrls"] = []
        errors = validate_report(bad_report)
        assert any("non-empty" in e.lower() for e in errors)

    def test_validation_fails_empty_raw_manifest(self, report):
        bad_report = dict(report)
        bad_report["rawManifest"] = {}
        errors = validate_report(bad_report)
        assert any("non-empty" in e.lower() for e in errors)

    def test_validation_fails_docstring_missing_path(self, report):
        bad_report = dict(report)
        bad_report["docstrings"] = [{"wikiPath": "x", "symbol": "y"}]
        errors = validate_report(bad_report)
        assert any("path" in e.lower() for e in errors)

    def test_validation_fails_rule_id_bad_format(self, report):
        bad_report = dict(report)
        bad_report["ruleIds"] = [{"code": "BAD", "sourcePath": "x.py"}]
        errors = validate_report(bad_report)
        assert any("pattern" in e.lower() or "match" in e.lower() for e in errors)

    def test_validation_fails_raw_manifest_non_bool(self, report):
        bad_report = dict(report)
        bad_report["rawManifest"] = {"path": "raw/assets/manifest.json", "ok": "not_bool"}
        errors = validate_report(bad_report)
        assert any("boolean" in e.lower() for e in errors)


class TestWriteAndReread:
    """Tests for report serialization/deserialization round-trip."""

    def test_write_and_validate(self, report, project_root, tmp_path):
        output = tmp_path / "test-report.json"
        write_report(report, output)
        assert output.exists()
        reread = json.loads(output.read_text(encoding="utf-8"))
        errors = validate_report(reread)
        assert errors == [], f"Validation errors after round-trip: {errors}"

    def test_write_generated_report(self, project_root, tmp_path):
        """Test that generating and writing from scratch works."""
        output = tmp_path / "fresh-report.json"
        fresh = generate_report(project_root)
        write_report(fresh, output)
        assert output.exists()
        content = json.loads(output.read_text(encoding="utf-8"))
        assert content["schemaVersion"] == SCHEMA_VERSION


class TestWIKIMetadata:
    """Tests for the wiki metadata integrity."""

    def test_all_wiki_metadata_paths_exist(self, project_root):
        for wiki_rel in WIKI_METADATA:
            wiki_full = project_root / wiki_rel
            assert wiki_full.exists(), f"Wiki metadata path not found: {wiki_full}"

    def test_all_wiki_to_raw_exists(self, project_root):
        for raw_rel in WIKI_TO_RAW.values():
            raw_full = project_root / raw_rel
            assert raw_full.exists(), f"Wiki-to-raw path not found: {raw_full}"

    def test_all_wiki_metadata_have_symbols(self):
        for wiki_rel, meta in WIKI_METADATA.items():
            assert meta.get("symbol"), f"Missing symbol for {wiki_rel}"
            assert meta.get("sourceHints"), f"Missing sourceHints for {wiki_rel}"

    def test_all_wiki_metadata_have_source_path_in_wiki_to_raw(self):
        for wiki_rel in WIKI_METADATA:
            # Items under wiki/entities/ or wiki/concepts/ or wiki/synthesis/
            short = wiki_rel.removeprefix("wiki/")
            assert (
                short in WIKI_TO_RAW or wiki_rel == "wiki/provenance_report.md"
            ), f"Missing WIKI_TO_RAW mapping for {short}"
