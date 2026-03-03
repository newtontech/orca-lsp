# ORCA-LSP User Guide

## Installation

### From PyPI (Recommended)

```bash
pip install orca-lsp
```

### From Source

```bash
git clone https://github.com/newtontech/orca-lsp.git
cd orca-lsp
pip install -e .
```

## Editor Integration

### VS Code

1. Install the [LSP client extension](https://marketplace.visualstudio.com/items?itemName=matangover.mypy)
2. Add to your `settings.json`:

```json
{
  "lsp.languageServers": {
    "orca-lsp": {
      "command": ["orca-lsp"],
      "selector": { "language": "orca", "pattern": "**/*.inp" },
      "args": []
    }
  }
}
```

### Neovim (nvim-lspconfig)

```lua
local lspconfig = require('lspconfig')

lspconfig.orca_lsp.setup {
  cmd = {"orca-lsp"},
  filetypes = {"orca"},
  root_dir = lspconfig.util.root_pattern(".git", "*.inp"),
}
```

### Emacs (lsp-mode)

```elisp
(lsp-register-client
 (make-lsp-client :new-connection (lsp-stdio-connection "orca-lsp")
                  :major-modes '(orca-mode)
                  :server-id 'orca-lsp))
```

### Vim/Neovim (coc.nvim)

Add to `coc-settings.json`:

```json
{
  "languageserver": {
    "orca": {
      "command": "orca-lsp",
      "filetypes": ["orca"],
      "rootPatterns": [".git", "*.inp"]
    }
  }
}
```

## Features

### Auto-Completion

Type `!` and get suggestions for:
- DFT functionals (B3LYP, PBE0, ωB97X-D, etc.)
- Wavefunction methods (HF, MP2, CCSD(T), etc.)
- Basis sets (def2-SVP, cc-pVTZ, 6-31G*, etc.)
- Job types (SP, OPT, FREQ, TS, IRC, etc.)

Type `%` and get suggestions for:
- Block names (maxcore, pal, method, scf, etc.)
- Block parameters

### Hover Documentation

Hover over any keyword to see:
- Brief description
- References (if available)
- Usage examples

### Diagnostics

Real-time error detection:
- Unknown keywords
- Invalid parameters
- Missing required sections
- Memory warnings

### Quick Fixes

Automatic suggestions for:
- Missing `%maxcore` block
- Missing `%pal nprocs` setting

## Example Input Files

### Basic Optimization

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

### DLPNO-CCSD(T) Single Point

```orca
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C SP
%maxcore 8000
%pal nprocs 8 end

* xyz 0 1
  C   1.390000   0.000000   0.000000
  C   0.695000   1.203781   0.000000
  C  -0.695000   1.203781   0.000000
  C  -1.390000   0.000000   0.000000
  C  -0.695000  -1.203781   0.000000
  C   0.695000  -1.203781   0.000000
  H   2.470000   0.000000   0.000000
  H   1.235000   2.139088   0.000000
  H  -1.235000   2.139088   0.000000
  H  -2.470000   0.000000   0.000000
  H  -1.235000  -2.139088   0.000000
  H   1.235000  -2.139088   0.000000
*
```

### Solvation Model

```orca
! B3LYP def2-SVP OPT CPCM(Water)
%maxcore 4000
%cpcm
  epsilon 80.4
end

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
*
```

## Troubleshooting

### Server Not Starting

Check if ORCA-LSP is in PATH:
```bash
which orca-lsp
```

### No Completion Suggestions

Make sure the file has `.inp` extension and your editor recognizes it as ORCA input.

### Diagnostics Not Showing

Check your editor's LSP client logs for errors.

## Getting Help

- GitHub Issues: https://github.com/newtontech/orca-lsp/issues
- ORCA Documentation: https://sites.cecs.anu.edu.au/orca/
