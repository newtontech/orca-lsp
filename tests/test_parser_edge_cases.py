"""Tests for parser edge cases: inline comments, quoted values, unusual spacing."""

import pytest

from orca_lsp.parser import ORCAParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def parser() -> ORCAParser:
    return ORCAParser()


# ===========================================================================
# 1. Inline comments in simple input lines
# ===========================================================================

class TestInlineCommentsInSimpleInput:
    """The '!' line may contain inline '!' comments after the keywords."""

    def test_inline_comment_stripped_from_tokens(self, parser: ORCAParser) -> None:
        """A second '!' on the simple input line should start a comment."""
        content = "! B3LYP def2-SVP ! this is a comment"
        result = parser.parse_simple_input(content, 0)
        assert "B3LYP" in result.methods
        assert "def2-SVP" in result.basis_sets
        # The comment text must NOT appear as a keyword.
        assert not any("this" in kw for kw in result.other_keywords)
        assert not any("comment" in kw for kw in result.other_keywords)

    def test_double_exclamation_preserves_keywords(self, parser: ORCAParser) -> None:
        content = "! HF 6-31G* !! double exclamation"
        result = parser.parse_simple_input(content, 0)
        assert "HF" in result.methods
        assert "6-31G*" in result.basis_sets
        assert not any("double" in kw for kw in result.other_keywords)

    def test_comment_with_special_chars(self, parser: ORCAParser) -> None:
        content = "! B3LYP def2-TZVP Opt ! B3LYP/def2-TZVP geometry opt"
        result = parser.parse_simple_input(content, 0)
        assert "B3LYP" in result.methods
        assert "def2-TZVP" in result.basis_sets
        assert "OPT" in result.job_types
        # The slash in the comment should not leak into tokens.
        assert not any("/" in kw for kw in result.other_keywords)


# ===========================================================================
# 2. Quoted values in parameter blocks
# ===========================================================================

class TestQuotedValuesInPercentBlocks:
    """Quoted strings (e.g. file paths, basis set names) inside % blocks."""

    def test_quoted_basis_set_name(self, parser: ORCAParser) -> None:
        """%basis newGTO H \"cc-pVTZ\" end — quoted value should not be split."""
        content = '%basis newGTO H "cc-pVTZ" end'
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "basis"
        # 'end' must be detected even with quoted strings on the same line.
        assert end_line == 0

    def test_quoted_filepath_in_moinp(self, parser: ORCAParser) -> None:
        content = '%moinp "previous.gbw"'
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "moinp"
        assert end_line == 0

    def test_multiline_block_with_quoted_value(self, parser: ORCAParser) -> None:
        content = '%basis\nnewGTO H\n"cc-pVTZ"\nend'
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "basis"
        assert end_line == 3

    def test_single_quoted_value(self, parser: ORCAParser) -> None:
        """Single-quoted values should also be preserved."""
        content = "%output xyzfile 'true'"
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "output"
        assert end_line == 0


# ===========================================================================
# 3. Unusual spacing (multiple spaces, tabs)
# ===========================================================================

class TestUnusualSpacing:
    """Tabs and multiple spaces should not break tokenization."""

    def test_multiple_spaces_in_simple_input(self, parser: ORCAParser) -> None:
        content = "!  B3LYP   def2-SVP    Opt"
        result = parser.parse_simple_input(content, 0)
        assert "B3LYP" in result.methods
        assert "def2-SVP" in result.basis_sets
        assert "OPT" in result.job_types

    def test_tabs_in_simple_input(self, parser: ORCAParser) -> None:
        content = "!\tB3LYP\tdef2-SVP\tOpt"
        result = parser.parse_simple_input(content, 0)
        assert "B3LYP" in result.methods
        assert "def2-SVP" in result.basis_sets
        assert "OPT" in result.job_types

    def test_tabs_in_percent_block_header(self, parser: ORCAParser) -> None:
        content = "%scf\tmaxiter\t100\tend"
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "scf"
        assert end_line == 0
        assert block.parameters.get("maxiter") == 100

    def test_trailing_spaces_in_geometry_atoms(self, parser: ORCAParser) -> None:
        content = "* xyz 0 1\nH    0.0   0.0   0.0  \nO    0.0   0.0   1.0  \n*"
        lines = content.split("\n")
        geom, end_line = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) == 2
        assert geom.atoms[0].element == "H"
        assert geom.atoms[1].element == "O"

    def test_tabs_between_atom_coordinates(self, parser: ORCAParser) -> None:
        content = "* xyz 0 1\nH\t0.0\t0.0\t0.0\n*"
        lines = content.split("\n")
        geom, end_line = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) == 1
        assert geom.atoms[0].x == 0.0

    def test_full_parse_with_tabs(self, parser: ORCAParser) -> None:
        content = "! B3LYP\tdef2-SVP\n* xyz\t0\t1\nH\t0\t0\t0\n*"
        result = parser.parse(content)
        assert result.simple_input is not None
        assert "B3LYP" in result.simple_input.methods
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 1


# ===========================================================================
# 4. % block end detection edge cases
# ===========================================================================

class TestPercentBlockEndDetection:
    """Robust detection of 'end' in % blocks."""

    def test_end_with_leading_whitespace(self, parser: ORCAParser) -> None:
        content = "%scf\n  maxiter 200\n  end"
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "scf"
        assert end_line == 2

    def test_end_with_trailing_whitespace(self, parser: ORCAParser) -> None:
        content = "%scf\nmaxiter 200\nend   "
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert end_line == 2

    def test_end_case_insensitive(self, parser: ORCAParser) -> None:
        content = "%scf\nmaxiter 200\nEND"
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert end_line == 2

    def test_end_mixed_case(self, parser: ORCAParser) -> None:
        content = "%scf\nmaxiter 200\nEnd"
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert end_line == 2

    def test_inline_end_after_parameters(self, parser: ORCAParser) -> None:
        """Parameters followed by 'end' on the same line."""
        content = "%pal nprocs 4 end"
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "pal"
        assert block.parameters.get("nprocs") == 4
        assert end_line == 0

    def test_word_end_embedded_in_identifier_not_treated_as_end(
        self, parser: ORCAParser
    ) -> None:
        """A parameter named 'render' should NOT be confused with 'end'."""
        content = "%output\nrender off\nend"
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "output"
        # The block should end on line 2, not prematurely on line 1.
        assert end_line == 2

    def test_end_keyword_with_surrounding_whitespace(self, parser: ORCAParser) -> None:
        content = "%method\n  D3BJ\n  end  "
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        assert block is not None
        assert block.name == "method"
        assert end_line == 2
        assert block.parameters.get("dispersion") == "D3BJ"

    def test_no_end_returns_single_line(self, parser: ORCAParser) -> None:
        """A multi-line block without 'end' should fall back to single-line."""
        content = "%scf\nmaxiter 200"
        lines = content.split("\n")
        block, end_line = parser.parse_percent_block(lines, 0)
        # Without 'end', the parser should still return something valid.
        assert block is not None
        assert block.name == "scf"


# ===========================================================================
# 5. Geometry block terminator edge cases
# ===========================================================================

class TestGeometryTerminator:
    """The geometry block ends with '*'. Test robust detection."""

    def test_star_with_trailing_whitespace(self, parser: ORCAParser) -> None:
        content = "* xyz 0 1\nH 0 0 0\n*   "
        lines = content.split("\n")
        geom, end_line = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) == 1
        assert end_line == 2

    def test_star_with_trailing_comment(self, parser: ORCAParser) -> None:
        """'* end of geometry' should still terminate the block."""
        content = "* xyz 0 1\nH 0 0 0\n* end of geometry"
        lines = content.split("\n")
        geom, end_line = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) == 1
        assert end_line == 2

    def test_star_with_leading_whitespace(self, parser: ORCAParser) -> None:
        content = "* xyz 0 1\nH 0 0 0\n  *"
        lines = content.split("\n")
        geom, end_line = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) == 1
        assert end_line == 2

    def test_inline_comment_in_atom_line(self, parser: ORCAParser) -> None:
        """Atom line with a trailing '! comment' should still parse correctly."""
        content = "* xyz 0 1\nH 0.0 0.0 0.0 ! hydrogen\nO 0.0 0.0 1.0\n*"
        lines = content.split("\n")
        geom, end_line = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) == 2
        assert geom.atoms[0].element == "H"
        assert geom.atoms[0].x == 0.0

    def test_geometry_without_terminator(self, parser: ORCAParser) -> None:
        """If the file ends without a '*', geometry should still return atoms parsed so far."""
        content = "* xyz 0 1\nH 0 0 0\nO 0 0 1.0"
        lines = content.split("\n")
        geom, end_line = parser.parse_geometry(lines, 0)
        assert geom is not None
        assert len(geom.atoms) == 2


# ===========================================================================
# 6. Full-file integration with edge cases
# ===========================================================================

class TestFullFileEdgeCases:
    """Integration tests combining multiple edge cases in one file."""

    def test_complete_file_with_comments_and_spacing(self, parser: ORCAParser) -> None:
        content = (
            "! B3LYP  def2-TZVP  Opt  ! geometry optimisation\n"
            "%maxcore  4000\n"
            "%scf\n"
            "  maxiter 200\n"
            "  end\n"
            "* xyz  0  1\n"
            "  H   0.0  0.0  0.0  ! origin\n"
            "  O   0.0  0.0  1.0\n"
            "*"
        )
        result = parser.parse(content)
        assert result.simple_input is not None
        assert "B3LYP" in result.simple_input.methods
        assert "def2-TZVP" in result.simple_input.basis_sets
        assert "OPT" in result.simple_input.job_types
        # Comment tokens must not leak.
        assert not any("geometry" in kw for kw in result.simple_input.other_keywords)
        assert not any("optimisation" in kw for kw in result.simple_input.other_keywords)

        # % blocks
        maxcore_blocks = [b for b in result.percent_blocks if b.name == "maxcore"]
        assert len(maxcore_blocks) == 1
        assert maxcore_blocks[0].parameters.get("memory") == 4000

        scf_blocks = [b for b in result.percent_blocks if b.name == "scf"]
        assert len(scf_blocks) == 1
        assert scf_blocks[0].parameters.get("maxiter") == 200

        # Geometry
        assert result.geometry is not None
        assert len(result.geometry.atoms) == 2
        assert result.geometry.atoms[0].element == "H"
        assert result.geometry.atoms[1].element == "O"

    def test_file_with_inline_comment_in_exclamation_line(self, parser: ORCAParser) -> None:
        content = (
            "! HF 6-31G* SP ! single point\n"
            "* xyz 0 1\n"
            "H 0 0 0\n"
            "*"
        )
        result = parser.parse(content)
        assert result.simple_input is not None
        assert "HF" in result.simple_input.methods
        assert "6-31G*" in result.simple_input.basis_sets
        assert "SP" in result.simple_input.job_types
        assert not any("single" in kw for kw in result.simple_input.other_keywords)
        assert not any("point" in kw for kw in result.simple_input.other_keywords)
