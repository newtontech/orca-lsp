# ORCA-LSP Architecture

## Overview

ORCA-LSP is a Language Server Protocol implementation for ORCA quantum chemistry software input files.

## Components

### Parser (`src/orca_lsp/parser.py`)

The parser is responsible for:
- Parsing ORCA input files (.inp)
- Extracting simple input lines (!)
- Parsing % blocks with parameters
- Extracting geometry sections (XYZ and internal coordinates)
- Validating keywords and providing diagnostics

#### Data Structures

- `SimpleInput`: Parsed simple input line (!)
- `PercentBlock`: Parsed % block with parameters
- `Geometry`: Parsed geometry section with atoms
- `Atom`: Individual atom with coordinates
- `ParseResult`: Complete parse result with errors and warnings

### Server (`src/orca_lsp/server.py`)

The LSP server implements:
- **Completion**: Auto-completion for methods, basis sets, job types, and % blocks
- **Hover**: Context-aware documentation for keywords
- **Diagnostics**: Real-time error and warning detection
- **Code Actions**: Quick fixes for common errors

### Keywords (`src/orca_lsp/keywords.py`)

Comprehensive keyword database:
- DFT functionals (B3LYP, PBE0, M06-2X, etc.)
- Wavefunction methods (HF, MP2, CCSD(T), etc.)
- Basis sets (def2-SVP, cc-pVTZ, 6-31G*, etc.)
- Job types (SP, OPT, FREQ, TS, IRC, etc.)
- % blocks with examples

## LSP Features

### Completion

The server provides context-aware completion:
- After `!`: Methods, basis sets, job types
- After `%`: Block names and parameters
- In geometry section: Element symbols

### Hover

Hover documentation shows:
- Method descriptions and references
- Basis set information
- Job type explanations
- % block parameter documentation

### Diagnostics

Real-time diagnostics detect:
- Unknown keywords
- Invalid parameters
- Missing required sections
- Memory and parallelization issues

### Code Actions

Quick fixes include:
- Add missing %maxcore
- Add missing %pal nprocs
- Fix common keyword typos

## Testing

The project maintains 100% test coverage:
- Unit tests for parser
- Unit tests for server
- Integration tests for LSP features
- Edge case tests for robustness

Run tests:
```bash
pytest --cov=orca_lsp --cov-report=html
```

## Performance

- Test execution: ~3-5 seconds
- Parser performance: O(n) where n is file size
- Memory usage: Minimal (no caching)

## Future Enhancements

Potential improvements:
1. Add more % blocks support
2. Enhanced error messages with suggestions
3. Support for ORCA output files
4. Integration with ORCA documentation
5. Configuration file support
