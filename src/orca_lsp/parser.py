"""ORCA input file parser"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any
from .keywords import (
    DFT_FUNCTIONALS, 
    WAVEFUNCTION_METHODS, 
    BASIS_SETS, 
    JOB_TYPES,
    ELEMENTS
)


@dataclass
class SimpleInput:
    """Parsed simple input line (!)"""
    methods: List[str] = field(default_factory=list)
    basis_sets: List[str] = field(default_factory=list)
    job_types: List[str] = field(default_factory=list)
    other_keywords: List[str] = field(default_factory=list)
    raw: str = ""
    
    def is_valid(self) -> bool:
        """Check if simple input has required components"""
        return len(self.methods) > 0 or len(self.basis_sets) > 0


@dataclass
class PercentBlock:
    """Parsed % block"""
    name: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""
    line_start: int = 0
    line_end: int = 0
    
    def is_valid(self) -> bool:
        """Check if % block is valid"""
        return bool(self.name)


@dataclass
class Atom:
    """Represents an atom in geometry"""
    element: str = ""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    line_number: int = 0
    
    def is_valid(self) -> bool:
        """Check if atom data is valid"""
        return self.element in ELEMENTS


@dataclass
class Geometry:
    """Parsed geometry section (* xyz ... *)"""
    charge: int = 0
    multiplicity: int = 1
    atoms: List[Atom] = field(default_factory=list)
    format_type: str = "xyz"  # xyz, int, etc.
    line_start: int = 0
    line_end: int = 0
    
    def is_valid(self) -> bool:
        """Check if geometry section is valid"""
        return len(self.atoms) > 0 and all(atom.is_valid() for atom in self.atoms)


@dataclass
class ParseResult:
    """Complete parse result for an ORCA input file"""
    simple_input: Optional[SimpleInput] = None
    percent_blocks: List[PercentBlock] = field(default_factory=list)
    geometry: Optional[Geometry] = None
    errors: List[Dict[str, Any]] = field(default_factory=list)
    warnings: List[Dict[str, Any]] = field(default_factory=list)


class ORCAParser:
    """Parser for ORCA input files"""
    
    def __init__(self):
        self.dft_functionals = set(DFT_FUNCTIONALS.keys())
        self.wavefunction_methods = set(WAVEFUNCTION_METHODS.keys())
        self.basis_sets = set(BASIS_SETS.keys())
        self.job_types = set(JOB_TYPES.keys())
        self.all_methods = self.dft_functionals | self.wavefunction_methods
    
    def parse(self, content: str) -> ParseResult:
        """Parse complete ORCA input file"""
        result = ParseResult()
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                i += 1
                continue
            
            # Parse simple input line (!)
            if stripped.startswith('!'):
                result.simple_input = self.parse_simple_input(stripped, i)
                i += 1
                continue
            
            # Parse % blocks
            if stripped.startswith('%'):
                block, end_line = self.parse_percent_block(lines, i)
                if block:
                    result.percent_blocks.append(block)
                i = end_line + 1
                continue
            
            # Parse geometry section
            if stripped.startswith('*'):
                geom, end_line = self.parse_geometry(lines, i)
                if geom:
                    result.geometry = geom
                i = end_line + 1
                continue
            
            i += 1
        
        # Run diagnostics
        self._run_diagnostics(result)
        
        return result
    
    def parse_simple_input(self, line: str, line_number: int) -> SimpleInput:
        """Parse simple input line starting with !"""
        result = SimpleInput(raw=line, line_number=line_number)
        
        # Remove ! and split by whitespace
        content = line[1:].strip()
        tokens = content.split()
        
        for token in tokens:
            token_upper = token.upper()
            
            if token_upper in self.dft_functionals:
                result.methods.append(token)
            elif token_upper in self.wavefunction_methods:
                result.methods.append(token)
            elif token_upper in self.basis_sets:
                result.basis_sets.append(token)
            elif token_upper in self.job_types:
                result.job_types.append(token)
            else:
                # Check case-insensitively for some keywords
                if token_upper in [k.upper() for k in self.all_methods]:
                    # Find the correct case version
                    for method in self.all_methods:
                        if method.upper() == token_upper:
                            result.methods.append(method)
                            break
                elif token_upper in [k.upper() for k in self.basis_sets]:
                    for basis in self.basis_sets:
                        if basis.upper() == token_upper:
                            result.basis_sets.append(basis)
                            break
                elif token_upper in [k.upper() for k in self.job_types]:
                    for job in self.job_types:
                        if job.upper() == token_upper:
                            result.job_types.append(job)
                            break
                else:
                    result.other_keywords.append(token)
        
        return result
    
    def parse_percent_block(self, lines: List[str], start_line: int) -> Tuple[Optional[PercentBlock], int]:
        """Parse a % block starting at start_line"""
        block = PercentBlock(line_start=start_line)
        
        first_line = lines[start_line].strip()
        
        # Extract block name
        match = re.match(r'%\s*(\w+)', first_line)
        if match:
            block.name = match.group(1).lower()
        else:
            return None, start_line
        
        # Check if block is on single line
        if 'end' in first_line.lower() or first_line.lower().endswith('end'):
            block.raw_content = first_line
            # Parse parameters from single line
            self._parse_block_parameters(block, first_line)
            return block, start_line
        
        # Multi-line block
        content_lines = [first_line]
        i = start_line + 1
        
        while i < len(lines):
            line = lines[i]
            content_lines.append(line)
            
            if line.strip().lower() == 'end':
                break
            i += 1
        
        block.raw_content = '\n'.join(content_lines)
        block.line_end = i
        
        # Parse block-specific parameters
        self._parse_block_parameters(block, block.raw_content)
        
        return block, i
    
    def _parse_block_parameters(self, block: PercentBlock, content: str):
        """Parse parameters for a % block"""
        lines = content.split('\n')
        
        if block.name == 'maxcore':
            # %maxcore 4000
            for line in lines:
                parts = line.split()
                if len(parts) >= 2 and parts[0].lower() == '%maxcore':
                    try:
                        block.parameters['memory'] = int(parts[1])
                    except ValueError:
                        pass
        
        elif block.name == 'pal':
            # %pal nprocs 4 end
            for line in lines:
                if 'nprocs' in line.lower():
                    match = re.search(r'nprocs\s+(\d+)', line, re.IGNORECASE)
                    if match:
                        block.parameters['nprocs'] = int(match.group(1))
        
        elif block.name == 'method':
            # Parse method block
            for line in lines:
                stripped = line.strip().lower()
                if 'd3bj' in stripped:
                    block.parameters['dispersion'] = 'D3BJ'
                elif 'd3' in stripped:
                    block.parameters['dispersion'] = 'D3'
                elif 'd4' in stripped:
                    block.parameters['dispersion'] = 'D4'
        
        elif block.name == 'scf':
            # %scf settings
            for line in lines:
                stripped = line.strip().lower()
                if 'maxiter' in stripped:
                    match = re.search(r'maxiter\s+(\d+)', stripped)
                    if match:
                        block.parameters['maxiter'] = int(match.group(1))
    
    def parse_geometry(self, lines: List[str], start_line: int) -> Tuple[Optional[Geometry], int]:
        """Parse geometry section (* xyz ... *)"""
        geom = Geometry(line_start=start_line)
        
        first_line = lines[start_line].strip()
        
        # Parse header: * xyz charge multiplicity
        # or * int charge multiplicity for internal coordinates
        parts = first_line.split()
        
        if len(parts) < 2:
            return None, start_line
        
        # Check format type
        geom.format_type = parts[1].lower() if len(parts) > 1 else "xyz"
        
        # Parse charge and multiplicity
        if len(parts) >= 4:
            try:
                geom.charge = int(parts[2])
                geom.multiplicity = int(parts[3])
            except ValueError:
                pass
        
        # Parse atom lines
        i = start_line + 1
        while i < len(lines):
            line = lines[i].strip()
            
            # End of geometry
            if line == '*':
                geom.line_end = i
                break
            
            # Parse atom
            atom_parts = line.split()
            if len(atom_parts) >= 4:
                try:
                    atom = Atom(
                        element=atom_parts[0],
                        x=float(atom_parts[1]),
                        y=float(atom_parts[2]),
                        z=float(atom_parts[3]),
                        line_number=i
                    )
                    geom.atoms.append(atom)
                except ValueError:
                    pass
            
            i += 1
        
        return geom, geom.line_end if geom.line_end > 0 else i
    
    def _run_diagnostics(self, result: ParseResult):
        """Run diagnostics and populate errors/warnings"""
        # Check for simple input
        if result.simple_input is None:
            result.errors.append({
                'message': 'Missing simple input line (!) with method and basis set',
                'line': 0,
                'severity': 'error'
            })
        else:
            # Check for method
            if not result.simple_input.methods:
                result.errors.append({
                    'message': 'No method specified in simple input (e.g., B3LYP, HF, MP2)',
                    'line': result.simple_input.line_number if hasattr(result.simple_input, 'line_number') else 0,
                    'severity': 'error'
                })
            
            # Check for basis set
            if not result.simple_input.basis_sets:
                result.errors.append({
                    'message': 'No basis set specified in simple input (e.g., def2-TZVP, 6-31G*)',
                    'line': result.simple_input.line_number if hasattr(result.simple_input, 'line_number') else 0,
                    'severity': 'error'
                })
        
        # Check for geometry
        if result.geometry is None:
            result.errors.append({
                'message': 'Missing geometry section (* xyz charge multiplicity ...)',
                'line': 0,
                'severity': 'error'
            })
        else:
            # Validate atoms
            for atom in result.geometry.atoms:
                if not atom.is_valid():
                    result.errors.append({
                        'message': f'Invalid element symbol: {atom.element}',
                        'line': atom.line_number,
                        'severity': 'error'
                    })
        
        # Check for maxcore recommendation
        has_maxcore = any(b.name == 'maxcore' for b in result.percent_blocks)
        if not has_maxcore:
            result.warnings.append({
                'message': 'Missing %maxcore setting. Recommended: %maxcore 2000-4000 (MB per core)',
                'line': 0,
                'severity': 'warning'
            })
