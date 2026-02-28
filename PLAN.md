# ORCA LSP Development Plan

## Project Overview
Language Server Protocol implementation for ORCA quantum chemistry software.

## Input File Format

### File Extensions
- `.inp` - ORCA input file

### Structure
```
! B3LYP def2-TZVP OPT FREQ
%maxcore 4000
%pal nprocs 4 end

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
*
```

## Implementation Status

### Phase 1: Simple Input Parser
- [x] Route line parser (!)
- [x] Method detection (DFT, HF, MP2, CCSD, etc.)
- [x] Basis set detection (def2-SVP, def2-TZVP, etc.)
- [x] Job type detection (SP, OPT, FREQ, etc.)

### Phase 2: % Block Parser
- [x] %maxcore parser
- [x] %pal parser
- [x] %method parser
- [x] %basis parser
- [x] %scf parser
- [x] %geom parser
- [x] %freq parser

### Phase 3: Geometry Parser
- [x] XYZ coordinate parsing
- [x] Charge and multiplicity detection
- [x] Atom validation

### Phase 4: LSP Features
- [x] Diagnostics (invalid keywords, parameter checking)
- [x] Completion (methods, basis sets, %blocks)
- [x] Hover (display documentation)
- [x] Quick Fix suggestions

### Phase 5: Testing
- [x] Unit tests for parser
- [x] Unit tests for LSP features
- [x] Example input files

## Technical Details

### Supported Methods
- HF (Hartree-Fock)
- DFT: B3LYP, PBE, PBE0, TPSS, M06, M06L, BLYP, BP86, etc.
- MP2, RI-MP2, MP3
- CCSD, CCSD(T), DLPNO-CCSD(T)
- CASSCF, NEVPT2

### Supported Basis Sets
- Pople: STO-3G, 3-21G, 6-31G, 6-31G*, 6-311G, 6-311G*
- Karlsruhe: def2-SVP, def2-TZVP, def2-QZVP, def2-SVPD, def2-TZVPD
- Dunning: cc-pVDZ, cc-pVTZ, cc-pVQZ, aug-cc-pVDZ, aug-cc-pVTZ
- Auxiliary: def2/J, def2-TZVP/C, def2-QZVP/C

### Supported Job Types
- SP (Single Point)
- OPT (Geometry Optimization)
- FREQ (Frequency Calculation)
- NUMFREQ (Numerical Frequency)
- OPT FREQ (Optimization + Frequency)
- IRC (Intrinsic Reaction Coordinate)
- SCAN (Coordinate Scan)
- MD (Molecular Dynamics)

### % Blocks
- `%maxcore` - Memory per core (MB)
- `%pal nprocs` - Parallelization
- `%method` - Method details (D3 dispersion, etc.)
- `%basis` - Basis set details
- `%scf` - SCF convergence settings
- `%geom` - Geometry optimization settings
- `%freq` - Frequency calculation settings

### Diagnostics Features
- Invalid keyword detection
- Missing charge/multiplicity
- Basis set compatibility warnings
- Memory setting validation
- Parallelization recommendations

## Resources
- ORCA Manual (https://www.faccts.de/docs/orca/)
- ORCA Input Library
- ORCA Forum

---

*Plan Created: 2026-03-01*
*Status: Complete*
