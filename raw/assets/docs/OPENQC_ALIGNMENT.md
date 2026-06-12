# OpenQC Alignment

`orca-lsp` is the standalone ORCA language server. `newtontech/OpenQC-VSCode` should expose the same language behavior in VS Code.

## Keep aligned

- File extensions and language IDs for ORCA input files.
- Diagnostics for invalid keywords, `%` blocks, memory settings, and parallelization settings.
- Completion vocabulary for methods, basis sets, job types, and common `%` blocks.
- Minimal parser fixtures used for smoke tests.

## Release check

Before a public OpenQC release, smoke test one valid and one invalid ORCA input against this server and the extension.
