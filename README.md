# ORCA LSP

Language Server Protocol implementation for ORCA quantum chemistry software.

## Features

- **Syntax Highlighting**: Full support for ORCA input file syntax
- **Auto-completion**: 
  - Methods (DFT functionals, wavefunction methods)
  - Basis sets (Pople, Karlsruhe, Dunning)
  - Job types (SP, OPT, FREQ, etc.)
  - %blocks (%maxcore, %pal, %method, etc.)
- **Diagnostics**: 
  - Invalid keyword detection
  - Parameter validation
  - Missing required sections
  - Memory and parallelization warnings
- **Hover Documentation**: Context-aware documentation for keywords
- **Quick Fixes**: Automatic suggestions for common errors

## Installation

```bash
pip install orca-lsp
```

## Usage

### As a Language Server

```bash
orca-lsp
```

The server communicates via stdin/stdout following the Language Server Protocol.

## Supported Input Format

```orca
! B3LYP def2-TZVP OPT FREQ
%maxcore 4000
%pal nprocs 4 end

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
*
```

## Development

```bash
git clone https://github.com/newtontech/orca-lsp.git
cd orca-lsp
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Test Coverage

The project maintains high test coverage:

```bash
pytest --cov=orca_lsp --cov-report=html
```

Open `htmlcov/index.html` to view the detailed coverage report.

Current coverage: 100%

## Architecture

### Parser (`parser.py`)
The parser provides:
- Full ORCA input file parsing
- Support for simple input lines (!)
- % block parsing with parameter extraction
- Geometry section parsing (XYZ and internal coordinates)
- Validation and diagnostics

### Server (`server.py`)
The LSP server implements:
- Text completion for all contexts
- Hover documentation for keywords
- Diagnostics publishing
- Code actions for quick fixes
- Document synchronization

### Keywords (`keywords.py`)
Comprehensive keyword database:
- DFT functionals (hybrid, GGA, meta-GGA, double-hybrid)
- Wavefunction methods (HF, MP2, CCSD, etc.)
- Basis sets (Pople, Karlsruhe def2, Dunning cc-pVXZ)
- Job types (SP, OPT, FREQ, TS, IRC, etc.)
- % blocks with examples

## License

MIT
