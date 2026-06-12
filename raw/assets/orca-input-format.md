# ORCA Input File Format Reference

> Source: ORCA 6.1.1 Manual -- Section 2.1 General Structure of the Input File
> URL: https://orca-manual.mpi-muelheim.mpg.de/contents/essentialelements/input.html
> Collected: 2026-06-12

## General Structure

The ORCA input file is a **free-format ASCII file** that can contain:

1. **Simple keyword lines** starting with `!`
2. **Input blocks** enclosed between `%` and `end`
3. **Coordinate specification** with total charge and spin multiplicity, either via `%coords` block or enclosed between two `*` symbols

### Minimal Example

```
! HF def2-TZVP

%scf
   convergence tight
end

* xyz 0 1
C  0.0  0.0  0.0
O  0.0  0.0  1.13
*
```

### Comments

Comments start with `#` and continue to end of line:

```
# This is a comment. Continues until the end of the line
```

Comments can also be closed by a second `#`:

```
TolE=1e-5;    #Energy conv.#  TolMaxP=1e-6; #Density conv.#
```

### Case Sensitivity

- The ORCA input is **NOT case sensitive**. UPPER CASE, lower case, or aNy cOMmBINAtiON are allowed.
- Exception: file names (e.g., for `%MOInp` or `*XYZName`) are case-sensitive on Unix-like OSs.
- The order of simple keywords and input blocks is generally not important.

## Input Blocks

Input blocks start with `%`, followed by the block name, and end with `end`:

```
%scf
   MaxIter 500
   Convergence tight
end
```

### Variable Assignment Syntax

```
VariableName Value
# or with optional "="
OtherVariableName = OtherValue
```

Values can be numeric, quote-delimited strings, or predefined aliases.

### Array Syntax

```
Array[1]  Value1
Array[1]  Value1,Value2,Value3
Array  Value1,Value2
```

Note: Arrays always start with index 0 (ORCA is C++). `Array[1]` is the *second* element.

### String Values

Strings (filenames) must be enclosed in quotes:

```
%scf
  MOInp "Myfile.gbw"
end
```

### Nested Sub-Blocks

Some keywords open nested sub-blocks closed with additional `end`:

```
%scf
  Guess PModel        # variable assignment
  SOSCF               # nested sub-block
    start 0.002       # variable assignment
  end                 # closes SOSCF sub-block
end
%basis
  NewGTO              # nested sub-block
    H "def2-SVP"
    S 1
    1 0.05 1.0
  end                 # closes NewGTO
end
```

### Single-Variable Blocks (No `end`)

```
%MOInp "MyFile.gbw"
%maxcore 3000
```

## Input Priority and Processing Order

1. All simple input lines (`!`) are collected into a single string.
2. Known keywords are processed in a predefined order, regardless of input file order.
3. For basis sets: if two different orbital basis sets are given (e.g., `! def2-SVP def2-TZVP`), the latter takes priority. Same for auxiliary basis sets of the same type.
4. Some simple keywords set multiple internal variables -- more specific keywords take precedence.
5. Block input is parsed in order. If a keyword is duplicated, the latter value is used.
6. Multiple instances of the same block are not recommended.

## Global Memory

```
%maxcore 2000   # 2000 MB per processing core
```

- Applies per processing core, not total.
- Do not exceed 75-80% of physical memory.
- Default: 4GB (plenty for standard DFT).
- For coupled clusters: at least 8GB recommended.

## BaseName

ORCA generates output files starting with the same prefix (BaseName). Usually inferred from input filename.

```
%base "job1"   # all generated files start with "job1"
```

## Multi-Step Jobs ($new_job -- Deprecated)

The `$new_job` feature is deprecated. Use the **Compound** feature instead.

Example of deprecated syntax:

```
! LSD DEF2-SVP TightSCF KeepInts
%eprnmr gtensor 1 end
* int 0 2
   B  0  0  0   0      0  0
   O  1  0  0   1.2049 0  0
*
$new_job
! BP86 DEF2-SVP SmallPrint ReadInts NoKeepInts
%eprnmr gtensor 1 end
* int 0 2
   B  0  0  0   0      0  0
   O  1  0  0   1.2049 0  0
*
```

## Coordinate Input

### Cartesian (xyz)

```
* xyz 0 1
O   0.0000   0.0000   0.0626
H  -0.7920   0.0000  -0.4973
H   0.7920   0.0000  -0.4973
*
```

### Internal Coordinates (int)

```
* int 0 2
O  0 0 0 0.0    0.0 0.0
H  1 0 0 0.9903 0.0 0.0
*
```

### From External File

```
* xyzfile 0 2 hydroxide.xyz
```

### Atom Specification

Atoms can be specified by symbol (H, C, Cu, Te) or atomic number (1, 6, 29, 52). Coordinates are in Angstroms.

## List of Input Blocks (Table 2.1 from Manual)

Major input blocks include:
- `%scf` -- SCF convergence and method settings
- `%method` -- Method/functional specification
- `%basis` -- Basis set customization
- `%geom` -- Geometry optimization controls
- `%freq` -- Frequency calculation settings
- `%tddft` / `%cis` -- Excited state calculations
- `%mp2` -- MP2 correlation settings
- `%mdci` -- Coupled cluster / CI settings
- `%cpcm` -- Conductor-like PCM solvation
- `%cosmo` -- COSMO solvation
- `%eprnmr` -- EPR/NMR property settings
- `%casscf` -- CASSCF multireference
- `%pal` -- Parallel execution
- `%output` -- Output format control
- `%plots` -- Orbital/density plotting
- `%moinp` -- MO input specification
- `%rel` -- Relativistic settings
- `%chkcoords` -- Coordinate checking
- `%maxcore` -- Memory per core (no `end`)
- `%base` -- BaseName (no `end`)

## Simple Keyword Lines

Simple input lines start with `!` and can contain any number of space-separated keywords:

```
! Keyword1 Keyword2
! Keyword3
```

Multiple `!` lines are allowed. Common keyword categories:

| Category | Examples |
|----------|----------|
| Methods | HF, B3LYP, PBE0, MP2, CCSD(T), DLPNO-CCSD(T) |
| Basis Sets | def2-SVP, def2-TZVP, cc-pVTZ, 6-31G* |
| Job Types | SP, OPT, FREQ, TS, IRC, SCAN |
| SCF Control | TightSCF, VeryTightSCF, LooseSCF |
| Dispersion | D3, D3BJ, D4 |
| RI/DF | RIJCOSX, RI-JK, RI-J |
| Grid | DefGrid1, DefGrid2, DefGrid3 |
| Solvation | CPCM(Water), SMD(Water) |
| Output | PrintLevel Mini, SmallPrint, LargePrint |
| Spin | UKS, RKS, ROKS |
