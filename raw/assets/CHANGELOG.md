# Change Log
# Change Log

## [0.5.4] - 2026-03-05

### Changed
- Added comprehensive type annotations for mypy compliance
- Added TYPE_CHECKING import for TextDocument type hints
- Fixed all mypy errors (13 errors resolved)
- Code quality: 100% mypy compliance

### Technical
- Added return type annotations (-> None) to __init__ and methods
- Fixed _get_word_at_position to use proper TextDocument type
- All 338 tests pass with 100% coverage

## [0.5.3] - 2026-03-05

## [0.5.3] - 2026-03-05

### Added
- New example files demonstrating advanced ORCA features:
  - `transition_state.inp` - TS optimization with %geom settings
  - `td_dft.inp` - TD-DFT excited state calculation  
  - `counterpoise.inp` - Counterpoise correction (BSSE)

### Changed
- Updated documentation with new examples
- Tests: 338 tests with 100% coverage

## [0.5.2] - 2026-03-04

### Added
- New DFT functionals: ωB97X-D3, ωB97X-D4, LC-ωPBEh, M08-HX, M08-SO, M11, M11-L, DSD-PBEP86, DOD-PBEP86
- New percent blocks: symmetry, rels, cis, tddft, mrcc

### Changed
- Updated server version to 0.5.2
- Total: 45 DFT functionals, 21 percent blocks
- Tests: 338 tests with 100% coverage

## [0.5.1] - 2026-03-04

### Fixed
- Fixed BASIS_SETS dictionary structure (nested pc basis sets were incorrectly nested under ma-def2-TZVP)

### Changed
- Properly flattened BASIS_SETS to include all 38 basis sets as top-level entries
- Basis set count increased from 30 to 38 (added pc-1, pc-2, pc-3, aug-pc-1, aug-pc-2, EPR-II, EPR-III)

## [0.5.0] - 2026-03-04

### Added
- New % blocks for advanced ORCA functionality:
  - %eprnmr - EPR and NMR property calculations
  - %moinp - MO input from previous calculation
  - %rirpa - RI-RPA and GW calculations
  - %output - Output file settings
- Expanded DFT functional database:
  - B3PW91, X3LYP, O3LYP, mPWLYP, BMK
- New basis sets:
  - pc-1, pc-2, pc-3 - Jensen polarization-consistent
  - aug-pc-1, aug-pc-2 - Augmented pc basis sets
  - EPR-II, EPR-III - EPR-optimized basis sets

### Changed
- Expanded keywords database (34 DFT functionals, 32 basis sets, 19 % blocks)
- Enhanced parser for new % block parameters
- Test count: 329 tests (100% coverage)

## [0.4.0] - 2026-03-04

### Added
- Enhanced DFT functional database with additional functionals:
  - CAM-B3LYP - Coulomb-attenuated B3LYP for charge transfer
  - LC-ωPBE - Long-range corrected PBE functional
  - ωB97M-D - ωB97M-D range-separated hybrid with dispersion
  - MN15, MN15-L - Minnesota 2015 functionals
  - SCAN, SCAN0, r2SCAN - SCAN family functionals
  - DSD-PBEB95, PWPB95 - Additional double hybrids
- Added RKS, UKS, ROKS method types for DFT
- Added ma-def2 basis sets for minimal augmented DFT
- Added %cpcm block for solvation calculations
- New example files:
  - solvation.inp - CPCM solvation calculation
  - camb3lyp.inp - CAM-B3LYP calculation

### Changed
- Expanded keywords database (25 DFT functionals, 20 wavefunction methods, 27 basis sets)
- Enhanced completion support for new keywords

## [0.3.0] - 2026-03-03

### Added
- Achieved 100% test coverage (320 tests)
- Enhanced else branch coverage for parser loops
- Improved test coverage for regex matching edge cases
- Added tests for %pal and %scf block edge cases

### Changed
- Removed dead code for job type case-insensitive matching
- Cleaned up unreachable code branches
- Added pragma comments for logically unreachable branches

### Fixed
- Fixed branch coverage for case-insensitive keyword loops
- Enhanced test coverage for if statement else branches
- Improved parser robustness for edge cases

### Tests
- Increased test count from 299 to 320 tests
- Achieved 100% code coverage (up from 97%)
- Added tests for loop completion paths
- Added tests for regex non-matching scenarios
- Enhanced else branch coverage

### Documentation
- Updated CHANGELOG with coverage improvements
- Documented pragma comments for coverage

## [0.2.1] - 2026-03-03

### Added
- Improved test coverage from 96% to 97%
- Added comprehensive edge case tests for parser and server
- Added pragma comments for non-testable decorator functions

### Fixed
- Enhanced branch coverage for case-insensitive keyword matching
- Improved test coverage for unknown keyword handling
- Better coverage for geometry parsing edge cases

### Tests
- Added 299 tests total (up from 213)
- Achieved 97% code coverage
- Added tests for unknown keyword paths
- Added tests for case-insensitive matching
- Added tests for geometry parsing loops

### Documentation
- Updated coverage number to 97% in README

## [0.2.0] - 2026-03-02

### Added
- Enhanced parser with case-insensitive keyword matching
- Improved error handling for invalid input
- Additional % block support (method, scf, geom, freq, etc.)
- Internal coordinate geometry format support
- Enhanced diagnostics with specific error messages
- Quick fixes for common errors (e.g., missing %maxcore)

### Fixed
- Fixed parser edge cases with single-line blocks
- Improved geometry parsing with invalid atom symbols
- Fixed word boundary detection in hover feature
- Enhanced block parameter extraction

### Tests
- Added comprehensive test suite (213 tests)
- Achieved 96% code coverage
- Added integration tests for parser and server
- Added edge case tests for robustness

### Documentation
- Updated README with architecture details
- Added test coverage instructions
- Enhanced feature descriptions

## [0.1.0] - 2026-03-01

* Initial release with basic LSP support
* Parser implementation for input files
* Diagnostics and completion providers
