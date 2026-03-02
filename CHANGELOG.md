# Change Log

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
