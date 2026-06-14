"""Universal generated-input preflight capabilities.

This module implements the four fleet-wide preflight capabilities called out in
``newtontech/orca-lsp#81`` against a *generic artifact-role model*, so the
checks generalize to any backend in the scientific LSP fleet instead of being
wired to MatMaster submission policy:

* ``version-aware-keywords``  - explicit runtime/version assumption metadata and
  method/basis keyword availability derived from the builtin keyword set, never
  guessed.
* ``cross-artifact-graph``   - resolves an ORCA input file (or a case
  directory) as a graph of artifacts with stable generic roles
  (primary-input, simple-keywords, geometry, method-config, basis-config,
  wavefunction-reference). Cross-file/cross-section checks operate on the graph
  rather than ad-hoc block names, so the same model works for the rest of the
  fleet.
* ``code-actions``           - normalizes repair hints/actions on every
  diagnostic and exposes a blocking gate the agent CLI can run as
  ``check --fail-on-blocking`` / ``preflight --fail-on-blocking``.
* ``fleet-regression-fixtures`` - ``fleet_manifest`` returns a machine-readable
  description of the preflight surface (codes, capabilities, fixture
  expectations) so the parent ``bohrium_skills`` probe/report workflow can
  consume regression evidence without re-deriving it.

The diagnostics emitted here are plain dictionaries (not the legacy
``Diagnostic`` dataclass) so they can carry the richer ``DiagnosticEnvelope/v1``
fields (``source_provenance``, ``domain_tags``, ``facts``, ``artifact_roles``,
``version_assumption``, ``actions``) directly.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .keywords import (
    ALL_KEYWORDS,
    DFT_FUNCTIONALS,
)
from .parser import ORCAParser, ParseResult, PercentBlock

# --- Artifact-role model ---------------------------------------------------

# Generic roles. These are intentionally software-agnostic: every fleet backend
# can map its native input shape onto this same small role set, which is what
# lets the parent router consume cross-file checks without learning MatMaster
# specifics. ORCA's ``!`` / ``%block`` / ``* xyz *`` structure maps cleanly.
ROLE_PRIMARY_INPUT = "primary-input"
ROLE_SIMPLE_KEYWORDS = "simple-keywords"
ROLE_GEOMETRY = "geometry"
ROLE_METHOD_CONFIG = "method-config"
ROLE_BASIS_CONFIG = "basis-config"
ROLE_WAVEFUNCTION_REFERENCE = "wavefunction-reference"

ALL_ROLES = (
    ROLE_PRIMARY_INPUT,
    ROLE_SIMPLE_KEYWORDS,
    ROLE_GEOMETRY,
    ROLE_METHOD_CONFIG,
    ROLE_BASIS_CONFIG,
    ROLE_WAVEFUNCTION_REFERENCE,
)

# Conservative workflow thresholds used by the warning-level SCF maxiter check.
# The actual cutoff is overridable via the preflight intent contract; this is
# only the default fleet baseline, not a MatMaster policy.
DEFAULT_MAXITER_WARNING = 50

# Codes reserved for the universal preflight surface. They use the ``ORCA6xx``
# band so they sort after existing rule codes and stay identifiable as
# cross-fleet preflight findings.
CODE_MISSING_SIMPLE_INPUT = "ORCA601"
CODE_MISSING_GEOMETRY = "ORCA602"
CODE_MULTIPLICITY_CHARGE = "ORCA603"
CODE_UNRESOLVED_WFN_REFERENCE = "ORCA604"
CODE_UNKNOWN_KEYWORD = "ORCA605"
CODE_MISSING_BASIS_CONFIG = "ORCA606"
CODE_LOW_MAXITER = "ORCA607"
CODE_VERSION_ASSUMPTION = "ORCA608"
CODE_KEYWORD_VERSION_MISMATCH = "ORCA609"


@dataclass(frozen=True)
class ArtifactNode:
    """A node in the cross-artifact graph.

    ``role`` is one of the fleet-generic roles above; ``path`` is the resolved
    filesystem path (may be a non-existent reference, which is itself a
    finding); ``source`` records where the reference originated so consumers
    can trace provenance.
    """

    role: str
    path: Path
    exists: bool
    source: str
    referenced_from: tuple[str, int] | None = None
    detail: dict[str, Any] | None = None


@dataclass
class ArtifactGraph:
    """Generic cross-artifact graph built from a parsed ORCA input."""

    case_dir: Path
    nodes: list[ArtifactNode] = field(default_factory=list)

    def by_role(self, role: str) -> list[ArtifactNode]:
        return [node for node in self.nodes if node.role == role]

    def to_json(self) -> list[dict[str, Any]]:
        """Serialize the graph for the parent probe/report workflow."""

        def _node_json(node: ArtifactNode) -> dict[str, Any]:
            payload: dict[str, Any] = {
                "role": node.role,
                "path": str(node.path),
                "exists": node.exists,
                "source": node.source,
            }
            if node.referenced_from is not None:
                payload["referenced_from"] = {
                    "path": node.referenced_from[0],
                    "line": node.referenced_from[1],
                }
            if node.detail:
                payload["detail"] = node.detail
            return payload

        return sorted(
            (_node_json(node) for node in self.nodes),
            key=lambda item: (item["role"], item["path"]),
        )


# Regex that recognizes an external wavefunction file reference inside a
# ``%moinp "<path>"`` block (single-line OR multi-line form). ORCA accepts both
# quoted and bare paths; we capture the resolved filename so the graph can
# record whether it exists.
_MOINP_RE = re.compile(
    r"^\s*%?\s*moinp\s+[\"']?(?P<path>[^\"']+?)[\"']?\s*(?:end\s*)?$",
    re.IGNORECASE,
)


def _find_primary_input(case_dir: Path) -> Path | None:
    """Locate the primary ORCA input inside a case directory.

    ORCA inputs are conventionally ``*.inp`` but can also be extension-less.
    We prefer the first ``*.inp`` file, then fall back to the first file whose
    content begins with a simple-input ``!`` line or a ``%`` block.
    """
    if not case_dir.is_dir():
        return None
    inp_files = sorted(case_dir.glob("*.inp"))
    if inp_files:
        return inp_files[0]
    for candidate in sorted(case_dir.iterdir()):
        if not candidate.is_file():
            continue
        try:
            head = candidate.read_text(encoding="utf-8", errors="ignore")[:512]
        except OSError:
            continue
        for line in head.splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if stripped.startswith("!") or stripped.startswith("%"):
                return candidate
            break
    return None


def build_artifact_graph(case_dir: Path, input_path: Path, result: ParseResult) -> ArtifactGraph:
    """Build the cross-artifact graph from a parsed ORCA input.

    The model is generic: it records roles + resolved paths + provenance. The
    same shape generalizes to other fleet backends because it never bakes in
    MatMaster/Bohrium runtime concepts (no input_dir, no image, no session).
    """
    case_dir = case_dir.resolve()
    input_path = input_path.resolve()
    graph = ArtifactGraph(case_dir=case_dir)

    graph.nodes.append(
        ArtifactNode(
            role=ROLE_PRIMARY_INPUT,
            path=input_path,
            exists=input_path.exists(),
            source="case-root",
        )
    )

    if result.simple_input is not None:
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_SIMPLE_KEYWORDS,
                path=input_path,
                exists=True,
                source=f"{input_path.name}:!-line",
                referenced_from=(str(input_path), result.simple_input.line_number),
                detail={
                    "methods": list(result.simple_input.methods),
                    "basis_sets": list(result.simple_input.basis_sets),
                    "job_types": list(result.simple_input.job_types),
                },
            )
        )

    if result.geometry is not None:
        graph.nodes.append(
            ArtifactNode(
                role=ROLE_GEOMETRY,
                path=input_path,
                exists=bool(result.geometry.atoms),
                source=f"{input_path.name}:*-block",
                referenced_from=(str(input_path), result.geometry.line_start),
                detail={
                    "atom_count": len(result.geometry.atoms),
                    "charge": result.geometry.charge,
                    "multiplicity": result.geometry.multiplicity,
                },
            )
        )

    for block in result.percent_blocks:
        if block.name == "method" or block.name == "scf":
            graph.nodes.append(
                ArtifactNode(
                    role=ROLE_METHOD_CONFIG,
                    path=input_path,
                    exists=True,
                    source=f"{input_path.name}:%{block.name}",
                    referenced_from=(str(input_path), block.line_start),
                    detail=dict(block.parameters),
                )
            )
        elif block.name == "basis":
            graph.nodes.append(
                ArtifactNode(
                    role=ROLE_BASIS_CONFIG,
                    path=input_path,
                    exists=True,
                    source=f"{input_path.name}:%{block.name}",
                    referenced_from=(str(input_path), block.line_start),
                    detail=_basis_block_detail(block),
                )
            )
        elif block.name == "moinp":
            ref_path, ref_line = _resolve_moinp_reference(case_dir, input_path, block)
            graph.nodes.append(
                ArtifactNode(
                    role=ROLE_WAVEFUNCTION_REFERENCE,
                    path=ref_path,
                    exists=ref_path.exists(),
                    source=f"{input_path.name}:%moinp",
                    referenced_from=(str(input_path), ref_line),
                    detail={"declared_name": block.raw_content.strip()},
                )
            )

    return graph


def _basis_block_detail(block: PercentBlock) -> dict[str, Any]:
    """Extract element->basis assignments from a %basis NewGTO/NewAuxGTO block."""
    raw = block.raw_content
    detail: dict[str, Any] = {"newgto_assignments": {}, "newauxgto_assignments": {}}
    for line in raw.splitlines():
        tokens = line.strip().split()
        if len(tokens) < 2:
            continue
        key = tokens[0].lower()
        if key == "newgto":
            element, basis = _element_basis_pair(tokens[1:])
            if element and basis:
                detail["newgto_assignments"][element] = basis
        elif key == "newauxgto":
            element, basis = _element_basis_pair(tokens[1:])
            if element and basis:
                detail["newauxgto_assignments"][element] = basis
    return detail


def _element_basis_pair(rest: list[str]) -> tuple[str, str]:
    """Return (element, basis) from a NewGTO token tail, stripping quotes."""
    if len(rest) < 2:
        return ("", "")
    element = rest[0].strip("\"'")
    basis = rest[1].strip("\"'")
    return (element, basis)


def _resolve_moinp_reference(
    case_dir: Path, input_path: Path, block: PercentBlock
) -> tuple[Path, int]:
    """Resolve a %moinp \"file.gbw\" reference to a filesystem path + line."""
    for offset, line in enumerate(block.raw_content.splitlines()):
        match = _MOINP_RE.match(line)
        if match and match.group("path"):
            declared = match.group("path").strip()
            candidate = Path(declared)
            resolved = candidate if candidate.is_absolute() else case_dir / candidate
            return (resolved, block.line_start + offset)
    return (case_dir / "<unresolved-moinp>", block.line_start)


# --- Preflight diagnostics -------------------------------------------------


def preflight_diagnostics(
    case_dir: Path,
    input_path: Path,
    *,
    intent: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], ArtifactGraph]:
    """Run universal generated-input preflight checks.

    Returns a tuple of (diagnostics, artifact_graph). Diagnostics are envelope
    dicts carrying the full ``DiagnosticEnvelope/v1`` field set so the agent
    CLI can emit them directly without re-shaping.
    """
    case_dir = case_dir.resolve()
    input_path = input_path.resolve()
    text = input_path.read_text(encoding="utf-8", errors="ignore")
    parser = ORCAParser()
    result = parser.parse(text)
    graph = build_artifact_graph(case_dir, input_path, result)

    version_assumption = resolve_version_assumption(intent)
    diagnostics: list[dict[str, Any]] = []
    diagnostics.extend(_missing_simple_input_diagnostics(graph, result, input_path))
    diagnostics.extend(_missing_geometry_diagnostics(graph, result, input_path))
    diagnostics.extend(_multiplicity_charge_diagnostics(result, input_path))
    diagnostics.extend(_unresolved_wfn_reference_diagnostics(graph))
    diagnostics.extend(_unknown_keyword_diagnostics(result, input_path))
    diagnostics.extend(_missing_basis_config_diagnostics(graph, result, input_path))
    diagnostics.extend(_low_maxiter_diagnostics(result, input_path, intent))
    diagnostics.extend(
        _keyword_version_mismatch_diagnostics(result, input_path, version_assumption)
    )
    diagnostics.extend(_version_assumption_diagnostic(version_assumption, intent, input_path))

    return (
        sorted(
            diagnostics,
            key=lambda item: (
                item.get("range", {}).get("start", {}).get("line", 0),
                item.get("range", {}).get("start", {}).get("character", 0),
                item["code"],
            ),
        ),
        graph,
    )


def _diag(
    *,
    code: str,
    severity: str,
    message: str,
    path: Path,
    line: int = 1,
    column: int = 1,
    category: str,
    confidence: float,
    blocking: bool,
    source_provenance: dict[str, Any],
    fix_hints: list[str],
    actions: list[dict[str, Any]] | None = None,
    facts: dict[str, Any] | None = None,
    artifact_roles: list[str] | None = None,
    domain_tags: list[str] | None = None,
    version_assumption: dict[str, Any] | None = None,
    manual_ref: str | None = None,
    intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a single normalized preflight diagnostic.

    Carries every field the issue acceptance criteria require (``code``,
    ``severity``, ``path``/``range``, ``blocking``, ``category``,
    ``source_provenance``, ``fix_hints``/``actions``) plus the richer envelope
    fields (``facts``, ``artifact_roles``, ``domain_tags``,
    ``version_assumption``) used by the parent fleet probe.
    """
    line0 = max(line - 1, 0)
    col0 = max(column - 1, 0)
    payload: dict[str, Any] = {
        "code": code,
        "severity": severity,
        "message": message,
        "file": str(path),
        "line": line,
        "column": column,
        "category": category,
        "confidence": confidence,
        "source": "orca-preflight",
        "range": {
            "start": {"line": line0, "character": col0},
            "end": {"line": line0, "character": col0 + 1},
        },
        "blocking": blocking,
        "fix_hints": fix_hints,
        "source_provenance": source_provenance,
    }
    if actions:
        payload["actions"] = actions
    if facts:
        payload["facts"] = facts
    if artifact_roles:
        payload["artifact_roles"] = artifact_roles
    if domain_tags:
        payload["domain_tags"] = domain_tags
    if version_assumption:
        payload["version_assumption"] = version_assumption
    if manual_ref:
        payload["manual_ref"] = manual_ref
    if intent:
        payload["intent"] = intent
    return payload


def _missing_simple_input_diagnostics(
    graph: ArtifactGraph, result: ParseResult, input_path: Path
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if result.simple_input is not None:
        return out
    out.append(
        _diag(
            code=CODE_MISSING_SIMPLE_INPUT,
            severity="error",
            message="Missing simple input line (!) with method and basis set",
            path=input_path,
            line=1,
            category="semantic consistency",
            confidence=0.97,
            blocking=True,
            source_provenance={
                "role": ROLE_SIMPLE_KEYWORDS,
                "reason": "no '!'-prefixed simple input line found",
            },
            fix_hints=[
                "Add a '! <method> <basis> <jobtype>' line at the top of the input",
                "Example: ! B3LYP def2-TZVP OPT",
            ],
            actions=[
                {
                    "kind": "insert_simple_input",
                    "role": ROLE_SIMPLE_KEYWORDS,
                    "target": str(input_path),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={"has_simple_input": False},
            artifact_roles=[ROLE_SIMPLE_KEYWORDS, ROLE_PRIMARY_INPUT],
            domain_tags=["cross-file", "blocking"],
        )
    )
    return out


def _missing_geometry_diagnostics(
    graph: ArtifactGraph, result: ParseResult, input_path: Path
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if result.geometry is not None and result.geometry.atoms:
        return out
    out.append(
        _diag(
            code=CODE_MISSING_GEOMETRY,
            severity="error",
            message=(
                "Missing geometry section (* xyz charge multiplicity ... *) "
                "with atom coordinates"
            ),
            path=input_path,
            line=1,
            category="cross-file reference",
            confidence=0.95,
            blocking=True,
            source_provenance={
                "role": ROLE_GEOMETRY,
                "reason": "no '* xyz ... *' coordinate block parsed",
            },
            fix_hints=[
                "Add a '* xyz <charge> <multiplicity>' block with atom lines",
                "Close the block with a bare '*' line",
            ],
            actions=[
                {
                    "kind": "insert_geometry",
                    "role": ROLE_GEOMETRY,
                    "target": str(input_path),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={"atom_count": 0},
            artifact_roles=[ROLE_GEOMETRY, ROLE_PRIMARY_INPUT],
            domain_tags=["cross-file", "blocking"],
        )
    )
    return out


def _multiplicity_charge_diagnostics(result: ParseResult, input_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    geometry = result.geometry
    if geometry is None:
        return out
    if geometry.multiplicity < 1:
        out.append(
            _diag(
                code=CODE_MULTIPLICITY_CHARGE,
                severity="error",
                message=f"Multiplicity {geometry.multiplicity} must be >= 1",
                path=input_path,
                line=geometry.line_start + 1,
                category="semantic consistency",
                confidence=0.97,
                blocking=True,
                source_provenance={
                    "role": ROLE_GEOMETRY,
                    "parsed_multiplicity": geometry.multiplicity,
                    "parsed_charge": geometry.charge,
                },
                fix_hints=[
                    "Set multiplicity to 1 (singlet) or higher odd value for open-shell systems",
                ],
                actions=[
                    {
                        "kind": "set_geometry_header",
                        "role": ROLE_GEOMETRY,
                        "field": "multiplicity",
                        "target": str(input_path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={
                    "multiplicity": geometry.multiplicity,
                    "charge": geometry.charge,
                },
                artifact_roles=[ROLE_GEOMETRY],
                domain_tags=["semantic", "blocking"],
            )
        )
    return out


def _unresolved_wfn_reference_diagnostics(graph: ArtifactGraph) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for node in graph.by_role(ROLE_WAVEFUNCTION_REFERENCE):
        if node.exists:
            continue
        ref = node.referenced_from or (str(node.path), 1)
        out.append(
            _diag(
                code=CODE_UNRESOLVED_WFN_REFERENCE,
                severity="warning",
                message=(
                    f"wavefunction-reference artifact referenced from %moinp cannot "
                    f"be resolved: {node.path.name}"
                ),
                path=node.path,
                line=ref[1] + 1,
                category="cross-file reference",
                confidence=0.85,
                blocking=False,
                source_provenance={
                    "role": ROLE_WAVEFUNCTION_REFERENCE,
                    "declared_in": node.source,
                    "declared_name": (node.detail or {}).get("declared_name"),
                },
                fix_hints=[
                    f"Place {node.path.name} in the case directory",
                    "Or correct the path declared in %moinp",
                ],
                actions=[
                    {
                        "kind": "resolve_artifact",
                        "role": ROLE_WAVEFUNCTION_REFERENCE,
                        "target": str(node.path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"unresolved_path": str(node.path)},
                artifact_roles=[ROLE_WAVEFUNCTION_REFERENCE],
                domain_tags=["cross-file", "workspace-resolve"],
            )
        )
    return out


def _unknown_keyword_diagnostics(result: ParseResult, input_path: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    simple = result.simple_input
    if simple is None:
        return out
    known = {name.upper() for name in ALL_KEYWORDS}
    for token in simple.other_keywords:
        upper = token.upper()
        # Skip obviously-non-keyword tokens: numeric flags, file paths, and
        # option=value pairs. These are legitimate simple-input flags we do not
        # catalog but should not flag as unknown method/basis keywords.
        if upper.startswith("-") or "=" in token or token.endswith(".gbw"):
            continue
        if upper in known:
            continue
        out.append(
            _diag(
                code=CODE_UNKNOWN_KEYWORD,
                severity="warning",
                message=(
                    f"Simple-input token '{token}' is not in the builtin method/basis/"
                    f"job catalog; verify spelling against the ORCA manual"
                ),
                path=input_path,
                line=simple.line_number + 1,
                column=1,
                category="schema",
                confidence=0.7,
                blocking=False,
                source_provenance={
                    "role": ROLE_SIMPLE_KEYWORDS,
                    "keyword": token,
                    "schema_source": "orca-lsp builtin keyword catalog",
                },
                fix_hints=[
                    f"Confirm '{token}' is a valid ORCA simple keyword",
                    "Check for a typo against documented method/basis/job names",
                ],
                actions=[
                    {
                        "kind": "review_keyword",
                        "keyword": token,
                        "target": str(input_path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"keyword": token},
                artifact_roles=[ROLE_SIMPLE_KEYWORDS],
                domain_tags=["schema", "non-blocking"],
            )
        )
    return out


def _missing_basis_config_diagnostics(
    graph: ArtifactGraph, result: ParseResult, input_path: Path
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    simple = result.simple_input
    if simple is None:
        return out
    has_simple_basis = bool(simple.basis_sets)
    has_basis_block = any(
        node.role == ROLE_BASIS_CONFIG and (node.detail or {}).get("newgto_assignments")
        for node in graph.nodes
    )
    if has_simple_basis or has_basis_block:
        return out
    out.append(
        _diag(
            code=CODE_MISSING_BASIS_CONFIG,
            severity="error",
            message=(
                "No basis set declared: add a basis on the '!'-line or a " "%basis NewGTO block"
            ),
            path=input_path,
            line=simple.line_number + 1,
            category="semantic consistency",
            confidence=0.95,
            blocking=True,
            source_provenance={
                "role": ROLE_BASIS_CONFIG,
                "simple_basis_count": len(simple.basis_sets),
                "has_basis_block": has_basis_block,
            },
            fix_hints=[
                "Add a basis set to the '!'-line (e.g. def2-TZVP, 6-31G*)",
                'Or declare per-element basis via %basis NewGTO <El> "<basis>" end',
            ],
            actions=[
                {
                    "kind": "set_keyword",
                    "keyword": "basis",
                    "target": str(input_path),
                    "safe_to_auto_apply": False,
                }
            ],
            facts={
                "simple_basis_sets": list(simple.basis_sets),
                "has_basis_block": has_basis_block,
            },
            artifact_roles=[ROLE_BASIS_CONFIG, ROLE_SIMPLE_KEYWORDS],
            domain_tags=["semantic", "blocking"],
        )
    )
    return out


def _low_maxiter_diagnostics(
    result: ParseResult, input_path: Path, intent: dict[str, Any] | None
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    scf_block = next((b for b in result.percent_blocks if b.name == "scf"), None)
    if scf_block is None:
        return out
    maxiter_raw = scf_block.parameters.get("maxiter")
    if maxiter_raw is None:
        return out
    try:
        maxiter = int(str(maxiter_raw).split()[0])
    except (ValueError, IndexError):
        return out
    threshold = int((intent or {}).get("scf_maxiter_warning", DEFAULT_MAXITER_WARNING))
    if maxiter < threshold:
        out.append(
            _diag(
                code=CODE_LOW_MAXITER,
                severity="warning",
                message=(
                    f"%scf maxiter={maxiter} is below the conservative workflow "
                    f"threshold ({threshold}); SCF may fail to converge"
                ),
                path=input_path,
                line=scf_block.line_start + 1,
                category="preflight/runtime-risk",
                confidence=0.8,
                blocking=False,
                source_provenance={
                    "role": ROLE_METHOD_CONFIG,
                    "keyword": "maxiter",
                    "threshold_source": (
                        "intent" if "scf_maxiter_warning" in (intent or {}) else "default"
                    ),
                },
                fix_hints=[
                    f"Raise %scf maxiter to at least {threshold}",
                    "Or document the lower cap in the intent contract",
                ],
                actions=[
                    {
                        "kind": "set_keyword",
                        "keyword": "maxiter",
                        "value": str(threshold),
                        "target": str(input_path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={"maxiter": maxiter, "threshold": threshold},
                artifact_roles=[ROLE_METHOD_CONFIG],
                domain_tags=["preflight", "runtime-risk"],
            )
        )
    return out


# --- version-aware-keywords ------------------------------------------------


def resolve_version_assumption(intent: dict[str, Any] | None) -> dict[str, Any]:
    """Resolve the explicit runtime/version assumption for this preflight run.

    When the exact runtime/image version is unknown we record that fact
    explicitly rather than guessing, per the issue's version-assumptions
    acceptance criterion. The intent contract can override ``software_version``
    (e.g. ``orca >=5.0``); otherwise we fall back to the schema version the
    builtin keyword set was authored against.
    """
    intent = intent or {}
    software_version = intent.get("software_version")
    runtime_image = intent.get("runtime_image")
    assumption: dict[str, Any] = {
        "software": "orca",
        "software_version": software_version or "unknown",
        "runtime_image": runtime_image or "unknown",
        "schema_source": intent.get("schema_source", "orca-lsp builtin keyword catalog"),
        # The fallback is intentional and explicit so consumers never have to
        # guess whether ``unknown`` means "not checked" or "could not determine".
        "exact_runtime_known": bool(software_version or runtime_image),
    }
    if software_version or runtime_image:
        assumption["declared_by"] = "intent"
    else:
        assumption["declared_by"] = "fallback"
    return assumption


def _keyword_version_mismatch_diagnostics(
    result: ParseResult,
    input_path: Path,
    version_assumption: dict[str, Any],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    simple = result.simple_input
    if simple is None:
        return out
    # A double-hybrid functional (e.g. B2PLYP) implies an MP2-style correlation
    # step; combining it with an explicit RI-MP2/MP2 simple keyword is a real
    # version/method compatibility finding the parent probe can act on.
    methods_upper = {m.upper() for m in simple.methods}
    double_hybrid = any(
        DFT_FUNCTIONALS.get(name, {}).get("type") == "double-hybrid" for name in simple.methods
    )
    explicit_mp2 = bool(methods_upper & {"MP2", "RI-MP2", "SCS-MP2"})
    if double_hybrid and explicit_mp2:
        out.append(
            _diag(
                code=CODE_KEYWORD_VERSION_MISMATCH,
                severity="error",
                message=(
                    "A double-hybrid functional combined with an explicit MP2 keyword "
                    "is not a valid method combination"
                ),
                path=input_path,
                line=simple.line_number + 1,
                category="schema",
                confidence=0.92,
                blocking=True,
                source_provenance={
                    "role": ROLE_SIMPLE_KEYWORDS,
                    "methods": list(simple.methods),
                    "schema_source": "orca-lsp builtin functional catalog",
                },
                fix_hints=[
                    "Remove the explicit MP2 keyword when using a double-hybrid functional",
                    "Or replace the double-hybrid functional with a non-hybrid method",
                ],
                actions=[
                    {
                        "kind": "remove_keyword",
                        "keyword": "MP2",
                        "target": str(input_path),
                        "safe_to_auto_apply": False,
                    }
                ],
                facts={
                    "methods": list(simple.methods),
                    "double_hybrid": double_hybrid,
                    "explicit_mp2": explicit_mp2,
                },
                artifact_roles=[ROLE_SIMPLE_KEYWORDS],
                domain_tags=["schema", "version-aware", "blocking"],
                version_assumption=version_assumption,
                manual_ref="orca-lsp builtin functional catalog",
            )
        )
    return out


def _version_assumption_diagnostic(
    version_assumption: dict[str, Any],
    intent: dict[str, Any] | None,
    input_path: Path,
) -> list[dict[str, Any]]:
    """Emit an explicit information diagnostic when the runtime version is unknown.

    This makes the version assumption machine-readable in the diagnostic stream
    itself (not just metadata) so the parent probe can surface it without
    parsing the envelope top-level.
    """
    if version_assumption["exact_runtime_known"]:
        return []
    return [
        _diag(
            code=CODE_VERSION_ASSUMPTION,
            severity="information",
            message=(
                "Exact ORCA runtime/image version is unknown; preflight validated "
                "against the builtin keyword catalog"
            ),
            path=input_path,
            line=1,
            category="preflight/runtime-risk",
            confidence=1.0,
            blocking=False,
            source_provenance={
                "role": ROLE_PRIMARY_INPUT,
                "reason": "software_version and runtime_image not declared in intent",
            },
            fix_hints=[
                "Declare software_version/runtime_image in the intent contract",
            ],
            actions=[],
            facts={
                "software_version": version_assumption["software_version"],
                "runtime_image": version_assumption["runtime_image"],
                "schema_source": version_assumption["schema_source"],
            },
            artifact_roles=[ROLE_PRIMARY_INPUT],
            domain_tags=["version-aware", "assumption"],
            version_assumption=version_assumption,
            intent=dict(intent) if intent else None,
        )
    ]


# --- fleet-regression-fixtures --------------------------------------------


def fleet_manifest(
    *,
    fixtures: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Return a machine-readable preflight manifest for the parent fleet.

    The parent ``bohrium_skills`` probe/report workflow consumes this to know
    which preflight codes exist, which capabilities are implemented, and which
    fixtures exercise them. Keeping it as data (not README prose) means the
    fleet regression evidence stays in sync with the implementation.
    """
    codes = {
        CODE_MISSING_SIMPLE_INPUT: {
            "severity": "error",
            "category": "semantic consistency",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "no '!'-prefixed simple input line with method/basis",
        },
        CODE_MISSING_GEOMETRY: {
            "severity": "error",
            "category": "cross-file reference",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "no '* xyz ... *' coordinate block parsed",
        },
        CODE_MULTIPLICITY_CHARGE: {
            "severity": "error",
            "category": "semantic consistency",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "geometry multiplicity < 1",
        },
        CODE_UNRESOLVED_WFN_REFERENCE: {
            "severity": "warning",
            "category": "cross-file reference",
            "blocking": False,
            "capability": "cross-artifact-graph",
            "summary": "%moinp GBW wavefunction file cannot be resolved",
        },
        CODE_UNKNOWN_KEYWORD: {
            "severity": "warning",
            "category": "schema",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "simple-input token not in builtin keyword catalog",
        },
        CODE_MISSING_BASIS_CONFIG: {
            "severity": "error",
            "category": "semantic consistency",
            "blocking": True,
            "capability": "cross-artifact-graph",
            "summary": "no basis set on '!'-line or in %basis NewGTO block",
        },
        CODE_LOW_MAXITER: {
            "severity": "warning",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "%scf maxiter below conservative workflow threshold",
        },
        CODE_VERSION_ASSUMPTION: {
            "severity": "information",
            "category": "preflight/runtime-risk",
            "blocking": False,
            "capability": "version-aware-keywords",
            "summary": "exact runtime version unknown; fallback schema used",
        },
        CODE_KEYWORD_VERSION_MISMATCH: {
            "severity": "error",
            "category": "schema",
            "blocking": True,
            "capability": "version-aware-keywords",
            "summary": "method combination not valid for the builtin keyword set",
        },
    }
    capabilities = {
        "version-aware-keywords": {
            "status": "available",
            "evidence_codes": [
                CODE_KEYWORD_VERSION_MISMATCH,
                CODE_VERSION_ASSUMPTION,
                CODE_UNKNOWN_KEYWORD,
                CODE_LOW_MAXITER,
            ],
        },
        "cross-artifact-graph": {
            "status": "available",
            "roles": list(ALL_ROLES),
            "evidence_codes": [
                CODE_MISSING_SIMPLE_INPUT,
                CODE_MISSING_GEOMETRY,
                CODE_MULTIPLICITY_CHARGE,
                CODE_UNRESOLVED_WFN_REFERENCE,
                CODE_MISSING_BASIS_CONFIG,
            ],
        },
        "code-actions": {
            "status": "available",
            "blocking_gate": "orca-lsp-tool check --fail-on-blocking",
            "evidence_codes": list(codes.keys()),
        },
        "fleet-regression-fixtures": {
            "status": "available",
            "fixtures": list(fixtures) if fixtures else [],
        },
    }
    return {
        "software": "orca",
        "preflight_envelope": "DiagnosticEnvelope/v1",
        "artifact_roles": list(ALL_ROLES),
        "capabilities": capabilities,
        "codes": codes,
    }
