"""ORCA keywords and constants"""

# DFT Functionals
DFT_FUNCTIONALS = {
    # Hybrid functionals
    "B3LYP": {"type": "hybrid", "description": "B3LYP hybrid functional (20% HF exchange)"},
    "PBE0": {"type": "hybrid", "description": "PBE0 hybrid functional (25% HF exchange)"},
    "TPSS0": {"type": "hybrid", "description": "TPSS0 hybrid functional"},
    "M06": {"type": "hybrid", "description": "M06 hybrid meta-GGA functional"},
    "M06-2X": {"type": "hybrid", "description": "M06-2X hybrid meta-GGA functional (54% HF exchange)"},
    "M06L": {"type": "meta-gga", "description": "M06L meta-GGA functional"},
    "M06-HF": {"type": "hybrid", "description": "M06-HF high-HF exchange functional (100% HF)"},
    "ωB97X-D": {"type": "hybrid", "description": "ωB97X-D range-separated hybrid functional with dispersion"},
    "ωB97X-V": {"type": "hybrid", "description": "ωB97X-V range-separated hybrid functional"},
    "B97-D": {"type": "gga", "description": "B97-D GGA functional with dispersion"},
    "B97-D3": {"type": "gga", "description": "B97-D3 GGA functional with D3 dispersion"},
    "B2PLYP": {"type": "double-hybrid", "description": "B2PLYP double-hybrid functional"},
    "DSD-BLYP": {"type": "double-hybrid", "description": "DSD-BLYP double-hybrid functional"},
    
    # GGA functionals
    "PBE": {"type": "gga", "description": "PBE GGA functional"},
    "BP86": {"type": "gga", "description": "Becke-Perdew 86 GGA functional"},
    "BLYP": {"type": "gga", "description": "Becke-Lee-Yang-Parr GGA functional"},
    "TPSS": {"type": "meta-gga", "description": "TPSS meta-GGA functional"},
    "B97": {"type": "gga", "description": "B97 GGA functional"},
    "revPBE": {"type": "gga", "description": "Revised PBE GGA functional"},
    "RPBE": {"type": "gga", "description": "RPBE GGA functional"},
    "OLYP": {"type": "gga", "description": "Handy-Cohen optimized LYP functional"},
}

# Wavefunction methods
WAVEFUNCTION_METHODS = {
    "HF": {"description": "Hartree-Fock method"},
    "RHF": {"description": "Restricted Hartree-Fock"},
    "UHF": {"description": "Unrestricted Hartree-Fock"},
    "ROHF": {"description": "Restricted Open-shell Hartree-Fock"},
    "MP2": {"description": "Møller-Plesset second-order perturbation theory"},
    "RI-MP2": {"description": "Resolution-of-Identity MP2"},
    "SCS-MP2": {"description": "Spin-component scaled MP2"},
    "MP3": {"description": "Møller-Plesset third-order perturbation theory"},
    "CCSD": {"description": "Coupled Cluster Singles and Doubles"},
    "CCSD(T)": {"description": "CCSD with perturbative triples (gold standard)"},
    "DLPNO-CCSD": {"description": "Domain-based Local Pair Natural Orbital CCSD"},
    "DLPNO-CCSD(T)": {"description": "DLPNO-CCSD with perturbative triples"},
    "CASSCF": {"description": "Complete Active Space SCF"},
    "NEVPT2": {"description": "N-electron valence state PT2"},
    "CASPT2": {"description": "Complete Active Space PT2"},
    "MRPT": {"description": "Multireference perturbation theory"},
}

# Basis sets
BASIS_SETS = {
    # Pople basis sets
    "STO-3G": {"type": "minimal", "description": "Minimal basis set (Slater-type orbitals with 3 Gaussians)"},
    "3-21G": {"type": "small", "description": "Small split-valence basis set"},
    "6-31G": {"type": "medium", "description": "Split-valence basis set with 6 Gaussians for core"},
    "6-31G*": {"type": "medium-polarized", "description": "6-31G with d polarization on non-hydrogen atoms"},
    "6-31G**": {"type": "medium-polarized", "description": "6-31G with d polarization on non-H and p on H"},
    "6-31+G*": {"type": "medium-diffuse", "description": "6-31G* with diffuse functions on non-H"},
    "6-311G": {"type": "large", "description": "Triple-zeta split-valence basis"},
    "6-311G*": {"type": "large-polarized", "description": "6-311G with d polarization"},
    "6-311G**": {"type": "large-polarized", "description": "6-311G with d on non-H and p on H"},
    "6-311+G*": {"type": "large-diffuse", "description": "6-311G* with diffuse functions"},
    "6-311++G**": {"type": "large-diffuse", "description": "6-311G** with diffuse on all atoms"},
    
    # Karlsruhe basis sets (def2)
    "def2-SVP": {"type": "medium", "description": "Karlsruhe split-valence polarized basis"},
    "def2-TZVP": {"type": "large", "description": "Karlsruhe triple-zeta valence polarized basis"},
    "def2-TZVPP": {"type": "large", "description": "Karlsruhe triple-zeta with more polarization"},
    "def2-QZVP": {"type": "very-large", "description": "Karlsruhe quadruple-zeta valence polarized"},
    "def2-QZVPP": {"type": "very-large", "description": "Karlsruhe quadruple-zeta with more polarization"},
    "def2-SVPD": {"type": "medium-diffuse", "description": "def2-SVP with diffuse functions"},
    "def2-TZVPD": {"type": "large-diffuse", "description": "def2-TZVP with diffuse functions"},
    
    # Dunning correlation-consistent basis sets
    "cc-pVDZ": {"type": "medium", "description": "Correlation-consistent polarized valence double-zeta"},
    "cc-pVTZ": {"type": "large", "description": "Correlation-consistent polarized valence triple-zeta"},
    "cc-pVQZ": {"type": "very-large", "description": "Correlation-consistent polarized valence quadruple-zeta"},
    "cc-pV5Z": {"type": "huge", "description": "Correlation-consistent polarized valence quintuple-zeta"},
    "aug-cc-pVDZ": {"type": "medium-diffuse", "description": "cc-pVDZ with diffuse functions"},
    "aug-cc-pVTZ": {"type": "large-diffuse", "description": "cc-pVTZ with diffuse functions"},
    "aug-cc-pVQZ": {"type": "very-large-diffuse", "description": "cc-pVQZ with diffuse functions"},
    
    # Auxiliary basis sets
    "def2/J": {"type": "auxiliary", "description": "Karlsruhe auxiliary basis for Coulomb fitting"},
    "def2-TZVP/C": {"type": "auxiliary", "description": "Karlsruhe auxiliary basis for correlation (TZVP)"},
    "def2-QZVP/C": {"type": "auxiliary", "description": "Karlsruhe auxiliary basis for correlation (QZVP)"},
    "cc-pVTZ-f12-optri": {"type": "auxiliary", "description": "Optimal RI auxiliary basis for F12 methods"},
}

# Job types
JOB_TYPES = {
    "SP": {"description": "Single point energy calculation"},
    "OPT": {"description": "Geometry optimization"},
    "FREQ": {"description": "Frequency calculation (analytical or numerical)"},
    "NUMFREQ": {"description": "Numerical frequency calculation"},
    "OPT FREQ": {"description": "Geometry optimization followed by frequency"},
    "TS": {"description": "Transition state optimization"},
    "IRC": {"description": "Intrinsic reaction coordinate calculation"},
    "SCAN": {"description": "Potential energy surface scan"},
    "MD": {"description": "Molecular dynamics simulation"},
    "MOLECULAR DYNAMICS": {"description": "Molecular dynamics simulation"},
}

# % Blocks
PERCENT_BLOCKS = {
    "maxcore": {"description": "Set memory per core in MB", "example": "%maxcore 4000"},
    "pal": {"description": "Parallelization settings", "example": "%pal nprocs 4 end"},
    "method": {"description": "Method-specific settings", "example": "%method D3BJ end"},
    "basis": {"description": "Basis set settings", "example": "%basis newGTO H \"cc-pVTZ\" end"},
    "scf": {"description": "SCF convergence settings", "example": "%scf maxiter 100 end"},
    "geom": {"description": "Geometry optimization settings", "example": "%geom maxiter 50 end"},
    "freq": {"description": "Frequency calculation settings", "example": "%freq temp 298.15 end"},
    "md": {"description": "Molecular dynamics settings", "example": "%md timestep 0.5 end"},
    "loc": {"description": "Orbital localization settings", "example": "%loc LocMet IBO end"},
    "plots": {"description": "Plot generation settings", "example": "%plots format cube end"},
    "cp": {"description": "Counterpoise correction settings", "example": "%cp fragments 2 end"},
    "elprop": {"description": "Electronic properties settings", "example": "%elprop dipole true end"},
    "coords": {"description": "Coordinate system settings", "example": "%coords internals on end"},
}

# All valid keywords (for diagnostics)
ALL_KEYWORDS = {
    **DFT_FUNCTIONALS,
    **WAVEFUNCTION_METHODS,
    **BASIS_SETS,
    **JOB_TYPES,
}

# Common element symbols for geometry validation
ELEMENTS = [
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne",
    "Na", "Mg", "Al", "Si", "P", "S", "Cl", "Ar", "K", "Ca",
    "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn",
    "Ga", "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr",
    "Nb", "Mo", "Tc", "Ru", "Rh", "Pd", "Ag", "Cd", "In", "Sn",
    "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd",
    "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb",
    "Lu", "Hf", "Ta", "W", "Re", "Os", "Ir", "Pt", "Au", "Hg",
    "Tl", "Pb", "Bi", "Po", "At", "Rn"
]

# %maxcore recommendations (in MB) based on system size
MAXCORE_RECOMMENDATIONS = {
    "small": 1000,    # < 50 atoms
    "medium": 2000,   # 50-100 atoms
    "large": 4000,    # 100-200 atoms
    "very_large": 8000,  # > 200 atoms
}
