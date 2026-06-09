"""Regression tests for public ORCA input fixtures."""

from pathlib import Path

import pytest

from orca_lsp.parser import ORCAParser

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "orca_public_examples"


@pytest.mark.parametrize(
    (
        "fixture_name",
        "expected_methods",
        "expected_basis_sets",
        "expected_job_types",
        "expected_other_keywords",
        "expected_block_names",
        "expected_geometry_format",
        "expected_atom_count",
    ),
    [
        (
            "butane_pes_scan.inp",
            {"B3LYP"},
            {"6-31G*"},
            set(),
            {"LargePrint"},
            {"output", "paras"},
            "int",
            14,
        ),
        (
            "benzene_geometry.inp",
            {"PBE"},
            {"cc-pVDZ"},
            {"OPT"},
            set(),
            set(),
            "xyz",
            12,
        ),
        (
            "water_optimization.inp",
            {"B3LYP"},
            {"def2-TZVP"},
            {"OPT"},
            {"TightSCF", "D3BJ", "RIJCOSX", "Grid4"},
            {"pal", "maxcore", "geom"},
            "xyz",
            3,
        ),
    ],
)
def test_public_orca_examples_parse_core_constructs(
    fixture_name: str,
    expected_methods: set[str],
    expected_basis_sets: set[str],
    expected_job_types: set[str],
    expected_other_keywords: set[str],
    expected_block_names: set[str],
    expected_geometry_format: str,
    expected_atom_count: int,
) -> None:
    parser = ORCAParser()
    source = (FIXTURE_DIR / fixture_name).read_text(encoding="utf-8")

    result = parser.parse(source)

    assert result.errors == []
    assert result.simple_input is not None
    assert expected_methods.issubset(result.simple_input.methods)
    assert expected_basis_sets.issubset(result.simple_input.basis_sets)
    assert expected_job_types.issubset(result.simple_input.job_types)
    assert expected_other_keywords.issubset(result.simple_input.other_keywords)

    assert expected_block_names.issubset({block.name for block in result.percent_blocks})
    assert result.geometry is not None
    assert result.geometry.format_type == expected_geometry_format
    assert len(result.geometry.atoms) == expected_atom_count


def test_public_water_optimization_detects_resource_blocks() -> None:
    parser = ORCAParser()
    source = (FIXTURE_DIR / "water_optimization.inp").read_text(encoding="utf-8")

    result = parser.parse(source)
    blocks = {block.name: block for block in result.percent_blocks}

    assert blocks["pal"].parameters["nprocs"] == 4
    assert blocks["maxcore"].parameters["memory"] == 2000
