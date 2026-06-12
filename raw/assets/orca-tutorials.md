# ORCA Tutorials and Learning Resources

> Sources:
> - ORCA 6.0 Tutorials (FACCTs): https://www.faccts.de/docs/orca/6.0/tutorials/
> - ORCA Input Library: https://sites.google.com/site/orcainputlibrary/home
> - Texas A&M HPRC: https://hprc.tamu.edu/training/intro_orca.html
> - Winter School ORCA Intro: https://winterschool.cc/images/ORCAIntro_WSCC_2021.pdf
> Collected: 2026-06-12

## Official Resources

### ORCA 6.0 Tutorials (FACCTs)
- URL: https://www.faccts.de/docs/orca/6.0/tutorials/
- Official tutorials aimed at new users.

**Tutorial Sections:**

#### First Steps
- How to cite
- Installing ORCA
- Hello water! Your first ORCA calculation
- Input and Output
- Running a calculation in parallel
- Graphical User Interfaces (GUI)
- Solving common issues

#### Workflows
- Compound Jobs
- Extrapolation Techniques

#### Properties
- Single point energies
- Geometry optimization
- Vibrational frequencies
- Thermodynamics
- Implicit Solvation Models
- Explicit Solvation (SOLVATOR)
- Conformer Search (GOAT)
- Relativistic corrections
- Dispersion corrections
- Bond Analysis
- Local Energy Decomposition (LED)
- Fractional occupation density (FOD)
- Charge Models

#### Reactivity
- Finding Transition States with NEB-TS
- Transition State Conformers
- Intrinsic Reaction Coordinate (IRC)
- Calculating accurate energy barriers
- Kinetic Isotope Effects (KIE)
- Plotting Fukui functions
- Automated docking (DOCKER)

#### Spectroscopy
- Infrared and Raman
- UV/Vis spectroscopy
- Electronic Circular Dichroism (ECD)
- Vibrational Circular Dichroism (VCD)
- Nuclear Magnetic Resonance (NMR)
- Electron Paramagnetic Resonance (EPR)
- Spin-orbit coupling

#### Multiscale Methods
- QM/XTB ONIOM
- ONIOM methods beyond QM/XTB
- Multiscale NEB-TS for transition states
- Ionic-Crystal-QM/MM

### ORCA 6.1.1 Manual
- URL: https://orca-manual.mpi-muelheim.mpg.de/
- The most comprehensive reference for all ORCA features.
- Organized into major sections:

**Manual Table of Contents:**
1. Quickstart Guide
2. Essential Calculation Elements
   - General Structure of Input File
   - Input of Coordinates
   - Basic Calculation Settings
   - Control of Output
   - Parallel and Multi-Process Runs
   - Self-Consistent-Field (SCF)
   - Basis Sets
   - Resolution-of-the-Identity (RI)
   - Numerical Integration
   - Counterpoise Corrections
   - Relativistic Calculations
   - Implicit Solvation
3. Model Chemistries
   - Wavefunction Types
   - Hartree-Fock Theory
   - DFT
   - Dispersion Corrections
   - Semiempirical Methods
   - Composite Methods (3c)
   - MP2
   - Coupled Cluster (MDCI)
   - CASSCF and RAS/ORMAS
   - ICE-CI
   - DMRG
   - NEVPT2, CASPT2
   - MR-EOM-CC
4. Structure and Reactivity
   - Geometry Optimizations
   - Surface Scans
   - Transition State Searches
   - IRC
   - NEB Method
   - Vibrational Frequencies
   - Thermochemistry
   - GOAT, SOLVATOR, DOCKER
5. Spectroscopy and Properties
   - Population Analysis
   - NBO Analysis
   - Excited States (TD-DFT, ROCIS, EOM-CCSD, etc.)
   - Vibrational Spectroscopy
   - NMR, EPR Parameters
   - Mossbauer Parameters
   - Spin-Orbit Coupling
   - Local Energy Decomposition
6. Multiscale Simulations
7. Molecular Dynamics
8. Workflows and Automatization
   - ORCA Python Interface (OPI)
   - Compound Module
   - Compound Examples
9. Utilities and Visualization
   - Orbital/Density Plots
   - orca_2JSON
   - Property File

## Community Resources

### ORCA Input Library
- URL: https://sites.google.com/site/orcainputlibrary/home
- Community-maintained collection of ORCA input files.
- Note: Not updated for ORCA 6.0 yet. Maintainer seeks help.

**Pages available:**
- Setting up ORCA
- ORCA Common Errors and Problems
- General Input
- Restarting calculations
- Geometry input
- Visualization and printing
- Basis sets
- Effective Core Potentials
- Numerical precision
- SCF Convergence Issues
- Semiempirical methods
- DFT calculations
- MP2 & MP3
- Relativistic approximations
- Geometry optimizations
- Vibrational Frequencies & Thermochemistry
- Molecular properties
- Frozen core calculations
- Coupled cluster
- Excited state calculations
- CASSCF calculations
- Interfaces and QM/MM
- Orbital and density analysis
- Continuum solvation (CPCM, COSMO, SMD)
- Useful scripts and commands for ORCA I/O
- Molecular dynamics

### Texas A&M HPRC Tutorial
- URL: https://hprc.tamu.edu/training/intro_orca.html
- PDF: https://hprc.tamu.edu/files/training/2020/Fall/Intro_ORCA_tutorial.pdf
- Brief introduction to quantum chemistry simulations with ORCA.
- Covers input file structure, running jobs, and basic analysis.

### Winter School ORCA Introduction
- URL: https://winterschool.cc/images/ORCAIntro_WSCC_2021.pdf
- Lecture slides covering ORCA basics.
- Includes geometry optimizations, DFT, basis sets, and practical examples.

### Zipse Group ORCA Input Files
- URL: https://zipse.cup.uni-muenchen.de/teaching/computational-chemistry-2/topics/orca-input-files/
- Practical examples of ORCA input files from a university course.

## Video Tutorials

### Official/Recommended
- **How to Download, Install & Run ORCA**: https://www.youtube.com/watch?v=zrct4Xa-Jdg
- **H2O Geometry Optimization**: https://www.youtube.com/watch?v=onU2vPIGunE
- **Compound Module Tutorial**: https://www.youtube.com/watch?v=6Hk4pDk0vLM
- **ORCA-Python Interface (OPI)**: https://www.youtube.com/watch?v=L-_gLevWA2k

### Comprehensive Course
- **Dr. M. A. Hashmi's YouTube Playlist**: https://www.youtube.com/playlist?list=PLWk-zl-RHnbeS6w418dSucN690VN_j8wA
- From installation to advanced calculations.

## HPC Documentation

- **NERSC**: https://docs.nersc.gov/applications/orca/
- **University of Chicago RCC**: https://docs.rcc.uchicago.edu/software/apps-and-envs/orca/
- **PC2 Paderborn**: https://upb-pc2.atlassian.net/wiki/spaces/PC2DOK/pages/1902859
- **CSC Finland**: https://github.com/CSCfi/csc-user-guide/blob/master/docs/apps/orca.md

## Chinese-Language Resources

- **Multiwfn ORCA Input Generation**: http://sobereva.com/490
- **ORCA 5.0 New Features**: http://sobereva.com/604
- **ORCA Beginner Guide**: https://www.scribd.com/document/690433235/

## Quick Reference Card

For a new ORCA user, the recommended learning path is:

1. **Install ORCA** -- follow the "Installing ORCA" tutorial
2. **Hello Water** -- run your first calculation
3. **Input/Output** -- understand file structure
4. **DFT Optimization** -- learn geometry optimization
5. **Frequencies** -- verify minima, get thermochemistry
6. **TD-DFT** -- calculate excited states
7. **Compound Jobs** -- chain multi-step workflows
8. **Advanced Methods** -- DLPNO-CCSD(T), CASSCF, etc.
