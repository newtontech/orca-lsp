"""Tests for new blocks and keywords"""

from orca_lsp.parser import ORCAParser
from orca_lsp.keywords import PERCENT_BLOCKS


class TestNewPercentBlocks:
    def test_eprnmr_block_defined(self):
        assert "eprnmr" in PERCENT_BLOCKS

    def test_rirpa_block_defined(self):
        assert "rirpa" in PERCENT_BLOCKS

    def test_moinp_block_defined(self):
        assert "moinp" in PERCENT_BLOCKS


class TestNewBlockParsing:
    def test_eprnmr_parsing(self):
        parser = ORCAParser()
        content = "! B3LYP def2-TZVP\n%eprnmr gtensor 1 end\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1
        assert result.percent_blocks[0].name == "eprnmr"

    def test_rirpa_parsing(self):
        parser = ORCAParser()
        content = "! B3LYP def2-TZVP\n%rirpa nroots 10 end\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1
        assert result.percent_blocks[0].parameters.get("nroots") == 10


class TestNewBlockEdgeCases:
    def test_eprnmr_no_match(self):
        parser = ORCAParser()
        content = "! B3LYP def2-TZVP\n%eprnmr something 1 end\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1
        assert result.percent_blocks[0].parameters.get("gtensor") is None

    def test_rirpa_no_match(self):
        parser = ORCAParser()
        content = "! B3LYP def2-TZVP\n%rirpa something 10 end\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1
        assert result.percent_blocks[0].parameters.get("nroots") is None


class TestBlockRegexEdgeCases:
    def test_eprnmr_gtensor_no_number(self):
        parser = ORCAParser()
        content = "! B3LYP def2-TZVP\n%eprnmr\n gtensor abc\nend\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1
        assert result.percent_blocks[0].parameters.get("gtensor") is None

    def test_rirpa_nroots_no_number(self):
        parser = ORCAParser()
        content = "! B3LYP def2-TZVP\n%rirpa\n nroots abc\nend\n* xyz 0 1\nH 0 0 0\n*"
        result = parser.parse(content)
        assert len(result.percent_blocks) == 1
        assert result.percent_blocks[0].parameters.get("nroots") is None
