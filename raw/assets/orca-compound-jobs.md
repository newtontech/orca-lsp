# ORCA Compound Jobs and Multi-Step Workflows

> Sources:
> - ORCA 6.1.1 Manual -- Compound: https://orca-manual.mpi-muelheim.mpg.de/contents/workflowsautomatization/compound.html
> - ORCA 6.0 Tutorials -- Compound Jobs: https://www.faccts.de/docs/orca/6.0/tutorials/workflows/compound_jobs.html
> - CompoundScripts GitHub: https://github.com/ORCAQuantumChemistry/CompoundScripts
> - ORCA 6.1 Manual -- Compound Examples: https://www.faccts.de/docs/orca/6.1/manual/contents/workflowsautomatization/compound_examples.html
> Collected: 2026-06-12

## Overview

ORCA's **Compound** feature is the recommended way to combine multiple calculation steps into a single input file. It replaces the deprecated `$new_job` syntax.

### Deprecated: $new_job

```
# WARNING: $new_job is deprecated
! B3LYP def2-SVP SP
* xyz 0 1
  O 0 0 0
  H 0 0 1
  H 0 1 0
*
$new_job
! B3LYP def2-TZVP SP
* xyz 0 1
  O 0 0 0
  H 0 0 1
  H 0 1 0
*
```

### Recommended: Compound Module

The Compound module allows:
- Chaining calculations with different methods/basis sets
- Passing results between steps (geometries, orbitals, energies)
- Python-style scripting within ORCA
- Automated plotting and analysis

## Compound Use Cases

1. **Optimization + Frequency**: Optimize geometry, then compute frequencies
2. **Multi-Level Single Points**: Cheap optimization, expensive single point
3. **Extrapolation**: Multiple basis sets for CBS extrapolation
4. **Spectroscopy Pipeline**: Optimize -> frequency -> excited states
5. **Conformer Search**: GOAT + refinement

## Common Workflow Patterns

### Pattern 1: Opt + Freq (Combined Keywords)

The simplest approach -- just combine `OPT` and `FREQ` keywords:

```
! B3LYP def2-TZVP OPT FREQ D3BJ TightSCF
%maxcore 4000
%pal nprocs 4 end

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
*
```

### Pattern 2: Cheap Opt + Expensive SP (Using $new_job -- deprecated but still used)

```
# Step 1: Cheap optimization
! B3LYP def2-SVP OPT TightSCF
%maxcore 4000
* xyz 0 1
  O   0.0  0.0  0.0
  H   0.0  0.0  1.0
  H   0.0  1.0  0.0
*

$new_job

# Step 2: High-accuracy single point on optimized geometry
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C TightSCF
%maxcore 8000
* xyzfile 0 1
```

### Pattern 3: Multi-Method Property Calculation

```
# Step 1: DFT optimization
! B3LYP def2-TZVP OPT TightSCF KeepInts
%maxcore 4000
* xyz 0 1
  B  0 0 0  0      0 0
  O  1 0 0  1.2049 0 0
*

$new_job

# Step 2: Property calculation with different functional
! BP86 def2-TZVP SmallPrint ReadInts
%eprnmr gtensor 1 end
* xyz 0 1
  B  0 0 0  0      0 0
  O  1 0 0  1.2049 0 0
*
```

## CompoundScripts Library

The official `CompoundScripts` repository (https://github.com/ORCAQuantumChemistry/CompoundScripts) provides ready-made scripts for common workflows.

### Available Scripts Include:
- Basis set extrapolation
- BSSE-corrected interaction energies
- Multi-step optimization protocols
- Automated spectral simulations
- Conformer search pipelines

## ORCA Python Interface (OPI)

For more complex automation, ORCA 6.1+ provides the Python Interface:

```python
# Pseudocode for OPI workflow
from orca import OPI

# Create input
inp = OPI.Input()
inp.method = "B3LYP"
inp.basis = "def2-TZVP"
inp.job_type = "OPT"

# Run calculation
result = OPI.run(inp)

# Extract optimized geometry
geometry = result.get_geometry()

# Create single-point job with optimized geometry
sp_inp = OPI.Input()
sp_inp.method = "DLPNO-CCSD(T)"
sp_inp.basis = "def2-TZVPP"
sp_inp.geometry = geometry

sp_result = OPI.run(sp_inp)
energy = sp_result.get_energy()
```

## Extrapolation Techniques

### Two-Point Basis Set Extrapolation

For CBS (complete basis set) extrapolation:

```
# Step 1: Triple-zeta calculation
! CCSD(T) def2-TZVPP def2-TZVPP/C TightSCF
%maxcore 8000
* xyz 0 1
  ...
*

$new_job

# Step 2: Quadruple-zeta calculation
! CCSD(T) def2-QZVPP def2-QZVPP/C TightSCF
%maxcore 16000
* xyz 0 1
  ...
*
```

Then extrapolate: E(CBS) = E(QZ) + (E(QZ) - E(TZ)) / ( (4/3)^3 - 1 )

## Input Priority in Multi-Step Jobs

When using `$new_job`:
- All calculation flags are transferred from the previous job
- Only changes need to be specified
- The new job takes orbitals from the old job by default
- To override, specify your own guess explicitly
- If you enabled RI for one job, it carries over (turn off manually if not wanted)
