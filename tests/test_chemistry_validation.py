"""Tests for chemistry keyword validation."""

import pytest

from orca_lsp.parser import ORCAParser


def parse_messages(content: str) -> list[str]:
    """Parse content and return diagnostic messages."""
    result = ORCAParser().parse(content)
    return [item["message"] for item in result.errors + result.warnings]


@pytest.mark.parametrize(
    ("simple_line", "expected_message"),
    [
        ("! B3LYP def2-SVP D3 D4", "Mutually exclusive dispersion corrections"),
        ("! B3LYP def2-SVP RIJCOSX RI-J", "Mutually exclusive RI approximations"),
        ("! BP86 B3LYP def2-SVP", "Mutually exclusive DFT functionals"),
        ("! MP2 CCSD(T) def2-SVP", "Mutually exclusive correlation methods"),
        ("! B3LYP def2-SVP def2-TZVP", "Mutually exclusive basis sets"),
        ("! B3LYP def2-SVP TightSCF LooseSCF", "Mutually exclusive SCF convergence"),
        ("! B3LYP def2-SVP ZORA DKH", "Mutually exclusive relativistic corrections"),
        ("! B3LYP def2-SVP CPCM SMD", "Mutually exclusive solvent models"),
    ],
)
def test_mutually_exclusive_keywords(simple_line: str, expected_message: str):
    """Mutually exclusive simple-line keywords should be reported as errors."""
    content = f"{simple_line}\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*"
    messages = parse_messages(content)

    assert any(expected_message in message for message in messages)


def test_hybrid_functional_with_mp2_warns():
    """Hybrid DFT plus MP2 should suggest a double-hybrid functional."""
    messages = parse_messages("! B3LYP MP2 def2-SVP\n%maxcore 2000\n* xyz 0 1\nH 0 0 0\n*")

    assert any("double-hybrid" in message for message in messages)
