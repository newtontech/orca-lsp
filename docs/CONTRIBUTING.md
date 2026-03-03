# Contributing to ORCA-LSP

Thank you for your interest in contributing to ORCA-LSP!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/newtontech/orca-lsp.git
cd orca-lsp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Install pre-commit hooks:
```bash
pre-commit install
```

## Code Style

We use the following tools:
- **Black**: Code formatting
- **isort**: Import sorting
- **Ruff**: Linting
- **MyPy**: Type checking

Run all checks:
```bash
black .
isort .
ruff check .
mypy src/
```

## Testing

We maintain **100% test coverage**. All new code must include tests.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=orca_lsp --cov-report=html

# Run specific test file
pytest tests/test_parser.py

# Run with verbose output
pytest -v
```

### Writing Tests

1. Place tests in the `tests/` directory
2. Name test files as `test_*.py`
3. Name test functions as `test_*`
4. Aim for 100% coverage of new code

Example:
```python
def test_parse_simple_input(parser):
    """Test parsing simple input line."""
    content = "! B3LYP def2-SVP OPT"
    result = parser.parse(content)
    
    assert result.simple_input is not None
    assert "B3LYP" in result.simple_input.methods
    assert "def2-SVP" in result.simple_input.basis_sets
    assert "OPT" in result.simple_input.job_types
```

## Project Structure

```
orca-lsp/
├── src/orca_lsp/
│   ├── __init__.py
│   ├── parser.py          # ORCA input parser
│   ├── server.py          # LSP server implementation
│   └── keywords.py        # Keyword database
├── tests/
│   ├── test_parser.py     # Parser tests
│   ├── test_server.py     # Server tests
│   └── test_keywords.py   # Keyword tests
├── docs/
│   ├── ARCHITECTURE.md    # Architecture documentation
│   └── USER_GUIDE.md      # User guide
├── examples/
│   ├── water.inp          # Example input files
│   └── benzene.inp
├── pyproject.toml         # Project configuration
└── README.md
```

## Adding New Features

### Adding a New Keyword

1. Add to `keywords.py`:
```python
NEW_KEYWORDS = {
    "NEW_KEYWORD": {
        "description": "Description of the keyword",
        "type": "method",  # or "basis", "job_type", etc.
    }
}
```

2. Add tests in `test_keywords.py`

3. Update documentation

### Adding a New % Block

1. Add parsing logic in `parser.py`
2. Add completion items in `server.py`
3. Add hover documentation in `server.py`
4. Add tests
5. Update documentation

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and ensure 100% coverage
5. Run linting and formatting
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### PR Checklist

- [ ] Tests pass with 100% coverage
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Changelog updated (if applicable)
- [ ] Commit messages are clear

## Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create git tag
4. Build and publish to PyPI
5. Create GitHub release

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive criticism
- Accept responsibility for mistakes

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
