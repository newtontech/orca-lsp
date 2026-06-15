#!/usr/bin/env python3
"""OpenQC v1 docstring/wiki/raw traceability report generator.

Produces reports/docstring-wiki-raw-traceability.json satisfying the
openqc.lsp.traceability.v1 schema.  The report maps:
  - Source docstrings → wiki pages (docstrings[])
  - Wiki pages → raw assets (wikiSources[])
  - Diagnostic rule codes → rule metadata (ruleIds[])
  - Raw assets → GitHub source URLs (sourceUrls[])
  - All raw assets → ok status (rawManifest)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "openqc.lsp.traceability.v1"
SERVER_ID = "orca-lsp"
REPOSITORY = "https://github.com/newtontech/orca-lsp"
LANGUAGE_ID = "orca"

BACKEND = "ORCA"
FILE_ROLE = "INPUT"

# ── Existing code → OpenQC format mapping ────────────────────────────────────
# Existing rules use codes like ORCA-E001, TC-W001.
# We map them to <BACKEND>-<FILE_ROLE>-<CATEGORY>-NNN format.
LEGACY_CODE_MAP: dict[str, str] = {
    # ORCA lint rules
    "ORCA-E001": f"{BACKEND}-{FILE_ROLE}-SYNTAX-001",
    "ORCA-E002": f"{BACKEND}-{FILE_ROLE}-SYNTAX-002",
    "ORCA-E003": f"{BACKEND}-{FILE_ROLE}-SYNTAX-003",
    "ORCA-E004": f"{BACKEND}-{FILE_ROLE}-SYNTAX-004",
    "ORCA-E005": f"{BACKEND}-{FILE_ROLE}-VALIDATION-001",
    "ORCA-E006": f"{BACKEND}-{FILE_ROLE}-VALIDATION-002",
    "ORCA-E007": f"{BACKEND}-{FILE_ROLE}-VALIDATION-003",
    "ORCA-E020": f"{BACKEND}-{FILE_ROLE}-SYNTAX-020",
    "ORCA-E021": f"{BACKEND}-{FILE_ROLE}-VALIDATION-020",
    "ORCA-E022": f"{BACKEND}-{FILE_ROLE}-SYNTAX-021",
    "ORCA-E023": f"{BACKEND}-{FILE_ROLE}-SYNTAX-022",
    "ORCA-E027": f"{BACKEND}-{FILE_ROLE}-SYNTAX-023",
    "ORCA-E028": f"{BACKEND}-{FILE_ROLE}-SYNTAX-024",
    "ORCA-W001": f"{BACKEND}-{FILE_ROLE}-CONFIG-001",
    "ORCA-W002": f"{BACKEND}-{FILE_ROLE}-SYNTAX-050",
    "ORCA-W003": f"{BACKEND}-{FILE_ROLE}-SYNTAX-051",
    "ORCA-W004": f"{BACKEND}-{FILE_ROLE}-CONFIG-002",
    "ORCA-W005": f"{BACKEND}-{FILE_ROLE}-CONFIG-003",
    "ORCA-W020": f"{BACKEND}-{FILE_ROLE}-CONFIG-020",
    "ORCA-W021": f"{BACKEND}-{FILE_ROLE}-CONFIG-021",
    # Typecheck rules
    "TC-E001": f"{BACKEND}-{FILE_ROLE}-TYPE-001",
    "TC-E002": f"{BACKEND}-{FILE_ROLE}-TYPE-002",
    "TC-E003": f"{BACKEND}-{FILE_ROLE}-TYPE-003",
    "TC-W001": f"{BACKEND}-{FILE_ROLE}-SCHEMA-001",
    "TC-W002": f"{BACKEND}-{FILE_ROLE}-SCHEMA-002",
    "TC-W003": f"{BACKEND}-{FILE_ROLE}-TYPE-004",
}

# ── Wiki page metadata ───────────────────────────────────────────────────────
WIKI_METADATA: dict[str, dict[str, Any]] = {
    "wiki/entities/ORCA_Quantum_Chemistry.md": {
        "symbol": "ORCA_Quantum_Chemistry",
        "sourceHints": ["ORCA quantum chemistry", "ORCA LSP", "orca-lsp"],
    },
    "wiki/entities/Language_Server_Protocol.md": {
        "symbol": "Language_Server_Protocol",
        "sourceHints": ["Language Server Protocol", "LSP", "language server"],
    },
    "wiki/entities/Diagnostic_Engine_v1.md": {
        "symbol": "Diagnostic_Engine_v1",
        "sourceHints": [
            "diagnostic",
            "Diagnostic Engine",
            "rich_diagnostics",
            "diagnostic_to_dict",
        ],
    },
    "wiki/entities/OpenQC_Alignment.md": {
        "symbol": "OpenQC_Alignment",
        "sourceHints": ["OpenQC", "alignment"],
    },
    "wiki/entities/DFT_Functionals.md": {
        "symbol": "DFT_Functionals",
        "sourceHints": ["DFT", "functional", "density functional", "DFT_FUNCTIONALS"],
    },
    "wiki/entities/Basis_Sets.md": {
        "symbol": "Basis_Sets",
        "sourceHints": ["basis set", "BASIS_SETS"],
    },
    "wiki/entities/Job_Types.md": {
        "symbol": "Job_Types",
        "sourceHints": ["job type", "JOB_TYPES"],
    },
    "wiki/entities/Percent_Blocks.md": {
        "symbol": "Percent_Blocks",
        "sourceHints": ["block", "PERCENT_BLOCKS", "% block"],
    },
    "wiki/entities/Wavefunction_Methods.md": {
        "symbol": "Wavefunction_Methods",
        "sourceHints": ["wavefunction", "WAVEFUNCTION_METHODS", "MP2", "CCSD"],
    },
    "wiki/entities/Element_Symbols.md": {
        "symbol": "Element_Symbols",
        "sourceHints": ["element", "ELEMENTS", "atom symbol"],
    },
    "wiki/entities/Geometry_Section.md": {
        "symbol": "Geometry_Section",
        "sourceHints": ["geometry", "coordinate", "xyz", "atom"],
    },
    "wiki/entities/ORCA_Official_Documentation.md": {
        "symbol": "ORCA_Official_Documentation",
        "sourceHints": ["ORCA manual", "documentation", "official"],
    },
    "wiki/entities/ORCA_GitHub_Tools.md": {
        "symbol": "ORCA_GitHub_Tools",
        "sourceHints": ["GitHub", "tools", "CI"],
    },
    "wiki/entities/Auxiliary_Basis_Sets.md": {
        "symbol": "Auxiliary_Basis_Sets",
        "sourceHints": ["auxiliary", "RI", "fitting", "def2/J"],
    },
    "wiki/concepts/Density_Functional_Theory.md": {
        "symbol": "Density_Functional_Theory",
        "sourceHints": ["DFT", "density functional theory", "functionals"],
    },
    "wiki/concepts/Basis_Set_Selection.md": {
        "symbol": "Basis_Set_Selection",
        "sourceHints": ["basis selection", "basis set choice"],
    },
    "wiki/concepts/Coupled_Cluster_Theory.md": {
        "symbol": "Coupled_Cluster_Theory",
        "sourceHints": ["coupled cluster", "CCSD", "DLPNO"],
    },
    "wiki/concepts/Dispersion_Corrections.md": {
        "symbol": "Dispersion_Corrections",
        "sourceHints": ["dispersion", "D3", "D4", "D3BJ"],
    },
    "wiki/concepts/DLPNO_Methods.md": {
        "symbol": "DLPNO_Methods",
        "sourceHints": ["DLPNO", "local pair", "domain-based"],
    },
    "wiki/concepts/Frequency_Calculation.md": {
        "symbol": "Frequency_Calculation",
        "sourceHints": ["frequency", "FREQ", "vibrational"],
    },
    "wiki/concepts/Geometry_Optimization.md": {
        "symbol": "Geometry_Optimization",
        "sourceHints": ["optimization", "OPT", "geometry opt"],
    },
    "wiki/concepts/Compound_Jobs.md": {
        "symbol": "Compound_Jobs",
        "sourceHints": ["compound", "job type", "OPT FREQ"],
    },
    "wiki/concepts/Solvation_Models.md": {
        "symbol": "Solvation_Models",
        "sourceHints": ["solvation", "CPCM", "SMD"],
    },
    "wiki/concepts/Time_Dependent_DFT.md": {
        "symbol": "Time_Dependent_DFT",
        "sourceHints": ["TDDFT", "time-dependent", "excited state"],
    },
    "wiki/concepts/Transition_State_Search.md": {
        "symbol": "Transition_State_Search",
        "sourceHints": ["transition state", "TS", "saddle point"],
    },
    "wiki/synthesis/Input_File_Guide.md": {
        "symbol": "Input_File_Guide",
        "sourceHints": ["input file", "inp file", "file format"],
    },
    "wiki/synthesis/ORCA_LSP_API_Reference.md": {
        "symbol": "ORCA_LSP_API_Reference",
        "sourceHints": ["API", "agent", "tool", "CLI"],
    },
    "wiki/synthesis/ORCA_Output_Guide.md": {
        "symbol": "ORCA_Output_Guide",
        "sourceHints": ["output", "log", "out file", "parse-log"],
    },
    "wiki/synthesis/Diagnostics_Catalog.md": {
        "symbol": "Diagnostics_Catalog",
        "sourceHints": ["diagnostics", "rule", "code", "catalog"],
    },
}

# Map from wiki path (without wiki/ prefix) to raw asset path
WIKI_TO_RAW: dict[str, str] = {
    "entities/Diagnostic_Engine_v1.md": "raw/assets/docs/DIAGNOSTIC_ENGINE_V1.md",
    "entities/OpenQC_Alignment.md": "raw/assets/docs/OPENQC_ALIGNMENT.md",
    "entities/ORCA_Official_Documentation.md": "raw/assets/orca-input-format.md",
    "entities/ORCA_Quantum_Chemistry.md": "raw/assets/README.md",
    "entities/Language_Server_Protocol.md": "raw/assets/docs/ARCHITECTURE.md",
    "synthesis/Input_File_Guide.md": "raw/assets/orca-input-format.md",
    "synthesis/ORCA_Output_Guide.md": "raw/assets/orca-output-format.md",
    "synthesis/ORCA_LSP_API_Reference.md": "raw/assets/docs/ARCHITECTURE.md",
    "synthesis/Diagnostics_Catalog.md": "raw/assets/docs/DIAGNOSTIC_ENGINE_V1.md",
    "concepts/Basis_Set_Selection.md": "raw/assets/orca-basis-sets-reference.md",
    "concepts/Coupled_Cluster_Theory.md": "raw/assets/orca-keywords-reference.md",
    "concepts/Density_Functional_Theory.md": "raw/assets/orca-keywords-reference.md",
    "concepts/Dispersion_Corrections.md": "raw/assets/orca-keywords-reference.md",
    "concepts/DLPNO_Methods.md": "raw/assets/orca-keywords-reference.md",
    "concepts/Frequency_Calculation.md": "raw/assets/orca-compound-jobs.md",
    "concepts/Geometry_Optimization.md": "raw/assets/orca-compound-jobs.md",
    "concepts/Compound_Jobs.md": "raw/assets/orca-compound-jobs.md",
    "concepts/Solvation_Models.md": "raw/assets/orca-tutorials.md",
    "concepts/Time_Dependent_DFT.md": "raw/assets/orca-tutorials.md",
    "concepts/Transition_State_Search.md": "raw/assets/orca-tutorials.md",
    "entities/DFT_Functionals.md": "raw/assets/orca-keywords-reference.md",
    "entities/Basis_Sets.md": "raw/assets/orca-basis-sets-reference.md",
    "entities/Job_Types.md": "raw/assets/orca-compound-jobs.md",
    "entities/Percent_Blocks.md": "raw/assets/orca-keywords-reference.md",
    "entities/Wavefunction_Methods.md": "raw/assets/orca-keywords-reference.md",
    "entities/Element_Symbols.md": "raw/assets/orca-keywords-reference.md",
    "entities/Geometry_Section.md": "raw/assets/orca-input-format.md",
    "entities/Auxiliary_Basis_Sets.md": "raw/assets/orca-basis-sets-reference.md",
    "entities/ORCA_GitHub_Tools.md": "raw/assets/orca-github-tools.md",
}


def find_project_root() -> Path:
    """Find the project root by looking for pyproject.toml."""
    candidate = Path(__file__).resolve().parent.parent
    if (candidate / "pyproject.toml").exists():
        return candidate
    cwd = Path.cwd()
    if (cwd / "pyproject.toml").exists():
        return cwd
    return candidate


def _rel(root: Path, path: Path) -> str:
    """Return repo-relative path string."""
    return str(path.relative_to(root))


def discover_source_files(root: Path) -> list[Path]:
    """Discover Python source files under src/orca_lsp."""
    src_dir = root / "src" / "orca_lsp"
    if not src_dir.is_dir():
        return []
    return sorted(src_dir.rglob("*.py"))


def discover_wiki_pages(root: Path) -> list[Path]:
    """Discover wiki markdown files under wiki/."""
    wiki_dir = root / "wiki"
    if not wiki_dir.is_dir():
        return []
    return sorted(wiki_dir.rglob("*.md"))


def discover_raw_assets(root: Path) -> list[Path]:
    """Discover raw asset files under raw/."""
    raw_dir = root / "raw"
    if not raw_dir.is_dir():
        return []
    assets = []
    for f in sorted(raw_dir.rglob("*")):
        if f.is_file() and f.suffix in {".md", ".inp", ".json"}:
            assets.append(f)
    return assets


def write_raw_asset_manifest(root: Path) -> Path:
    """Write a deterministic manifest for all raw evidence assets."""
    manifest_path = root / "raw" / "assets" / "manifest.json"
    entries = []
    for raw_path in discover_raw_assets(root):
        if raw_path == manifest_path:
            continue
        raw_rel = _rel(root, raw_path)
        entries.append(
            {
                "path": raw_rel.removeprefix("raw/assets/"),
                "source_type": "raw_asset",
                "source_url": f"{REPOSITORY}/blob/main/{raw_rel}",
                "stable_id": raw_rel.replace("/", "-").replace(".", "-"),
            }
        )
    payload = {
        "manifest_version": "1.0.0",
        "schema_version": "provenance-manifest-v1",
        "repository": "newtontech/orca-lsp",
        "entries": entries,
    }
    manifest_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return manifest_path


def extract_docstrings(source_path: Path) -> list[dict[str, str]]:
    """Extract module-level and top-level docstrings from a Python source file."""
    text = source_path.read_text(encoding="utf-8", errors="replace")
    results: list[dict[str, str]] = []

    # Module docstring (first triple-quoted string)
    mod_match = re.match(r'(?:"""|\'\'\')(.*?)(?:"""|\'\'\')', text, re.DOTALL)
    if mod_match:
        results.append(
            {
                "symbol": source_path.stem,
                "docstring": mod_match.group(1).strip(),
                "line": 1,
            }
        )

    # Class/function docstrings
    for match in re.finditer(
        r'(?:class|def|async def)\s+(\w+)[^"]*(?:"""|\'\'\')(.*?)(?:"""|\'\'\')',
        text,
        re.DOTALL,
    ):
        results.append(
            {
                "symbol": match.group(1),
                "docstring": match.group(2).strip(),
                "line": text[: match.start()].count("\n") + 1,
            }
        )
        if len(results) >= 10:
            break

    return results


def match_docstring_to_wiki(
    docstring_entries: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Match docstring entries to wiki pages based on content hints."""
    matched: list[dict[str, str]] = []
    for entry in docstring_entries:
        doc_text = entry["docstring"].lower()
        best_match: str | None = None
        best_score = 0
        for wiki_path, meta in WIKI_METADATA.items():
            for hint in meta["sourceHints"]:
                if hint.lower() in doc_text:
                    score = len(hint)
                    if score > best_score:
                        best_score = score
                        best_match = wiki_path
        if best_match:
            matched.append(
                {
                    "path": entry["_sourceRel"],
                    "wikiPath": best_match,
                    "symbol": WIKI_METADATA[best_match]["symbol"],
                }
            )
    return matched


def build_docstrings(root: Path) -> list[dict[str, str]]:
    """Build the docstrings[] array mapping source files → wiki pages."""
    results: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for source_path in discover_source_files(root):
        source_rel = _rel(root, source_path)
        entries = extract_docstrings(source_path)
        for e in entries:
            e["_sourceRel"] = source_rel
        matched = match_docstring_to_wiki(entries)
        for m in matched:
            key = (m["path"], m["wikiPath"])
            if key not in seen:
                seen.add(key)
                results.append(m)
    return results


def build_wiki_sources(root: Path) -> list[dict[str, str]]:
    """Build the wikiSources[] array mapping wiki pages → raw assets."""
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for wiki_path in discover_wiki_pages(root):
        wiki_rel = _rel(root, wiki_path)
        wiki_short = wiki_rel.removeprefix("wiki/")
        raw_rel = WIKI_TO_RAW.get(wiki_short)
        if raw_rel and raw_rel not in seen:
            seen.add(raw_rel)
            results.append(
                {
                    "wikiPath": wiki_rel,
                    "rawPath": raw_rel,
                    "sourceUrl": f"{REPOSITORY}/blob/main/{raw_rel}",
                }
            )
    return sorted(results, key=lambda x: x["wikiPath"])


def _extract_legacy_codes(path: Path, root: Path) -> list[str]:
    """Extract rule code strings matching <PREFIX>-<type><digits> from a file."""
    text = path.read_text(encoding="utf-8", errors="replace")
    # Match codes like ORCA-E001, TC-W001, TC-E003 etc.
    pattern = re.compile(r"\b([A-Z]{2,6})-[EW](\d{3,4})\b")
    codes: list[str] = []
    for match in pattern.finditer(text):
        code = match.group(0)
        # Verify it looks like a real diagnostic code
        if re.match(r"^[A-Z]{2,6}-[EW]\d{3,4}$", code):
            codes.append(code)
    return codes


def build_rule_ids(root: Path) -> list[dict[str, str]]:
    """Build the ruleIds[] array with OpenQC format codes.

    Rule codes follow <BACKEND>-<FILE_ROLE>-<CATEGORY>-NNN.
    We map existing legacy codes (ORCA-E001, TC-W001) to the new format.
    """
    lint_path = root / "src" / "orca_lsp" / "features" / "lint.py"
    typecheck_path = root / "src" / "orca_lsp" / "features" / "typecheck.py"

    legacy_codes: set[str] = set()
    if lint_path.exists():
        legacy_codes.update(_extract_legacy_codes(lint_path, root))
    if typecheck_path.exists():
        legacy_codes.update(_extract_legacy_codes(typecheck_path, root))

    rule_ids: list[dict[str, str]] = []
    seen: set[str] = set()

    for legacy_code in sorted(legacy_codes):
        openqc_code = LEGACY_CODE_MAP.get(legacy_code)
        if openqc_code and openqc_code not in seen:
            seen.add(openqc_code)
            # Determine which file this code originates from
            source_path = "src/orca_lsp/features/lint.py"
            if legacy_code.startswith("TC-"):
                source_path = "src/orca_lsp/features/typecheck.py"
            rule_ids.append(
                {
                    "code": openqc_code,
                    "sourcePath": source_path,
                }
            )

    return rule_ids


def build_source_urls(root: Path) -> list[dict[str, str]]:
    """Build the sourceUrls[] array mapping raw assets → GitHub URLs."""
    results: list[dict[str, str]] = []
    for raw_path in discover_raw_assets(root):
        raw_rel = _rel(root, raw_path)
        results.append(
            {
                "rawPath": raw_rel,
                "url": f"{REPOSITORY}/blob/main/{raw_rel}",
            }
        )
    return sorted(results, key=lambda x: x["rawPath"])


def build_raw_manifest(root: Path) -> dict[str, Any]:
    """Build the OpenQC rawManifest descriptor."""
    manifest_path = root / "raw" / "assets" / "manifest.json"
    return {
        "path": _rel(root, manifest_path),
        "ok": manifest_path.is_file() and manifest_path.stat().st_size > 0,
    }


def generate_report(root: Path | None = None) -> dict[str, Any]:
    """Generate the full OpenQC v1 traceability report."""
    if root is None:
        root = find_project_root()

    write_raw_asset_manifest(root)
    docstrings = build_docstrings(root)
    wiki_sources = build_wiki_sources(root)
    rule_ids = build_rule_ids(root)
    source_urls = build_source_urls(root)
    raw_manifest = build_raw_manifest(root)
    docstrings_linked = sum(
        1 for item in docstrings if (root / item["path"]).exists() and (root / item["wikiPath"]).exists()
    )
    broken_wiki_links = sum(1 for item in docstrings if not (root / item["wikiPath"]).exists())
    wiki_sources_without_raw = sum(1 for item in wiki_sources if not (root / item["rawPath"]).exists())

    report: dict[str, Any] = {
        "schemaVersion": SCHEMA_VERSION,
        "serverId": SERVER_ID,
        "repository": REPOSITORY,
        "languageId": LANGUAGE_ID,
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "docstringsTotal": len(docstrings),
            "docstringsLinked": docstrings_linked,
            "brokenWikiLinks": broken_wiki_links,
            "wikiSourcesWithoutRaw": wiki_sources_without_raw,
            "rawManifestFailures": 0 if raw_manifest["ok"] else 1,
            "ruleIdsTotal": len(rule_ids),
            "sourceUrlsTotal": len(source_urls),
            "wikiSourcesTotal": len(wiki_sources),
        },
        "docstrings": docstrings,
        "wikiSources": wiki_sources,
        "ruleIds": rule_ids,
        "sourceUrls": source_urls,
        "rawManifest": raw_manifest,
    }
    return report


def write_report(report: dict[str, Any], output_path: Path) -> None:
    """Write the report as formatted JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def validate_report(report: dict[str, Any]) -> list[str]:
    """Validate the report against the OpenQC v1 schema contract.

    Returns a list of error messages (empty = valid).
    """
    errors: list[str] = []

    required_top = [
        "schemaVersion",
        "serverId",
        "repository",
        "languageId",
        "generatedAt",
        "summary",
        "docstrings",
        "wikiSources",
        "ruleIds",
        "sourceUrls",
        "rawManifest",
    ]
    for field in required_top:
        if field not in report:
            errors.append(f"Missing top-level field: {field}")

    if errors:
        return errors

    if report["schemaVersion"] != SCHEMA_VERSION:
        errors.append(
            f"schemaVersion must be {SCHEMA_VERSION!r}, " f"got {report['schemaVersion']!r}"
        )
    if report["serverId"] != SERVER_ID:
        errors.append(f"serverId must be {SERVER_ID!r}, got {report['serverId']!r}")
    if report["repository"] != REPOSITORY:
        errors.append(f"repository must be {REPOSITORY!r}, got {report['repository']!r}")
    if report["languageId"] != LANGUAGE_ID:
        errors.append(f"languageId must be {LANGUAGE_ID!r}, got {report['languageId']!r}")
    if not report.get("generatedAt"):
        errors.append("generatedAt must be non-empty")

    # docstrings
    docstrings = report.get("docstrings", [])
    if not docstrings:
        errors.append("docstrings[] must be non-empty")
    for i, ds in enumerate(docstrings):
        if not ds.get("path"):
            errors.append(f"docstrings[{i}].path must be non-empty")
        if not ds.get("wikiPath"):
            errors.append(f"docstrings[{i}].wikiPath must be non-empty")
        if not ds.get("symbol"):
            errors.append(f"docstrings[{i}].symbol must be non-empty")

    # wikiSources
    wiki_sources = report.get("wikiSources", [])
    if not wiki_sources:
        errors.append("wikiSources[] must be non-empty")
    for i, ws in enumerate(wiki_sources):
        if not ws.get("wikiPath"):
            errors.append(f"wikiSources[{i}].wikiPath must be non-empty")
        if not ws.get("rawPath"):
            errors.append(f"wikiSources[{i}].rawPath must be non-empty")
        if not ws.get("sourceUrl"):
            errors.append(f"wikiSources[{i}].sourceUrl must be non-empty")

    # ruleIds
    rule_ids = report.get("ruleIds", [])
    if not rule_ids:
        errors.append("ruleIds[] must be non-empty")
    code_pattern = re.compile(r"^[A-Z]+-[A-Z]+-[A-Z]+-\d+$")
    for i, ri in enumerate(rule_ids):
        code = ri.get("code", "")
        if not re.match(code_pattern, code):
            errors.append(
                f"ruleIds[{i}].code {code!r} does not match "
                f"<BACKEND>-<FILE_ROLE>-<CATEGORY>-NNN"
            )
        if not ri.get("sourcePath"):
            errors.append(f"ruleIds[{i}].sourcePath must be non-empty")

    # sourceUrls
    source_urls = report.get("sourceUrls", [])
    if not source_urls:
        errors.append("sourceUrls[] must be non-empty")
    for i, su in enumerate(source_urls):
        if not su.get("rawPath"):
            errors.append(f"sourceUrls[{i}].rawPath must be non-empty")
        if not su.get("url"):
            errors.append(f"sourceUrls[{i}].url must be non-empty")

    # summary
    summary = report.get("summary", {})
    for field in [
        "docstringsTotal",
        "docstringsLinked",
        "brokenWikiLinks",
        "wikiSourcesWithoutRaw",
        "rawManifestFailures",
    ]:
        if not isinstance(summary.get(field), int) or summary[field] < 0:
            errors.append(f"summary.{field} must be a non-negative integer")

    # rawManifest
    raw_manifest = report.get("rawManifest", {})
    if not isinstance(raw_manifest, dict) or not raw_manifest:
        errors.append("rawManifest must be a non-empty object")
    else:
        manifest_path = raw_manifest.get("path")
        if not isinstance(manifest_path, str) or not manifest_path:
            errors.append("rawManifest.path must be non-empty")
        elif manifest_path.startswith("/") or ".." in Path(manifest_path).parts:
            errors.append("rawManifest.path must be repository-relative")
        if not isinstance(raw_manifest.get("ok"), bool):
            errors.append("rawManifest.ok must be boolean")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate OpenQC v1 traceability report")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("reports") / "docstring-wiki-raw-traceability.json",
        help="Output path for the report JSON",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Project root directory (auto-detected by default)",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate an existing report instead of generating one",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Generate report and validate it, exit non-zero on validation failure",
    )
    args = parser.parse_args(argv)

    root = args.root if args.root else find_project_root()

    if args.validate:
        if not args.output.exists():
            print(f"Report not found: {args.output}", file=sys.stderr)
            return 1
        report = json.loads(args.output.read_text(encoding="utf-8"))
        errors = validate_report(report)
        if errors:
            for err in errors:
                print(f"VALIDATION ERROR: {err}", file=sys.stderr)
            return 1
        print(f"Report is valid: {args.output}")
        return 0

    report = generate_report(root)
    write_report(report, args.output)
    print(f"Report written: {args.output}")
    print(f"  docstrings: {len(report['docstrings'])}")
    print(f"  wikiSources: {len(report['wikiSources'])}")
    print(f"  ruleIds: {len(report['ruleIds'])}")
    print(f"  sourceUrls: {len(report['sourceUrls'])}")
    print(f"  rawManifest: {report['rawManifest']['path']} ok={report['rawManifest']['ok']}")

    if args.check:
        errors = validate_report(report)
        if errors:
            for err in errors:
                print(f"VALIDATION ERROR: {err}", file=sys.stderr)
            return 1
        print("Validation: PASSED")

    return 0


if __name__ == "__main__":
    sys.exit(main())
