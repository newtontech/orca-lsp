# ORCA Example Input Files Collection

> Sources:
> - ORCA Input Library: https://sites.google.com/site/orcainputlibrary/home
> - ORCA 6.0 Tutorials (FACCTs): https://www.faccts.de/docs/orca/6.0/tutorials/
> - ORCA Manual Examples: https://orca-manual.mpi-muelheim.mpg.de/
> - Project examples: /Users/yhm/Desktop/code/orca-lsp/examples/
> Collected: 2026-06-12

## 1. Basic Single Point Energy (HF/def2-SVP)

```
! HF def2-SVP

* xyz 0 1
O   0.0000   0.0000   0.0626
H  -0.7920   0.0000  -0.4973
H   0.7920   0.0000  -0.4973
*
```

## 2. DFT Geometry Optimization + Frequency (B3LYP/def2-TZVP)

```
! B3LYP def2-TZVP OPT FREQ D3BJ
%maxcore 4000
%pal nprocs 4 end

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
*
```

## 3. High-Accuracy Single Point (DLPNO-CCSD(T)/def2-TZVPP)

```
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C SP TightSCF
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

## 4. TD-DFT Excited States

```
! B3LYP def2-TZVP SP TightSCF
%maxcore 4000
%pal nprocs 4 end
%tddft
  nroots 10
  maxdim 100
end

* xyz 0 1
  C   0.000000   0.000000   0.000000
  O   1.200000   0.000000   0.000000
  H  -0.500000   0.900000   0.000000
  H  -0.500000  -0.900000   0.000000
*
```

## 5. TD-DFT with Range-Separated Functional

```
! CAM-B3LYP def2-TZVP TightSCF DefGrid3 SP
%maxcore 6000
%pal nprocs 8 end
%tddft
  nroots 20
  maxdim 200
end

* xyz 0 1
  C   0.000000   0.000000   0.000000
  N   1.200000   0.000000   0.000000
  H  -0.500000   0.900000   0.000000
  H  -0.500000  -0.900000   0.000000
*
```

## 6. Solvation (CPCM)

```
! B3LYP def2-SVP OPT CPCM(Water) D3BJ
%maxcore 4000
%pal nprocs 4 end
%cpcm
  epsilon 80.4
  refrac 1.33
end

* xyz 0 1
  C   0.000000   0.000000   0.000000
  O   1.200000   0.000000   0.000000
  H  -0.500000   0.900000   0.000000
  H  -0.500000  -0.900000   0.000000
*
```

## 7. Transition State Search

```
! B3LYP def2-TZVP TS TightSCF
%maxcore 4000
%pal nprocs 8 end
%geom
  Calc_Hess true
  Recalc_Hess 5
end

* xyz 0 1
  C   0.000000   0.000000   0.000000
  O   1.200000   0.000000   0.000000
  H  -0.500000   0.900000   0.000000
  H  -0.500000  -0.900000   0.000000
*
```

## 8. MP2 Frequency Calculation

```
! MP2 def2-TZVP FREQ TightSCF
%maxcore 4000
%pal nprocs 4 end
%freq temp 298.15 end

* xyz 0 1
  C   0.000000   0.000000   0.667000
  C   0.000000   0.000000  -0.667000
  H   0.000000   0.920000   1.230000
  H   0.000000  -0.920000   1.230000
  H   0.000000   0.920000  -1.230000
  H   0.000000  -0.920000  -1.230000
*
```

## 9. Counterpoise Correction (BSSE)

```
! MP2 def2-TZVP SP TightSCF
%maxcore 4000
%pal nprocs 4 end
%cp
  fragments 2
  charge(1) 0 1
  charge(2) 0 1
end

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
  O   0.000000   0.000000   3.000000
  H   0.757160   0.586260   3.000000
  H  -0.757160   0.586260   3.000000
*
```

## 10. Open-Shell Radical (OH Radical)

```
! UHF def2-SVP
* int 0 2
O  0 0 0 0.0    0.0 0.0
H  1 0 0 0.9903 0.0 0.0
*
```

## 11. Reading Coordinates from External File

```
! B3LYP def2-TZVP OPT TightSCF
%maxcore 4000
* xyzfile 0 1 molecule.xyz
```

## 12. SCF Convergence Control

```
! B3LYP def2-TZVP SP
%scf
  MaxIter 500
  Convergence Tight
  Guess PModel
  Damping 0.2
end
%maxcore 4000

* xyz 0 1
  Fe  0.0  0.0  0.0
  C   0.0  0.0  1.8
  O   0.0  0.0  3.0
*
```

## 13. Relativistic Calculation (ZORA)

```
! ZORA B3LYP SARC-ZORA-TZVP def2/J TightSCF SP
%rel
  method ZORA
  picturechange true
end

* xyz 0 1
  Pt  0.0  0.0  0.0
  Cl  2.3  0.0  0.0
  Cl -2.3  0.0  0.0
*
```

## 14. Custom Basis Set Assignment

```
! B3LYP TightSCF SP
%basis
  NewGTO H "def2-SVP" end
  NewGTO C "def2-TZVP" end
  NewAuxGTO H "def2/J" end
  NewAuxGTO C "def2/J" end
end

* xyz 0 1
  C   0.0  0.0  0.0
  H   0.0  0.0  1.09
  H   1.03 0.0  -0.36
  H  -0.51 0.89  -0.36
  H  -0.51 -0.89  -0.36
*
```

## 15. PES Scan

```
! B3LYP def2-TZVP SP
%geom
  Scan
    B 0 1 = 0.9, 1.2, 16
  end
end

* xyz 0 1
  O  0.0  0.0  0.0
  H  0.9  0.0  0.0
  H -0.5  0.8  0.0
*
```

## 16. Frozen Core Calculation

```
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C TightSCF FrozenCore SP
%maxcore 8000
%pal nprocs 8 end

* xyz 0 1
  Cu  0.0  0.0  0.0
  Cl  2.3  0.0  0.0
  Cl -2.3  0.0  0.0
  Cl  0.0  2.3  0.0
  Cl  0.0 -2.3  0.0
*
```

## 17. Implicit Solvation with SMD

```
! B3LYP def2-TZVP OPT SMD(Water) D3BJ TightSCF
%maxcore 4000

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
*
```

## 18. Unrestricted Calculation (Triplet O2)

```
! UKS B3LYP def2-TZVP TightSCF SP
%scf
  Guess PModel
end

* xyz 0 3
  O  0.0  0.0  0.0
  O  1.2  0.0  0.0
*
```
