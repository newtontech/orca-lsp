"""Tests for package metadata."""

from importlib.metadata import version
from pathlib import Path

from orca_lsp import __version__


def test_runtime_version_matches_installed_metadata():
    """Runtime package version should match project metadata."""
    assert __version__ == version("orca-lsp")


def test_license_file_present():
    """Repository should ship the declared MIT license text."""
    license_text = Path("LICENSE").read_text(encoding="utf-8")
    assert "MIT License" in license_text
    assert "NewtonTech" in license_text
