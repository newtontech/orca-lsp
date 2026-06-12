# ORCA Basis Sets Reference

> Sources:
> - ORCA 6.1.1 Manual -- Basis Sets (Section 2.7): https://orca-manual.mpi-muelheim.mpg.de/contents/essentialelements/basisset.html
> - ORCA Input Library -- Basis Sets: https://sites.google.com/site/orcainputlibrary/basis-sets
> - ORCA 6.0 Manual -- Choice of Basis Set: https://www.faccts.de/docs/orca/6.0/manual/contents/detailed/basisset.html
> - Pantazis DFT-BasisSets Lecture: https://pc2.uni-paderborn.de/fileadmin/pc2/events/2020-02-10_Winterschool/Pantazis_DFT-BasisSets.pdf
> Collected: 2026-06-12

## Orbital Basis Sets

### Karlsruhe def2 Series (Ahlrichs)
Most commonly used in ORCA. Available for H-Rn (elements 1-86).

| Keyword | Quality | Polarization | Typical Use |
|---------|---------|-------------|-------------|
| `def2-SV(P)` | Double-zeta | Reduced | Quick screening |
| `def2-SVP` | Double-zeta | Single | Standard DFT |
| `def2-TZVP` | Triple-zeta | Single | Production DFT |
| `def2-TZVPP` | Triple-zeta | Double | High-quality DFT |
| `def2-QZVP` | Quadruple-zeta | Single | Benchmark |
| `def2-QZVPP` | Quadruple-zeta | Double | Near-CBS |

### Pople Basis Sets
Classic basis sets, well-tested for organic molecules.

| Keyword | Quality | Notes |
|---------|---------|-------|
| `STO-3G` | Minimal | Educational only |
| `3-21G` | Small split-valence | Quick estimates |
| `6-31G` | Split-valence | Basic |
| `6-31G*` | Split-valence + d | Standard |
| `6-31G**` | Split-valence + d,p | With H polarization |
| `6-311G*` | Triple-zeta + d | Better quality |
| `6-311G**` | Triple-zeta + d,p | With H polarization |
| `6-311+G**` | Triple-zeta + diffuse + d,p | Anions, Rydberg |

### Dunning Correlation-Consistent Basis Sets
Designed for correlated methods (MP2, CCSD, etc.).

| Keyword | Quality | Notes |
|---------|---------|-------|
| `cc-pVDZ` | Double-zeta | Standard correlated |
| `cc-pVTZ` | Triple-zeta | Production correlated |
| `cc-pVQZ` | Quadruple-zeta | Benchmark |
| `cc-pV5Z` | Quintuple-zeta | Near-CBS |
| `aug-cc-pVDZ` | + diffuse | Anions, TD-DFT |
| `aug-cc-pVTZ` | + diffuse | Production TD-DFT |
| `aug-cc-pVQZ` | + diffuse | High-accuracy TD-DFT |
| `cc-pCVXZ` | Core-valence | Core correlation |
| `cc-pwCVXZ` | Weighted core-valence | Core correlation |

### Jensen Polarization-Consistent (pcs/pcseg)
Efficient for DFT, systematic convergence.

| Keyword | Quality |
|---------|---------|
| `pc-1` / `pcseg-1` | Double-zeta |
| `pc-2` / `pcseg-2` | Triple-zeta |
| `pc-3` / `pcseg-3` | Quadruple-zeta |
| `pc-4` / `pcseg-4` | Quintuple-zeta |
| `aug-pcseg-1` through `aug-pcseg-4` | With diffuse |

### Sapporo Basis Sets
For heavier elements.

| Keyword | Notes |
|---------|-------|
| `Sapporo-DKH3-DZP` | DKH double-zeta |
| `Sapporo-DKH3-TZP` | DKH triple-zeta |
| `Sapporo-DKH3-QZP` | DKH quadruple-zeta |

### ANO (Atomic Natural Orbital) Basis Sets
Compact and systematic.

| Keyword | Notes |
|---------|-------|
| `ANO-RCC-MB` | Minimal contraction |
| `ANO-RCC-VDZP` | Double-zeta + polarization |
| `ANO-RCC-VTZP` | Triple-zeta + polarization |
| `ANO-RCC-VQZP` | Quadruple-zeta + polarization |

## Relativistic Basis Sets

For calculations with ZORA, DKH, or X2C Hamiltonians.

| Keyword | Method | Quality |
|---------|--------|---------|
| `SARC-ZORA-SVP` | ZORA | Double-zeta |
| `SARC-ZORA-TZVP` | ZORA | Triple-zeta |
| `SARC-ZORA-QZVP` | ZORA | Quadruple-zeta |
| `SARC-DKH-SVP` | DKH | Double-zeta |
| `SARC-DKH-TZVP` | DKH | Triple-zeta |
| `SARC-DKH-QZVP` | DKH | Quadruple-zeta |
| `SARC2-ZORA-TZVP` | ZORA | Updated SARC (lanthanides) |
| `x2c-TZVPall` | X2C | All-electron triple-zeta |
| `x2c-TZVPPall` | X2C | All-electron triple-zeta double-pol |

## Auxiliary Basis Sets

### Coulomb-Fitting (AuxJ)

| Keyword | For Orbital | Notes |
|---------|------------|-------|
| `def2/J` | All def2 orbital | Universal Coulomb fitting |
| `SARC/J` | All SARC orbital | Relativistic Coulomb fitting |
| `x2c/J` | All x2c orbital | X2C Coulomb fitting |

### Coulomb+Exchange-Fitting (AuxJK)

| Keyword | For Orbital | Notes |
|---------|------------|-------|
| `def2/JK` | def2 orbital | Coulomb + exchange fitting |

### Correlation-Fitting (AuxC)

| Keyword | For Orbital | Notes |
|---------|------------|-------|
| `def2-SVP/C` | def2-SVP | MP2/CC correlation |
| `def2-TZVP/C` | def2-TZVP | MP2/CC correlation |
| `def2-TZVPP/C` | def2-TZVPP | MP2/CC correlation |
| `def2-QZVPP/C` | def2-QZVPP | MP2/CC correlation |

### F12 Complementary Auxiliary (CABS)

| Keyword | For Orbital | Notes |
|---------|------------|-------|
| `cc-pVXZ-F12-CABS` | cc-pVXZ-F12 | F12 explicitly correlated |

### AutoAux

The `AutoAux` keyword generates auxiliary basis sets automatically for any orbital basis set that doesn't have a predefined auxiliary.

## Effective Core Potentials (ECPs)

For heavy elements (transition metals, lanthanides, actinides).

| Keyword | Element Range | Notes |
|---------|--------------|-------|
| `def2-ECP` | Rb-Rn | Standard for def2 series |
| `SDS(60,MDF)` | Lanthanides | Stuttgart-Dresden small-core |
| `SDS(28,MWB)` | 3d transition metals | Small-core ECP |
| `SDS(46,MWB)` | 4d transition metals | Small-core ECP |

## Basis Set Assignment Methods

### Global (Simple Input)

```
! B3LYP def2-TZVP
```

### Per-Element (via %basis block)

```
%basis
  NewGTO H "def2-SVP" end
  NewGTO C "def2-TZVP" end
end
```

### Per-Atom

```
%basis
  NewGTO 1 "def2-TZVP" end
  NewGTO 2 "def2-SVP" end
end
```

### From File

```
%basis
  GTOName "mybasis.bas"
end
```

## Recommended Basis Set Choices

| Calculation Type | Basis Set | Reason |
|-----------------|-----------|--------|
| Quick screening | def2-SVP | Fast, reasonable |
| Standard DFT | def2-TZVP | Good balance of cost/accuracy |
| Production DFT | def2-TZVP + D3BJ | With dispersion |
| High-quality DFT | def2-TZVPP or def2-QZVP | Larger basis |
| MP2 | def2-TZVP/C | With correlation auxiliary |
| DLPNO-CCSD(T) | def2-TZVPP/C | With correlation auxiliary |
| Benchmark | def2-QZVPP/C | Near CBS |
| TD-DFT | def2-TZVP or aug-cc-pVTZ | Diffuse functions important |
| Anions | aug-cc-pVTZ or def2-TZVPPD | Diffuse functions required |
| Heavy elements (relativistic) | SARC-ZORA-TZVP or x2c-TZVPall | With ZORA/DKH/X2C |
| Composite methods | Built-in (B97-3c, PBEh-3c) | Pre-optimized basis |

## Basis Set and Method Requirements

Not all methods need all basis set types:

| Method | Orbital | AuxJ | AuxJK | AuxC |
|--------|---------|------|-------|------|
| HF | Yes | Optional (RI-J) | Optional (RI-JK) | No |
| DFT (pure) | Yes | Recommended (RI-J) | No | No |
| DFT (hybrid) | Yes | Yes (RIJCOSX) | Optional | No |
| MP2 | Yes | Yes | No | Recommended |
| CCSD(T) | Yes | Yes | No | Recommended |
| DLPNO-CCSD(T) | Yes | Yes | No | Required |
| CASSCF | Yes | Optional | Optional | No |
