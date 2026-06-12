# ORCA Output File Format Reference

> Sources:
> - ORCA 6.0 Tutorials (Input and Output): https://www.faccts.de/docs/orca/6.0/tutorials/first_steps/input_output.html
> - ORCA 6.1.1 Manual -- Property File: https://orca-manual.mpi-muelheim.mpg.de/contents/utilitiesvisualization/property_file.html
> - ORCA 6.0 Manual -- Property File: https://www.faccts.de/docs/orca/6.0/manual/contents/detailed/property_file.html
> - orca_parser (GitHub): https://github.com/avanteijlingen/orca_parser
> Collected: 2026-06-12

## Output File Structure

ORCA generates several output files. The main output file uses the same BaseName as the input with no extension (or `.out`).

### Primary Output Files

| File | Description |
|------|-------------|
| `basename` (no ext) | Main output with full calculation details |
| `basename.gbw` | Gaussian basis set wavefunction file |
| `basename.property.txt` | Structured property data |
| `basename.hess` | Hessian data |
| `basename.opt` | Optimization trajectory |
| `basename.xyz` | Final geometry in XYZ format |
| `basename.engrad` | Energy + gradient data |
| `basename.inp` | Copy of input file |
| `basename.cis` | CIS/TD-DFT data |
| `basename.mp2` | MP2 natural orbitals |
| `basename.mdcipnoint` | DLPNO integrals |
| `basename.densities` | Density matrices |
| `basename.scfp` | SCF density matrix (alpha) |
| `basename.scfr` | SCF density matrix (beta) |

## Main Output File Sections

### 1. Header

```
                            *****************
                            |               |
                            |      O  R     |
                            |    C  A  !    |
                            |               |
                            *****************

         Program Version 6.1.1 - Release  -  PATH

         based on the original ORCA code by Frank Neese
```

Includes version, references, and contributors.

### 2. Input Echo

The input file is echoed back for reference.

### 3. Warnings

```
WARNINGS:
   [your warnings here]
```

Should be carefully checked before proceeding.

### 4. Calculation Type Banner

```
****************************
* Single Point Calculation *
****************************
```

Or:

```
******************************
* Geometry Optimization Run  *
******************************
```

### 5. Integral Module (SHARK)

```
----------------------
SHARK INTEGRAL PACKAGE
----------------------

Number of atoms                             ...      2
Number of basis functions                   ...     19
Number of shells                            ...      9
Maximum angular momentum                    ...      2
Integral batch strategy                     ... SHARK/LIBINT Hybrid
RI-J (if used) integral strategy            ... SPLIT-RIJ
Printlevel                                  ...      1
Contraction scheme used                     ... SEGMENTED contraction
```

### 6. SCF Settings

```
------------
SCF SETTINGS
------------
Hamiltonian:
 Ab initio Hamiltonian  Method          .... Hartree-Fock(GTOs)

General Settings:
 Integral files         IntName         .... orca
 Hartree-Fock type      HFTyp           .... UHF
 Total Charge           Charge          ....    0
 Multiplicity           Mult            ....    2
 Number of atoms        NAtoms          ....    2
 Number of basis functions NBas         ....   19
```

### 7. SCF Convergence

Each SCF iteration shows:

```
ITER  Energy     Delta-E   Max-DP   RMS-DP   [F,P]   Damp
                (Eh)      (Eh)     (Dp)     (Dp)
  1   -75.3182  0.0000000 0.15362  0.05697  0.625   0.7000
  2   -75.3237 -0.0055463 0.08961  0.03241  0.354   0.0000
  ...
 11   -75.3242 -0.0000000 0.00000  0.00000  0.000   0.0000
```

On convergence:

```
               *****************************************************
               *                     SUCCESS                       *
               *           SCF CONVERGED AFTER  11 CYCLES          *
               *****************************************************
```

### 8. Total Energy

```
----------------
TOTAL SCF ENERGY
----------------

Total Energy       :        -75.32415421767207 Eh           -2049.67444 eV

Components:
Nuclear Repulsion  :          4.27488404160356 Eh             116.32551 eV
Electronic Energy  :        -79.59903825927563 Eh           -2165.99995 eV
One Electron Energy:       -112.46709636116736 Eh           -3060.38528 eV
Two Electron Energy:         32.86805810189173 Eh             894.38533 eV
```

### 9. Orbital Energies

```
ORBITAL ENERGIES

   NO   OCC          E(Eh)            E(eV)
    0   1.0000     -20.254374       -551.3268
    1   1.0000      -1.254987        -34.1581
    2   1.0000      -0.612752        -16.6771
    3   1.0000      -0.453448        -12.3423
    4   1.0000      -0.391560        -10.6572
    5   0.0000       0.148932          4.0546
```

### 10. Final Single Point Energy

```
-------------------------   --------------------
FINAL SINGLE POINT ENERGY       -75.324154217672
-------------------------   --------------------
```

This is the key line to parse for the computed energy.

### 11. Dipole Moment

```
DIPOLE MOMENT
                                 X             Y             Z
Total Dipole Moment:      0.00000      -0.00000       1.49445
Magnitude (a.u.):            1.49445
Magnitude (Debye):           3.79579
```

### 12. Population Analysis

```
MULLIKEN ATOMIC CHARGES
   0 O:    -0.402345
   1 H:     0.201173
   2 H:     0.201173
Sum of atomic charges:    0.0000
```

### 13. Timings

```
Timings:
Reading and initializing          ...     0.004 sec
Integral generation               ...     0.007 sec
SCF iterations                    ...     0.038 sec
  Coulomb evaluation              ...     0.020 sec
  HF-exchange                     ...     0.000 sec
  XC-evaluation                   ...     0.000 sec
  DIIS step                       ...     0.003 sec
  Orbital orthonormalization      ...     0.001 sec
TOTAL                             ...     0.049 sec
```

## Geometry Optimization Output

### Optimization Header

```
******************************
* GEOMETRY OPTIMIZATION CYCLE *
******************************
```

### Per-Cycle Energy

```
                          ~!!!!!!!!!!!!!!!
                          ~ FINAL ENERGY ~
                          ~!!!!!!!!!!!!!!!
                      Ecorr =     -75.324154210 Eh
                      DE   =         -0.000000000 Eh
```

### Convergence Criteria

```
Geometry convergence  criteria:
Energy change              0.0000050   [Eh]     ****  YES
Max. gradient              0.0004500   [Eh/bohr] NO
RMS gradient               0.0003000   [Eh/bohr] YES
Max. displacement          0.0018000   [bohr]    NO
RMS displacement           0.0012000   [bohr]    YES
```

### Convergence Summary

```
                       *****************************************************
                       *                     SUCCESS                       *
                       *         GEOMETRY OPTIMIZATION CONVERGED           *
                       *****************************************************
```

## Frequency Calculation Output

### Vibrational Frequencies

```
VIBRATIONAL FREQUENCIES

   0:       0.00 cm**-1
   1:       0.00 cm**-1
   2:       0.00 cm**-1
   3:       0.00 cm**-1
   4:       0.00 cm**-1
   5:       0.00 cm**-1
   6:    1594.78 cm**-1
   7:    3657.04 cm**-1
   8:    3755.62 cm**-1
```

### Thermochemistry

```
--------------------
THERMOCHEMISTRY
--------------------

Temperature         ... 298.15 K
Pressure            ... 1.00 atm
Total Mass          ... 18.015 AMU

Electronic energy   ...    -76.01915435 Eh
Zero-point energy   ...      0.02134532 Eh     13.41 kcal/mol
Thermal energy      ...      0.02417856 Eh     15.19 kcal/mol
```

## TD-DFT Output

### Excited States

```
-----------------------------
TD-DFT/TDA EXCITATION SPECTRA
-----------------------------

STATE  1:  E=   0.148932 au      4.055 eV    32714.2 cm**-1
     49 ->  50  :     0.9898 (c=  0.994860)
     49 ->  52  :    -0.0951 (c= -0.097522)

STATE  2:  E=   0.234567 au      6.386 eV    51534.1 cm**-1
     48 ->  50  :     0.9712 (c=  0.985503)
```

## Property File Format

ORCA generates a `basename.property.txt` file with structured key-value data suitable for programmatic parsing:

```
# Number of atoms
$number_of_atoms
6

# Total Charge
$total_charge
0

# Spin multiplicity
$spin_multiplicity
1

# Total Energy (Eh)
$total_energy
-232.178932

# Final Single Point Energy (Eh)
$final_single_point_energy
-232.178932
```

## Key Parsing Patterns

### Final Energy
Search for: `FINAL SINGLE POINT ENERGY`

### SCF Convergence
Search for: `SCF CONVERGED AFTER`

### Optimization Convergence
Search for: `GEOMETRY OPTIMIZATION CONVERGED`

### Frequencies
Search for: `VIBRATIONAL FREQUENCIES`

### Excited States
Search for: `TD-DFT/TDA EXCITATION` or `TD-DFT EXCITATION`

### Dipole Moment
Search for: `DIPOLE MOMENT` or `Total Dipole Moment`

### Charges
Search for: `MULLIKEN ATOMIC CHARGES` or `LOEWDIN ATOMIC CHARGES`
