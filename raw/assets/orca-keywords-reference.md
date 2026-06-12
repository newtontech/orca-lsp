# ORCA Keywords Reference

> Sources:
> - ORCA 6.1.1 Manual: https://orca-manual.mpi-muelheim.mpg.de/contents/essentialelements/index_essentialelements.html
> - ORCA Input Library: https://sites.google.com/site/orcainputlibrary/home
> - ORCA 6.0 Tutorials (FACCTs): https://www.faccts.de/docs/orca/6.0/tutorials/
> - ORCA 5.0.4 Manual PDF: https://www.kofo.mpg.de/970316/orca_manual_5_0_4.pdf
> Collected: 2026-06-12

## Method Keywords

### Hartree-Fock Methods
| Keyword | Description |
|---------|-------------|
| `HF` | Hartree-Fock |
| `RHF` | Restricted Hartree-Fock |
| `UHF` | Unrestricted Hartree-Fock |
| `ROHF` | Restricted Open-shell Hartree-Fock |

### DFT Functionals (Selected)
| Keyword | Type | Description |
|---------|------|-------------|
| `B3LYP` | Hybrid GGA | Most popular hybrid functional |
| `PBE0` | Hybrid GGA | Perdew-Burke-Ernzerhof hybrid |
| `BP86` | GGA | Becke exchange + Perdew correlation |
| `BLYP` | GGA | Becke exchange + LYP correlation |
| `PBE` | GGA | Perdew-Burke-Ernzerhof |
| `TPSS` | meta-GGA | Tao-Perdew-Staroverov-Scuseria |
| `M06` | meta-GGA | Minnesota 2006 |
| `M06-2X` | meta-GGA | Minnesota high-nonlocality |
| `M06-L` | meta-GGA | Minnesota local |
| `CAM-B3LYP` | Range-separated | Long-range corrected B3LYP |
| `wB97X-D` | Range-separated | Range-separated with dispersion |
| `wB97X-D3` | Range-separated | Updated wB97X-D |
| `B2PLYP` | Double hybrid | Grimme's double hybrid |
| `DSD-PBEP86` | Double hybrid | Sanzhirov double hybrid |
| `revDSD-PBEP86` | Double hybrid | Revised DSD-PBEP86 |
| `LDA` / `SVWN` | LSDA | Local density approximation |

### Semiempirical Methods
| Keyword | Description |
|---------|-------------|
| `PM3` | Parameterized Model 3 |
| `AM1` | Austin Model 1 |
| `MNDO` | Modified Neglect of Differential Overlap |
| `ZINDO/1` | Zerner INDO variant 1 |
| `ZINDO/S` | Zerner INDO for spectroscopy |
| `GFN2-xTB` | Grimme's extended Tight-Binding |
| `GFN-FF` | Grimme's force field |

### Composite Methods (3c)
| Keyword | Description |
|---------|-------------|
| `B97-3c` | B97 with 3-correction composite |
| `PBEh-3c` | PBE hybrid 3-correction |
| `r2SCAN-3c` | r2SCAN 3-correction |
| `HF-3c` | Hartree-Fock 3-correction |

### Wavefunction Methods
| Keyword | Description |
|---------|-------------|
| `MP2` | Second-order Moller-Plesset |
| `MP3` | Third-order Moller-Plesset |
| `CCSD` | Coupled cluster singles doubles |
| `CCSD(T)` | CCSD with perturbative triples |
| `DLPNO-CCSD` | Domain-based local pair natural orbital CCSD |
| `DLPNO-CCSD(T)` | DLPNO-CCSD with perturbative triples |
| `QCISD` | Quadratic CISD |
| `CASSCF` | Complete active space SCF |

## Basis Set Keywords

### Karlsruhe def2 Series
| Keyword | Description |
|---------|-------------|
| `def2-SVP` | Split-valence polarization (double-zeta quality) |
| `def2-SV(P)` | Split-valence (reduced polarization) |
| `def2-TZVP` | Triple-zeta valence polarization |
| `def2-TZVPP` | Triple-zeta valence double polarization |
| `def2-QZVP` | Quadruple-zeta valence polarization |
| `def2-QZVPP` | Quadruple-zeta valence double polarization |

### Pople Basis Sets
| Keyword | Description |
|---------|-------------|
| `STO-3G` | Minimal basis |
| `3-21G` | Small split-valence |
| `6-31G` | Split-valence |
| `6-31G*` / `6-31G(d)` | With polarization on heavy atoms |
| `6-31G**` / `6-31G(d,p)` | With polarization on all atoms |
| `6-311G*` / `6-311G(d)` | Triple-zeta with polarization |
| `6-311G**` / `6-311G(d,p)` | Triple-zeta with full polarization |
| `6-311+G**` | With diffuse functions |

### Dunning Correlation-Consistent
| Keyword | Description |
|---------|-------------|
| `cc-pVDZ` | Double-zeta correlation-consistent |
| `cc-pVTZ` | Triple-zeta correlation-consistent |
| `cc-pVQZ` | Quadruple-zeta correlation-consistent |
| `cc-pV5Z` | Quintuple-zeta correlation-consistent |
| `aug-cc-pVDZ` | With diffuse functions |
| `aug-cc-pVTZ` | With diffuse functions |
| `aug-cc-pVQZ` | With diffuse functions |

### Jensen pcs-n / pcseg-n
| Keyword | Description |
|---------|-------------|
| `pc-1` / `pcseg-1` | Polarization-consistent double-zeta |
| `pc-2` / `pcseg-2` | Polarization-consistent triple-zeta |
| `pc-3` / `pcseg-3` | Polarization-consistent quadruple-zeta |
| `pc-4` / `pcseg-4` | Polarization-consistent quintuple-zeta |
| `aug-pc-1` through `aug-pc-4` | With diffuse functions |

### Relativistic Basis Sets
| Keyword | Description |
|---------|-------------|
| `SARC-ZORA-TZVP` | ZORA-optimized triple-zeta |
| `SARC-ZORA-QZVP` | ZORA-optimized quadruple-zeta |
| `SARC-DKH-QZVP` | DKH-optimized quadruple-zeta |
| `def2-TZVP(-f)` | def2 without f-functions (for ECP) |
| `x2c-TZVPall` | X2C-optimized all-electron |

### Auxiliary Basis Sets
| Keyword | Type | Description |
|---------|------|-------------|
| `def2/J` | AuxJ | Coulomb fitting for def2 series |
| `def2/JK` | AuxJK | Coulomb+exchange fitting for def2 |
| `def2-TZVP/C` | AuxC | Correlation fitting |
| `def2-TZVPP/C` | AuxC | Correlation fitting |
| `SARC/J` | AuxJ | Coulomb fitting for SARC series |
| `AutoAux` | Auto | Automatic generation |

## Job Type Keywords

| Keyword | Description |
|---------|-------------|
| `SP` | Single point energy |
| `OPT` | Geometry optimization |
| `FREQ` | Frequency calculation |
| `TS` | Transition state search |
| `IRC` | Intrinsic reaction coordinate |
| `SCAN` | Potential energy surface scan |
| `NEB-TS` | Nudged elastic band transition state |
| `GOAT` | Global optimization and conformer search |

## SCF Control Keywords

| Keyword | Description |
|---------|-------------|
| `TightSCF` | Tight SCF convergence (default: 10^-8 Eh) |
| `VeryTightSCF` | Very tight SCF convergence |
| `ExtremeSCF` | Extreme SCF convergence |
| `LooseSCF` | Loose SCF convergence |
| `NormalSCF` | Normal SCF convergence |
| `UKS` | Unrestricted Kohn-Sham |
| `RKS` | Restricted Kohn-Sham |
| `ROKS` | Restricted open-shell KS |

## Dispersion Correction Keywords

| Keyword | Description |
|---------|-------------|
| `D3` | Grimme D3 with zero-damping |
| `D3BJ` | Grimme D3 with Becke-Johnson damping |
| `D4` | Grimme D4 (charge-dependent) |
| `VV10` | Non-local correlation (for wB97X-D etc.) |

## RI/DF Keywords

| Keyword | Description |
|---------|-------------|
| `RIJCOSX` | RI-J + COS-X approximation (default for hybrid DFT in ORCA >= 5.0) |
| `RI-JK` | RI for both Coulomb and exchange |
| `RI-J` | RI for Coulomb only |
| `SPLIT-RI-J` | Split RI-J algorithm |
| `RI-MP2` | RI-accelerated MP2 |
| `DLPNO` | Domain-based local pair natural orbital |

## Numerical Grid Keywords

| Keyword | Description |
|---------|-------------|
| `DefGrid1` | Coarse grid (fast, less accurate) |
| `DefGrid2` | Medium grid (default) |
| `DefGrid3` | Fine grid (more accurate, slower) |
| `GridX1` / `GridX2` / `GridX3` | COSX grid sizes |
| `Grid1` through `Grid7` | DFT integration grid sizes (deprecated in ORCA 5.0+) |

## Solvation Keywords

| Keyword | Description |
|---------|-------------|
| `CPCM(Water)` | CPCM with Water dielectric |
| `CPCM(solvent)` | CPCM with named solvent |
| `COSMO(Water)` | COSMO with Water |
| `SMD(Water)` | SMD solvation model |
| `DRACO` | Dynamic radii adjustment for CPCM |

## Output Control Keywords

| Keyword | Description |
|---------|-------------|
| `SmallPrint` | Reduced output |
| `LargePrint` | Extended output |
| `PrintLevel Mini` | Minimal print level |
| `NoPOP` | Suppress population analysis |
| `KeepInts` | Keep integrals for subsequent jobs |
| `ReadInts` | Read integrals from previous job |

## Common Keyword Combinations

### Standard DFT Optimization
```
! B3LYP def2-TZVP OPT FREQ D3BJ TightSCF
```

### High-Accuracy Single Point
```
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C TightSCF SP
```

### TD-DFT Excited States
```
! B3LYP def2-TZVP TightSCF SP
%tddft
  nroots 10
end
```

### Geometry Optimization with Solvent
```
! B3LYP def2-SVP OPT CPCM(Water) D3BJ TightSCF
```

### Range-Separated Functional
```
! CAM-B3LYP def2-TZVP TightSCF DefGrid3
```

### Post-HF MP2
```
! MP2 def2-TZVP TightSCF RIJCOSX
```

## Percent Block Quick Reference

### %scf
```
%scf
  MaxIter 500
  Convergence Tight
  Guess PModel
  Damping 0.2
  LevelShift 0.5
  SOSCF
    start 0.002
  end
end
```

### %geom
```
%geom
  MaxIter 50
  Calc_Hess true
  Recalc_Hess 5
  Constraints
    { B 1 2 1.5 C }
  end
  Trust 0.2
end
```

### %tddft
```
%tddft
  NRoots 10
  MaxDim 100
  IRoot 1
  TDA false
  DoRaman true
end
```

### %cpcm
```
%cpcm
  epsilon 80.4
  refrac 1.33
end
```

### %mp2
```
%mp2
  MaxCore 4000
  RI true
  FreezeCore true
end
```

### %pal
```
%pal
  nprocs 8
end
```

### %basis
```
%basis
  NewGTO H "def2-SVP" end
  NewAuxGTO H "def2/J" end
  ECP Pt "def2-ECP" end
end
```

### %mdci (Coupled Cluster)
```
%mdci
  MaxIter 50
  TCutPNO 1e-8
  DLPNO true
end
```

### %freq
```
%freq
  Temp 298.15
  ScaleFactor 0.957
end
```

### %rel (Relativistic)
```
%rel
  method ZORA
  picturechange true
end
```
