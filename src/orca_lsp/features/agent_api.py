"""Machine-readable code-intelligence API for AI coding agents."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from lsprotocol.types import Diagnostic

from ..keywords import (
    BASIS_SETS,
    DFT_FUNCTIONALS,
    JOB_TYPES,
    PERCENT_BLOCKS,
    WAVEFUNCTION_METHODS,
)
from ..parser import ORCAParser
from ..validator import ORCAValidator


# ---------------------------------------------------------------------------
# Section parameter schemas (used by lookup_section / lookup_keyword)
# ---------------------------------------------------------------------------

SECTION_PARAMETERS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "scf": {
        "Convergence": {
            "type": "enum",
            "values": ["Tight", "Loose", "Normal"],
            "description": "SCF convergence threshold level",
        },
        "MaxIter": {
            "type": "integer",
            "min": 1,
            "max": 10000,
            "default": 50,
            "description": "Maximum number of SCF iterations",
        },
        "Guess": {
            "type": "enum",
            "values": ["PAtom", "Hueckel", "MORead", "SAD", "SADRI", "None"],
            "description": "Initial guess for the SCF",
        },
        "Shift": {
            "type": "float",
            "description": "Level shift applied to virtual orbitals",
        },
        "Damp": {
            "type": "float",
            "min": 0.0,
            "max": 1.0,
            "description": "Damping factor for SCF iterations",
        },
        "SlopeEval": {
            "type": "enum",
            "values": ["DCOSK", "DEFMAP", "CJ"],
            "description": "Slope evaluation method for DIIS",
        },
    },
    "pal": {
        "nprocs": {
            "type": "integer",
            "min": 1,
            "max": 4096,
            "description": "Number of parallel processes",
        },
        "OmpThreads": {
            "type": "integer",
            "min": 1,
            "max": 256,
            "description": "Number of OpenMP threads per process",
        },
    },
    "mp2": {
        "MP2_UseMP2OS": {
            "type": "boolean",
            "description": "Use opposite-spin MP2",
        },
        "MP2_UseMP2SS": {
            "type": "boolean",
            "description": "Use same-spin MP2",
        },
        "MP2_SpinComponentScale": {
            "type": "float",
            "description": "Scaling factor for spin-component scaled MP2",
        },
        "RI": {
            "type": "boolean",
            "description": "Use resolution-of-identity for MP2",
        },
    },
    "method": {
        "D3": {"type": "boolean", "description": "Enable Grimme D3 dispersion"},
        "D3BJ": {"type": "boolean", "description": "Enable Grimme D3 with Becke-Johnson damping"},
        "D4": {"type": "boolean", "description": "Enable Grimme D4 dispersion"},
        "GridX": {
            "type": "enum",
            "values": ["Grid1", "Grid2", "Grid3", "Grid4", "Grid5", "Grid6", "Grid7"],
            "description": "Integration grid size for DFT",
        },
        "FinalGridX": {
            "type": "enum",
            "values": ["Grid1", "Grid2", "Grid3", "Grid4", "Grid5", "Grid6", "Grid7"],
            "description": "Final integration grid for DFT energy evaluation",
        },
    },
    "geom": {
        "MaxIter": {
            "type": "integer",
            "min": 1,
            "max": 10000,
            "default": 50,
            "description": "Maximum geometry optimization steps",
        },
        "TolMAXDisp": {
            "type": "float",
            "description": "Maximum displacement convergence threshold",
        },
        "TolRMSG": {
            "type": "float",
            "description": "RMS gradient convergence threshold",
        },
        "Constraints": {
            "type": "block",
            "description": "Geometric constraints block",
        },
    },
    "freq": {
        "Temp": {
            "type": "float",
            "min": 0.0,
            "description": "Temperature for thermochemistry (Kelvin)",
        },
        "ScaleFreq": {
            "type": "float",
            "min": 0.0,
            "max": 2.0,
            "description": "Frequency scaling factor",
        },
        "AnFreq": {
            "type": "boolean",
            "description": "Use analytical frequencies",
        },
    },
    "tddft": {
        "NRoots": {
            "type": "integer",
            "min": 1,
            "max": 500,
            "description": "Number of excited states to compute",
        },
        "IRoot": {
            "type": "integer",
            "min": 1,
            "description": "Specific root for gradient calculation",
        },
        "TDA": {
            "type": "boolean",
            "description": "Use Tamm-Dancoff approximation",
        },
        "DoNTO": {
            "type": "boolean",
            "description": "Compute natural transition orbitals",
        },
    },
    "cpcm": {
        "epsilon": {
            "type": "float",
            "min": 1.0,
            "description": "Dielectric constant of solvent",
        },
        "SurfaceType": {
            "type": "enum",
            "values": ["VDW", "SES", "SAS"],
            "description": "Molecular surface type",
        },
    },
    "output": {
        "XYZFile": {
            "type": "boolean",
            "description": "Write final geometry as XYZ file",
        },
        "BasisFile": {
            "type": "boolean",
            "description": "Write basis set to file",
        },
        "MoldenFile": {
            "type": "boolean",
            "description": "Write orbitals in Molden format",
        },
        "PrintLevel": {
            "type": "enum",
            "values": ["MiniPrint", "SmallPrint", "NormalPrint", "LargePrint"],
            "description": "Amount of output detail",
        },
    },
    "maxcore": {
        "memory": {
            "type": "integer",
            "min": 100,
            "max": 65536,
            "description": "Memory per core in MB",
        },
    },
    "basis": {
        "newGTO": {
            "type": "string",
            "description": "Assign a new basis set to an element (e.g., newGTO H 'cc-pVTZ' end)",
        },
        "newAuxGTO": {
            "type": "string",
            "description": "Assign auxiliary basis set to an element",
        },
    },
    "cis": {
        "NRoots": {
            "type": "integer",
            "min": 1,
            "max": 500,
            "description": "Number of excited states for CIS/TDHF",
        },
    },
    "eprnmr": {
        "gtensor": {
            "type": "integer",
            "values": [0, 1],
            "description": "Compute g-tensor (0=off, 1=on)",
        },
        "nucgtensor": {
            "type": "integer",
            "values": [0, 1],
            "description": "Compute nuclear g-tensor contribution",
        },
        "hfcoupling": {
            "type": "integer",
            "values": [0, 1],
            "description": "Compute hyperfine coupling",
        },
    },
    "md": {
        "TimeStep": {
            "type": "float",
            "min": 0.01,
            "description": "Molecular dynamics timestep in fs",
        },
        "NSteps": {
            "type": "integer",
            "min": 1,
            "description": "Number of MD steps",
        },
    },
    "rirpa": {
        "nroots": {
            "type": "integer",
            "min": 1,
            "max": 500,
            "description": "Number of roots for RI-RPA/GW calculation",
        },
    },
}

# ---------------------------------------------------------------------------
# Example ORCA inputs (used by get_examples)
# ---------------------------------------------------------------------------

ORCA_EXAMPLES: Dict[str, Dict[str, str]] = {
    "single_point": {
        "title": "Single Point Energy Calculation",
        "description": "Compute the energy of a molecule at a fixed geometry using B3LYP/def2-TZVP.",
        "input": (
            "! B3LYP def2-TZVP TightSCF\n"
            "%maxcore 4000\n"
            "%pal nprocs 4 end\n"
            "\n"
            "* xyz 0 1\n"
            "  O   0.0000   0.0000   0.1173\n"
            "  H   0.0000   0.7572  -0.4692\n"
            "  H   0.0000  -0.7572  -0.4692\n"
            "*\n"
        ),
    },
    "optimization": {
        "title": "Geometry Optimization",
        "description": "Optimize molecular geometry followed by frequency analysis using PBE0/def2-SVP.",
        "input": (
            "! OPT FREQ PBE0 def2-SVP D3BJ\n"
            "%maxcore 2000\n"
            "%pal nprocs 4 end\n"
            "%geom\n"
            "  MaxIter 100\n"
            "end\n"
            "\n"
            "* xyz 0 1\n"
            "  C   0.0000   0.0000   0.0000\n"
            "  H   0.0000   0.0000   1.0890\n"
            "  H   1.0267   0.0000  -0.3630\n"
            "  H  -0.5133  -0.8892  -0.3630\n"
            "  H  -0.5133   0.8892  -0.3630\n"
            "*\n"
        ),
    },
    "frequency": {
        "title": "Frequency Calculation",
        "description": "Standalone frequency calculation at the B3LYP/def2-TZVP level.",
        "input": (
            "! FREQ B3LYP def2-TZVP\n"
            "%maxcore 4000\n"
            "%freq\n"
            "  Temp 298.15\n"
            "  ScaleFreq 0.96\n"
            "end\n"
            "\n"
            "* xyz 0 1\n"
            "  N   0.0000   0.0000   0.0000\n"
            "  N   0.0000   0.0000   1.0977\n"
            "*\n"
        ),
    },
    "td_dft": {
        "title": "TD-DFT Excited States",
        "description": "Time-dependent DFT calculation for excited states using CAM-B3LYP/def2-TZVP.",
        "input": (
            "! TD-DFT CAM-B3LYP def2-TZVP TightSCF\n"
            "%maxcore 4000\n"
            "%pal nprocs 4 end\n"
            "%tddft\n"
            "  NRoots 10\n"
            "  TDA false\n"
            "end\n"
            "\n"
            "* xyz 0 1\n"
            "  C   0.0000   0.0000   0.0000\n"
            "  O   0.0000   0.0000   1.2080\n"
            "  H   0.9657   0.0000  -0.5408\n"
            "  H  -0.9657   0.0000  -0.5408\n"
            "*\n"
        ),
    },
    "mp2": {
        "title": "MP2 Single Point",
        "description": "RI-MP2 single point energy with def2-TZVP/C auxiliary basis.",
        "input": (
            "! RI-MP2 def2-TZVP def2-TZVP/C TightSCF\n"
            "%maxcore 4000\n"
            "%pal nprocs 4 end\n"
            "%mp2\n"
            "  RI true\n"
            "end\n"
            "\n"
            "* xyz 0 1\n"
            "  O   0.0000   0.0000   0.1173\n"
            "  H   0.0000   0.7572  -0.4692\n"
            "  H   0.0000  -0.7572  -0.4692\n"
            "*\n"
        ),
    },
    "ccsd": {
        "title": "DLPNO-CCSD(T) Single Point",
        "description": "Domain-based local pair natural orbital CCSD(T) for large molecules.",
        "input": (
            "! DLPNO-CCSD(T) def2-TZVP TightSCF\n"
            "%maxcore 4000\n"
            "%pal nprocs 8 end\n"
            "\n"
            "* xyz 0 1\n"
            "  C   0.0000   1.3950   0.0000\n"
            "  C   1.2080   0.6975   0.0000\n"
            "  C   1.2080  -0.6975   0.0000\n"
            "  C   0.0000  -1.3950   0.0000\n"
            "  C  -1.2080  -0.6975   0.0000\n"
            "  C  -1.2080   0.6975   0.0000\n"
            "  H   0.0000   2.4710   0.0000\n"
            "  H   2.1420   1.2390   0.0000\n"
            "  H   2.1420  -1.2390   0.0000\n"
            "  H   0.0000  -2.4710   0.0000\n"
            "  H  -2.1420  -1.2390   0.0000\n"
            "  H  -2.1420   1.2390   0.0000\n"
            "*\n"
        ),
    },
}

# ---------------------------------------------------------------------------
# Next-token suggestion helpers
# ---------------------------------------------------------------------------

_SUGGESTION_FUNCTIONALS = sorted(DFT_FUNCTIONALS.keys())
_SUGGESTION_METHODS = sorted(WAVEFUNCTION_METHODS.keys())
_SUGGESTION_BASIS = sorted(BASIS_SETS.keys())
_SUGGESTION_JOB_TYPES = sorted(JOB_TYPES.keys())
_SUGGESTION_BLOCKS = sorted(PERCENT_BLOCKS.keys())


def _collect_simple_line_suggestions() -> List[Dict[str, str]]:
    """Build suggestion list for tokens after the ! line."""
    items: List[Dict[str, str]] = []
    for jt in _SUGGESTION_JOB_TYPES:
        desc = JOB_TYPES[jt]["description"]
        items.append({"token": jt, "type": "job_type", "description": desc})
    for func in _SUGGESTION_FUNCTIONALS:
        desc = DFT_FUNCTIONALS[func].get("description", "")
        items.append({"token": func, "type": "functional", "description": desc})
    for meth in _SUGGESTION_METHODS:
        desc = WAVEFUNCTION_METHODS[meth]["description"]
        items.append({"token": meth, "type": "method", "description": desc})
    for basis in _SUGGESTION_BASIS:
        desc = BASIS_SETS[basis].get("description", "")
        items.append({"token": basis, "type": "basis_set", "description": desc})
    return items


@dataclass
class AgentAPISnapshot:
    uri: str = ""
    version: Optional[int] = None
    diagnostics: List[Dict[str, Any]] = field(default_factory=list)
    outline: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(
            {
                "uri": self.uri,
                "version": self.version,
                "diagnostics": self.diagnostics,
                "outline": self.outline,
                "metadata": self.metadata,
            },
            indent=2,
        )


def _diag_to_dict(d: Diagnostic) -> Dict[str, Any]:
    return {
        "line": d.range.start.line,
        "character": d.range.start.character,
        "severity": d.severity,
        "message": d.message,
        "code": d.code,
        "source": d.source,
    }


class AgentAPIProvider:
    def __init__(self) -> None:
        self._parser = ORCAParser()
        self._validator = ORCAValidator()

    # ------------------------------------------------------------------
    # Existing snapshot API
    # ------------------------------------------------------------------

    def get_snapshot(
        self,
        source: str,
        uri: str = "",
        version: Optional[int] = None,
        diagnostics: Optional[List[Diagnostic]] = None,
    ) -> AgentAPISnapshot:
        diag_dicts = [_diag_to_dict(d) for d in (diagnostics or [])]
        outline = self._build_outline(source)
        return AgentAPISnapshot(
            uri=uri,
            version=version,
            diagnostics=diag_dicts,
            outline=outline,
            metadata={
                "language": "orca",
                "provider": "orca_lsp",
                "feature_count": {"diagnostics": len(diag_dicts), "outline_items": len(outline)},
            },
        )

    def _build_outline(self, source: str) -> List[Dict[str, Any]]:
        outline: List[Dict[str, Any]] = []
        lines = source.splitlines()
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped and not stripped.startswith("!") and not stripped.startswith("#"):
                outline.append({"line": i, "text": stripped[:80], "type": "content"})
        return outline

    def get_diagnostics_json(
        self, source: str, uri: str = "", diagnostics: Optional[List[Diagnostic]] = None
    ) -> str:
        snap = self.get_snapshot(source, uri, diagnostics=diagnostics)
        return json.dumps(
            {"uri": snap.uri, "diagnostics": snap.diagnostics, "count": len(snap.diagnostics)},
            indent=2,
        )

    def get_outline_json(self, source: str, uri: str = "") -> str:
        snap = self.get_snapshot(source, uri)
        return json.dumps({"uri": snap.uri, "outline": snap.outline}, indent=2)

    # ------------------------------------------------------------------
    # #52 - Domain language description
    # ------------------------------------------------------------------

    def describe_domain_language(self) -> Dict[str, Any]:
        """Return a structured description of the ORCA input language.

        Covers the route line, key blocks, coordinate sections, output
        blocks, and associated file types.
        """
        return {
            "language": "ORCA Input",
            "version": "5.x",
            "structure": {
                "route_line": {
                    "prefix": "!",
                    "description": (
                        "The simple input line defines the calculation level. "
                        "It starts with ! and contains method, basis set, job type, "
                        "and modifier keywords separated by spaces."
                    ),
                    "example": "! B3LYP def2-TZVP OPT TightSCF D3BJ",
                    "components": [
                        {
                            "name": "method",
                            "description": "DFT functional or wavefunction method",
                            "examples": ["B3LYP", "PBE0", "HF", "MP2", "CCSD(T)", "DLPNO-CCSD(T)"],
                        },
                        {
                            "name": "basis_set",
                            "description": "Basis set for the calculation",
                            "examples": ["def2-SVP", "def2-TZVP", "cc-pVTZ", "6-31G*"],
                        },
                        {
                            "name": "job_type",
                            "description": "Type of calculation to perform",
                            "examples": ["SP", "OPT", "FREQ", "OPT FREQ", "TS", "IRC"],
                        },
                        {
                            "name": "modifiers",
                            "description": "Convergence, dispersion, and other modifiers",
                            "examples": [
                                "TightSCF",
                                "LooseSCF",
                                "D3BJ",
                                "D3",
                                "D4",
                                "RIJCOSX",
                                "ZORA",
                                "CPCM",
                                "SMD",
                            ],
                        },
                    ],
                },
                "key_blocks": {
                    "prefix": "%",
                    "description": (
                        "Key blocks provide detailed control over calculation "
                        "parameters. They start with %name and end with 'end'."
                    ),
                    "blocks": [
                        {
                            "name": "scf",
                            "description": "SCF convergence settings",
                            "example": "%scf\n  MaxIter 100\n  Convergence Tight\nend",
                        },
                        {
                            "name": "pal",
                            "description": "Parallelization settings",
                            "example": "%pal\n  nprocs 8\nend",
                        },
                        {
                            "name": "mp2",
                            "description": "MP2-specific settings",
                            "example": "%mp2\n  RI true\nend",
                        },
                        {
                            "name": "method",
                            "description": "Method settings (dispersion, grid)",
                            "example": "%method\n  D3BJ true\nend",
                        },
                        {
                            "name": "geom",
                            "description": "Geometry optimization settings",
                            "example": "%geom\n  MaxIter 100\nend",
                        },
                        {
                            "name": "basis",
                            "description": "Custom basis set assignments",
                            "example": '%basis\n  newGTO H "cc-pVTZ" end\nend',
                        },
                        {
                            "name": "tddft",
                            "description": "Time-dependent DFT excited states",
                            "example": "%tddft\n  NRoots 10\nend",
                        },
                        {
                            "name": "cpcm",
                            "description": "Implicit solvation model",
                            "example": "%cpcm\n  epsilon 80.4\nend",
                        },
                        {
                            "name": "freq",
                            "description": "Frequency calculation settings",
                            "example": "%freq\n  Temp 298.15\nend",
                        },
                        {
                            "name": "output",
                            "description": "Output file generation settings",
                            "example": "%output\n  XYZFile true\nend",
                        },
                        {
                            "name": "eprnmr",
                            "description": "EPR/NMR property calculations",
                            "example": "%eprnmr\n  gtensor 1\nend",
                        },
                        {
                            "name": "md",
                            "description": "Molecular dynamics settings",
                            "example": "%md\n  TimeStep 0.5\n  NSteps 1000\nend",
                        },
                    ],
                    "single_line_blocks": [
                        {
                            "name": "maxcore",
                            "description": "Set memory per core in MB",
                            "example": "%maxcore 4000",
                        },
                        {
                            "name": "moinp",
                            "description": "Read initial MOs from a previous calculation",
                            "example": '%moinp "previous.gbw"',
                        },
                    ],
                },
                "coordinate_sections": {
                    "prefix": "*",
                    "description": (
                        "Molecular geometry is specified between * xyz (or * int) "
                        "and a closing * line. The header contains charge and multiplicity."
                    ),
                    "formats": [
                        {
                            "name": "xyz",
                            "description": "Cartesian coordinates",
                            "example": (
                                "* xyz 0 1\n"
                                "  O   0.0   0.0   0.1173\n"
                                "  H   0.0   0.7572 -0.4692\n"
                                "  H   0.0  -0.7572 -0.4692\n"
                                "*"
                            ),
                        },
                        {
                            "name": "int",
                            "description": "Internal (Z-matrix) coordinates",
                            "example": (
                                "* int 0 0\n"
                                "  O 0 0 0 0.0 0.0 0.0\n"
                                "  H 1 0 0 0.96 0.0 0.0\n"
                                "*"
                            ),
                        },
                    ],
                },
                "output_blocks": {
                    "description": "ORCA writes several output files after calculation.",
                    "files": [
                        {"extension": ".out", "description": "Main output log with all calculation details"},
                        {"extension": ".gbw", "description": "Gaussian basis set wavefunction file (orbitals)"},
                        {"extension": ".hessian", "description": "Hessian matrix from frequency calculations"},
                        {"extension": ".cit", "description": "CI vectors for excited state calculations"},
                        {"extension": ".engrad", "description": "Energy and gradient for geometry optimizations"},
                        {"extension": ".inp", "description": "Echo of the input file"},
                        {"extension": ".molden", "description": "Orbitals in Molden format for visualization"},
                        {"extension": ".xyz", "description": "Final geometry in XYZ format"},
                        {"extension": ".prop", "description": "Molecular properties"},
                    ],
                },
            },
            "file_types": {
                "input": [".inp"],
                "output": [".out", ".gbw", ".hessian", ".cit", ".engrad", ".molden", ".xyz", ".prop"],
                "auxiliary": [".moinp", ".cis", ".cisp", ".nto"],
            },
        }

    # ------------------------------------------------------------------
    # #53 - Schema lookup for sections and keywords
    # ------------------------------------------------------------------

    def lookup_section(self, name: str) -> Dict[str, Any]:
        """Look up an ORCA key block by name.

        Returns the block description, example, and parameter schema.
        If the name is not found, returns a not-found result.
        """
        normalized = name.lower().strip()
        block_info = PERCENT_BLOCKS.get(normalized)
        params = SECTION_PARAMETERS.get(normalized, {})

        result: Dict[str, Any] = {
            "section": normalized,
            "found": block_info is not None or bool(params),
        }
        if block_info:
            result["description"] = block_info["description"]
            result["example"] = block_info["example"]
        if params:
            result["parameters"] = params
        elif block_info:
            result["parameters"] = {}
        return result

    def lookup_keyword(self, section: str, keyword: str) -> Dict[str, Any]:
        """Look up a specific keyword within an ORCA key block.

        Returns the parameter definition (type, constraints, description).
        """
        normalized_section = section.lower().strip()
        normalized_keyword = keyword.lower().strip()

        # Case-insensitive lookup over parameter keys
        params = SECTION_PARAMETERS.get(normalized_section, {})
        for param_name, param_def in params.items():
            if param_name.lower() == normalized_keyword:
                return {
                    "section": normalized_section,
                    "keyword": param_name,
                    "found": True,
                    "definition": param_def,
                }

        return {
            "section": normalized_section,
            "keyword": keyword,
            "found": False,
            "message": f"Keyword '{keyword}' not found in section '{section}'",
        }

    # ------------------------------------------------------------------
    # #54 - Examples and next-token suggestions
    # ------------------------------------------------------------------

    def get_examples(self) -> List[Dict[str, str]]:
        """Return curated example ORCA inputs for common calculation types.

        Each example has a key, title, description, and complete input text.
        """
        results: List[Dict[str, str]] = []
        for key, example in ORCA_EXAMPLES.items():
            results.append(
                {
                    "key": key,
                    "title": example["title"],
                    "description": example["description"],
                    "input": example["input"],
                }
            )
        return results

    def next_token_suggestions(self, context: str, prefix: str = "") -> List[Dict[str, Any]]:
        """Return context-aware next-token suggestions for ORCA input.

        Parameters
        ----------
        context : str
            The current line or partial input to base suggestions on.
        prefix : str
            An optional filter prefix.  Only tokens whose names start
            with this string (case-insensitive) are returned.
        """
        suggestions: List[Dict[str, Any]] = []

        stripped = context.strip()

        # After !  -> simple input keywords
        if stripped.startswith("!"):
            all_items = _collect_simple_line_suggestions()
            lower_prefix = prefix.lower()
            if lower_prefix:
                all_items = [item for item in all_items if item["token"].lower().startswith(lower_prefix)]
            return all_items

        # After %  -> key block names
        if stripped.startswith("%"):
            block_prefix = stripped[1:].strip()
            if prefix:
                block_prefix = prefix
            for block_name in _SUGGESTION_BLOCKS:
                if block_prefix and not block_name.lower().startswith(block_prefix.lower()):
                    continue
                block_info = PERCENT_BLOCKS[block_name]
                suggestions.append(
                    {
                        "token": block_name,
                        "type": "block",
                        "description": block_info["description"],
                        "example": block_info["example"],
                    }
                )
            return suggestions

        # Inside a coordinate section (looks like element coords)
        _COORD_RE = re.compile(r"^([A-Z][a-z]?)(\s|$)", re.IGNORECASE)
        if _COORD_RE.match(stripped):
            from ..keywords import ELEMENTS

            elem_prefix = prefix or stripped.split()[0]
            for elem in ELEMENTS:
                if elem.lower().startswith(elem_prefix.lower()):
                    suggestions.append(
                        {"token": elem, "type": "element", "description": f"Chemical element {elem}"}
                    )
            return suggestions

        return suggestions

    # ------------------------------------------------------------------
    # #59 - Machine-readable code intelligence API
    # ------------------------------------------------------------------

    def get_code_intelligence_api(self) -> Dict[str, Any]:
        """Return a machine-readable API description of all LSP capabilities.

        Designed for consumption by AI coding agents (Claude Code, OpenCode, Codex).
        """
        return {
            "name": "orca-lsp",
            "version": "1.0.0",
            "language": "orca",
            "description": "Language Server Protocol for ORCA quantum chemistry input files",
            "capabilities": {
                "diagnostics": {
                    "description": "Real-time validation and error detection for ORCA inputs",
                    "methods": ["get_diagnostics_json"],
                    "checks": [
                        "Missing simple input line",
                        "Missing method or basis set",
                        "Invalid element symbols in geometry",
                        "Mutually exclusive keyword combinations",
                        "Missing %maxcore recommendation",
                        "SCF type conflicts",
                        "Spin/charge consistency",
                        "Basis set compatibility warnings",
                    ],
                    "rule_codes": [
                        "ORCA-E024 (SCF convergence failure in output)",
                        "ORCA-E025 (Input parse / runtime error in output)",
                    ],
                },
                "completions": {
                    "description": "Context-aware completions for ORCA keywords",
                    "methods": ["next_token_suggestions"],
                    "contexts": [
                        "After ! -> methods, basis sets, job types, modifiers",
                        "After % -> key block names",
                        "In coordinates -> element symbols",
                    ],
                },
                "navigation": {
                    "description": "Document outline and symbol navigation",
                    "methods": ["get_outline_json"],
                    "features": [
                        "Block-level outline extraction",
                        "Simple input line detection",
                        "Geometry section identification",
                    ],
                },
                "formatting": {
                    "description": "Input file formatting and normalization",
                    "features": [
                        "Keyword case normalization",
                        "Indentation for block contents",
                    ],
                },
                "rename": {
                    "description": "Symbol renaming within input files",
                    "features": [
                        "Element label renaming",
                        "Keyword renaming with validation",
                    ],
                },
                "hover": {
                    "description": "Documentation on hover for keywords",
                    "features": [
                        "DFT functional descriptions",
                        "Basis set descriptions",
                        "Method descriptions",
                    ],
                },
                "domain_knowledge": {
                    "description": "ORCA domain language knowledge base",
                    "methods": [
                        "describe_domain_language",
                        "lookup_section",
                        "lookup_keyword",
                        "get_examples",
                    ],
                },
                "validation": {
                    "description": "Input validation with and without ORCA binary",
                    "methods": ["validate_input", "dry_run_options"],
                    "features": [
                        "Offline structural validation",
                        "Optional ORCA binary dry-run",
                    ],
                },
            },
            "api_methods": [
                {
                    "name": "get_snapshot",
                    "description": "Get complete document state snapshot",
                    "parameters": ["source", "uri", "version", "diagnostics"],
                    "returns": "AgentAPISnapshot",
                },
                {
                    "name": "get_diagnostics_json",
                    "description": "Get diagnostics as JSON",
                    "parameters": ["source", "uri", "diagnostics"],
                    "returns": "str (JSON)",
                },
                {
                    "name": "get_outline_json",
                    "description": "Get document outline as JSON",
                    "parameters": ["source", "uri"],
                    "returns": "str (JSON)",
                },
                {
                    "name": "describe_domain_language",
                    "description": "Get structured ORCA input language description",
                    "parameters": [],
                    "returns": "dict",
                },
                {
                    "name": "lookup_section",
                    "description": "Look up an ORCA key block schema",
                    "parameters": ["name"],
                    "returns": "dict",
                },
                {
                    "name": "lookup_keyword",
                    "description": "Look up a keyword within an ORCA section",
                    "parameters": ["section", "keyword"],
                    "returns": "dict",
                },
                {
                    "name": "get_examples",
                    "description": "Get curated example ORCA inputs",
                    "parameters": [],
                    "returns": "list[dict]",
                },
                {
                    "name": "next_token_suggestions",
                    "description": "Get context-aware completion suggestions",
                    "parameters": ["context", "prefix"],
                    "returns": "list[dict]",
                },
                {
                    "name": "get_code_intelligence_api",
                    "description": "Get machine-readable API capabilities description",
                    "parameters": [],
                    "returns": "dict",
                },
                {
                    "name": "validate_input",
                    "description": "Validate ORCA input text without ORCA binary",
                    "parameters": ["text"],
                    "returns": "dict",
                },
                {
                    "name": "dry_run_options",
                    "description": "Return available dry-run/validate commands",
                    "parameters": [],
                    "returns": "dict",
                },
            ],
            "agent_integration": {
                "description": "How to integrate with AI coding agents",
                "snapshot_usage": (
                    "Call get_snapshot() after every document change to get "
                    "the full state: diagnostics, outline, and metadata."
                ),
                "completion_usage": (
                    "Call next_token_suggestions(context, prefix) to get "
                    "relevant completion items based on cursor position."
                ),
                "domain_usage": (
                    "Call describe_domain_language() once to understand the "
                    "language. Use lookup_section/lookup_keyword for specific "
                    "parameter details. Use get_examples() for templates."
                ),
            },
        }

    # ------------------------------------------------------------------
    # #60 - Validation / dry-run integration
    # ------------------------------------------------------------------

    def validate_input(self, text: str) -> Dict[str, Any]:
        """Validate ORCA input text without requiring the ORCA binary.

        Performs structural validation: checks for required sections,
        valid keywords, element symbols, and consistency rules.
        Returns a dict with valid flag, errors, and warnings.
        """
        result = self._parser.parse(text)

        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        for err in result.errors:
            errors.append(
                {
                    "line": err.get("line", 0),
                    "message": err.get("message", ""),
                    "severity": err.get("severity", "error"),
                }
            )

        for warn in result.warnings:
            warnings.append(
                {
                    "line": warn.get("line", 0),
                    "message": warn.get("message", ""),
                    "severity": warn.get("severity", "warning"),
                }
            )

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "sections": {
                "has_simple_input": result.simple_input is not None,
                "has_geometry": result.geometry is not None,
                "block_count": len(result.percent_blocks),
            },
        }

    def dry_run_options(self) -> Dict[str, Any]:
        """Return available dry-run and validation commands.

        Describes the offline validation path and optional binary-based
        dry-run that users can enable by configuring the ORCA executable.
        """
        return {
            "offline_validation": {
                "method": "validate_input",
                "description": (
                    "Structural validation of ORCA input without the ORCA binary. "
                    "Checks for required sections, valid keywords, element symbols, "
                    "and consistency rules."
                ),
                "available": True,
                "requires_binary": False,
            },
            "binary_dry_run": {
                "method": "run_validation",
                "description": (
                    "Run ORCA executable on the input file in a temporary directory "
                    "to capture real error messages. Requires orca executable path."
                ),
                "available": False,
                "requires_binary": True,
                "config_fields": {
                    "executable": "Path to the ORCA binary (e.g., /usr/local/bin/orca)",
                    "timeout": "Timeout in seconds (default: 30)",
                    "enabled": "Set to true to enable binary validation",
                },
            },
            "log_parsing": {
                "method": "parse_log",
                "description": (
                    "Parse existing ORCA output/log files for runtime errors "
                    "(SCF convergence failures, input parse errors, segfaults)."
                ),
                "available": True,
                "requires_binary": False,
                "rule_codes": ["ORCA-E024", "ORCA-E025"],
            },
        }

    # ------------------------------------------------------------------
    # #69 - OpenQC smoke test and rule manifest
    # ------------------------------------------------------------------

    def get_rule_manifest(self) -> List[Dict[str, Any]]:
        """Export all diagnostic rules with codes, severities, and descriptions.

        Returns a list of rule descriptors that downstream tools (OpenQC
        dashboards, CI gates) can use to register and filter diagnostics.
        Each entry contains a stable ``code``, human-readable ``description``,
        and ``severity`` string.
        """
        from ..features.lint import (
            RULE_CHARGE_MULTIPLICITY,
            RULE_DUPLICATE_BLOCK,
            RULE_DUPLICATE_TOKEN,
            RULE_INVALID_BLOCK_TERMINATOR,
            RULE_INVALID_CHARGE,
            RULE_INVALID_MULTIPLICITY,
            RULE_MALFORMED_PAL,
            RULE_MISSING_COORD_TERMINATOR,
            RULE_MISSING_MAXCORE,
            RULE_MISSING_METHOD_BASIS,
            RULE_MISSING_XYZ_HEADER,
            RULE_NPROCS_HIGH,
            RULE_NONSTANDARD_TOKEN,
            RULE_MAXITER_RANGE,
            RULE_UNKNOWN_BLOCK,
            RULE_UNKNOWN_TOKEN,
            RULE_UNCLOSED_BLOCK,
        )
        from ..features.test_runner import (
            RULE_LOG_INPUT_PARSE_ERROR,
            RULE_LOG_SCF_NOT_CONVERGED,
        )

        rules: List[Dict[str, Any]] = [
            {
                "code": RULE_UNKNOWN_TOKEN,
                "severity": "error",
                "description": "Unknown token in simple input line",
            },
            {
                "code": RULE_UNKNOWN_BLOCK,
                "severity": "error",
                "description": "Unknown % block name",
            },
            {
                "code": RULE_UNCLOSED_BLOCK,
                "severity": "error",
                "description": "Unclosed % block",
            },
            {
                "code": RULE_DUPLICATE_BLOCK,
                "severity": "error",
                "description": "Duplicate % block",
            },
            {
                "code": RULE_INVALID_CHARGE,
                "severity": "error",
                "description": "Invalid charge value",
            },
            {
                "code": RULE_INVALID_MULTIPLICITY,
                "severity": "error",
                "description": "Invalid multiplicity value",
            },
            {
                "code": RULE_CHARGE_MULTIPLICITY,
                "severity": "error",
                "description": "Multiplicity incompatible with charge",
            },
            {
                "code": RULE_MISSING_MAXCORE,
                "severity": "warning",
                "description": "Suggested %maxcore not set or value very low",
            },
            {
                "code": RULE_NONSTANDARD_TOKEN,
                "severity": "warning",
                "description": "Non-standard token in simple input",
            },
            {
                "code": RULE_DUPLICATE_TOKEN,
                "severity": "warning",
                "description": "Duplicate token in simple input",
            },
            {
                "code": RULE_MAXITER_RANGE,
                "severity": "warning",
                "description": "SCF maxiter out of typical range",
            },
            {
                "code": RULE_NPROCS_HIGH,
                "severity": "warning",
                "description": "%pal nprocs unusually high",
            },
            {
                "code": RULE_MISSING_METHOD_BASIS,
                "severity": "warning",
                "description": "Missing method or basis set in route line",
            },
            {
                "code": RULE_MALFORMED_PAL,
                "severity": "error",
                "description": "Malformed %pal block (missing or invalid nprocs)",
            },
            {
                "code": RULE_MISSING_XYZ_HEADER,
                "severity": "error",
                "description": "Missing charge/multiplicity in * xyz header",
            },
            {
                "code": RULE_MISSING_COORD_TERMINATOR,
                "severity": "error",
                "description": "Coordinate block not terminated with * or end",
            },
            {
                "code": RULE_INVALID_BLOCK_TERMINATOR,
                "severity": "error",
                "description": "Key block missing proper end terminator",
            },
            {
                "code": RULE_LOG_SCF_NOT_CONVERGED,
                "severity": "error",
                "description": "SCF convergence failure in ORCA output",
            },
            {
                "code": RULE_LOG_INPUT_PARSE_ERROR,
                "severity": "error",
                "description": "Input parse or runtime error in ORCA output",
            },
        ]
        return rules

    def openqc_smoke(self) -> Dict[str, Any]:
        """Lightweight integration smoke test for OpenQC.

        Exercises the rule manifest, lint engine, and agent API to verify
        the orca-lsp service is wired correctly.  Returns a dict with
        ``ok`` (bool), ``checks`` (list of individual check results), and
        a summary ``message``.
        """
        checks: List[Dict[str, Any]] = []

        # Check 1: rule manifest is non-empty and well-formed.
        manifest = self.get_rule_manifest()
        codes = {r["code"] for r in manifest}
        has_required_fields = all(
            "code" in r and "severity" in r and "description" in r
            for r in manifest
        )
        checks.append(
            {
                "name": "rule_manifest",
                "ok": len(manifest) > 0 and len(codes) == len(manifest) and has_required_fields,
                "detail": f"{len(manifest)} rules, {len(codes)} unique codes",
            }
        )

        # Check 2: lint engine runs on a minimal valid input (H2, closed-shell).
        valid_input = (
            "! B3LYP def2-TZVP TightSCF\n"
            "%maxcore 4000\n"
            "\n"
            "* xyz 0 1\n"
            "  H   0.0   0.0   0.0\n"
            "  H   0.0   0.0   0.74\n"
            "*\n"
        )
        from ..features.lint import LintProvider

        lint = LintProvider()
        diags = lint.lint(valid_input)
        checks.append(
            {
                "name": "lint_engine_valid",
                "ok": len(diags) == 0,
                "detail": f"{len(diags)} diagnostics on valid input",
            }
        )

        # Check 3: lint engine detects errors on invalid input.
        invalid_input = "! B3LYP\n\n* xyz 0 1\n  H 0 0 0\n*\n"
        diags_invalid = lint.lint(invalid_input)
        checks.append(
            {
                "name": "lint_engine_invalid",
                "ok": len(diags_invalid) > 0,
                "detail": f"{len(diags_invalid)} diagnostics on invalid input",
            }
        )

        # Check 4: validate_input works.
        validation = self.validate_input(valid_input)
        checks.append(
            {
                "name": "validate_input",
                "ok": validation["valid"] is True,
                "detail": f"valid={validation['valid']}",
            }
        )

        # Check 5: agent API snapshot works.
        snap = self.get_snapshot(valid_input, uri="smoke://test")
        checks.append(
            {
                "name": "agent_api_snapshot",
                "ok": snap.uri == "smoke://test" and isinstance(snap.metadata, dict),
                "detail": f"uri={snap.uri}",
            }
        )

        all_ok = all(c["ok"] for c in checks)
        return {
            "ok": all_ok,
            "checks": checks,
            "message": "OpenQC smoke passed" if all_ok else "OpenQC smoke detected failures",
        }
