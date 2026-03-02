"""Tests for ORCA parser."""
import pytest
from unittest.mock import MagicMock

from orca_lsp.parser import ORCAParser


class TestORCAParser:
    """Test ORCA parser."""

    def test_parser_initialization(self):
        """Test parser initialization."""
        parser = ORCAParser()
        assert parser is not None

    def test_parse_empty(self):
        """Test parsing empty content."""
        parser = ORCAParser()
        result = parser.parse("")
        assert result is not None
        assert hasattr(result, 'errors')
        assert hasattr(result, 'warnings')

    def test_parse_simple(self):
        """Test parsing simple input."""
        parser = ORCAParser()
        content = "! B3LYP def2-TZVP\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert result is not None

    def test_parse_with_errors(self):
        """Test parsing with errors."""
        parser = ORCAParser()
        content = "! INVALID_KEYWORD"
        result = parser.parse(content)
        assert result is not None
