# ORCA-Related Tools, Parsers, and Converters (GitHub)

> Sources:
> - GitHub Topics: https://github.com/topics/orca-quantum-chemistry
> - GitHub search results for ORCA parser/converter tools
> Collected: 2026-06-12

## Official ORCA Repositories

### ORCAQuantumChemistry Organization
- URL: https://github.com/ORCAQuantumChemistry
- The official GitHub organization for ORCA Quantum Chemistry.

### CompoundScripts
- URL: https://github.com/ORCAQuantumChemistry/CompoundScripts
- Official repository containing compound scripts for automating workflows within ORCA.
- Allows users to automate complicated calculations directly within ORCA.
- 113+ stars, 25+ forks.

## ORCA Output Parsers

### orca_parser
- URL: https://github.com/avanteijlingen/orca_parser
- PyPI: https://pypi.org/project/orca-parser/
- Install: `pip install orca-parser`
- Python module for parsing data from ORCA output files.
- Extracts energies, geometries, frequencies, and other computed properties.

### cclib (via parse-patrol)
- URL: https://github.com/ndaelman-hu/parse-patrol
- MCP servers for agentic parser tools for quantum chemistry output files.
- Wraps cclib: multi-format parser supporting Gaussian, ORCA, and many other QC programs.
- Also wraps iodata for various chemistry format parsing.

### qccodec
- URL: https://github.com/coltonbh/qccodec
- A library for parsing quantum chemistry I/O.
- Encodes inputs into native QC files, decodes (parses) program outputs into structured `qcdata` objects.
- Supports ORCA among multiple formats.

### qccop (qccompute)
- URL: https://github.com/coltonbh/qcop
- A package for operating Quantum Chemistry programs using `qcio` standardized data structures.
- Compatible with TeraChem, psi4, QChem, NWChem, ORCA, Molpro, and more.

## ORCA Automation Tools

### Parallelized-DFT-ORCA
- URL: https://github.com/aspuru-guzik-group/Parallelized-DFT-ORCA
- Automates the full workflow: geometry optimization -> frequency checks -> vertical excitation energy calculations -> NTO analysis.
- From the Aspuru-Guzik group.

### ORCA_run
- URL: https://github.com/glibaniosr/ORCA_run
- Shell/bash script to help start and run electronic structure calculations with ORCA.

### qtaim_generator
- URL: https://github.com/santi921/qtaim_generator
- High-throughput post-processing package wrapping Multiwfn and ORCA for QTAIM descriptors.

## ORCA Interfaces

### ASE (Atomic Simulation Environment) ORCA Calculator
- Docs: https://ase-lib.org/ase/calculators/orca.html
- Interface for running ORCA calculations from the ASE Python framework.
- Supports SCF, (TD)DFT, semi-empirical, MP2, CASSCF, and coupled cluster.

### ASH Framework ORCA Interface
- Docs: https://ash.readthedocs.io/en/latest/ORCA-interface.html
- Highly flexible interface to ORCA handling input generation, output parsing, and data extraction.

### ORCA Python Interface (OPI)
- Paper: https://pubs.acs.org/doi/10.1021/acs.jctc.5c02141
- Open-source Python interface for ORCA input creation, job execution, and output parsing.
- Released with ORCA 6.1.

### Multiwfn + ORCA
- URL: http://sobereva.com/multiwfn/
- Multiwfn can generate ORCA input files and process ORCA output for wavefunction analysis.

## AI/ML Tools for ORCA

### DELFIN
- URL: https://github.com/ComPlat/DELFIN
- Open-source AI-orchestrated computational chemistry platform.
- Automates first-principles molecular property prediction.

### Q-stack
- URL: https://github.com/lcmd-epfl/Q-stack
- Stack of codes for pre- and post-processing tasks for Quantum Machine Learning.
- Python-based library with broad QC support.

### GUIDE
- Paper: https://onlinelibrary.wiley.com/doi/full/10.1002/jcc.27177
- GUI tool (YASARA plugin) for automated quantum chemistry calculations.
- Supports ORCA and MOPAC simulation packages.

## File Format Tools

### orca_2json
- Part of ORCA utilities (documented in ORCA manual section 9.3).
- Converts ORCA output to JSON format for programmatic access.

### OpenBabel
- URL: https://github.com/openbabel/openbabel
- Can convert between chemical file formats including XYZ (used by ORCA).

## Key Takeaways for orca-lsp

1. **Parsing patterns**: The `orca_parser` and `cclib` projects provide reference implementations for parsing ORCA output files.
2. **Input validation**: The `ASE` and `ASH` interfaces show how to programmatically generate valid ORCA input.
3. **Compound scripts**: The official `CompoundScripts` repository demonstrates multi-step workflow patterns.
4. **Structured output**: The `orca_2JSON` utility and `property.txt` file format provide machine-readable output.
5. **Keyword validation**: Tools like `Multiwfn` and `qccodec` maintain keyword lists that can inform LSP autocompletion.
