# %块 / Percent Blocks

> 类型：参数块 / Parameter Block
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

%块用于设置ORCA计算的具体参数，从内存分配到方法特定选项。

## 核心%块 / Core % Blocks

### %maxcore：内存设置 / Memory Settings

设置每个核心的内存（MB）：

```orca
%maxcore 4000
```

推荐值：
- 小体系（<50原子）：1000 MB
- 中等体系（50-100原子）：2000 MB
- 大体系（100-200原子）：4000 MB
- 超大体系（>200原子）：8000 MB

### %pal：并行设置 / Parallelization Settings

设置并行核心数：

```orca
%pal nprocs 4 end
```

### %method：方法设置 / Method Settings

设置方法特定参数（色散等）：

```orca
%method D3BJ end
%cpcm
  epsilon 80.4
end
```

### %scf：SCF收敛设置 / SCF Convergence Settings

```orca
%scf
  maxiter 100
  conv 6
end
```

## 几何相关%块 / Geometry-related % Blocks

### %geom：几何优化设置 / Geometry Optimization Settings

```orca
%geom
  maxiter 50
  Calc_Hess true
  Recalc_Hess 5
end
```

### %coords：坐标系统设置 / Coordinate System Settings

```orca
%coords
  internals on
end
```

## 频率和热力学%块 / Frequency & Thermodynamics % Blocks

### %freq：频率计算设置 / Frequency Calculation Settings

```orca
%freq
  temp 298.15
  start Hessian
end
```

## 分子动力学%块 / Molecular Dynamics % Block

### %md：分子动力学设置 / MD Settings

```orca
%md
  timestep 0.5
  nstep 1000
  temp 298.15
end
```

## 激发态%块 / Excited State % Blocks

### %tddft：TD-DFT设置 / TD-DFT Settings

```orca
%tddft
  nroots 10
  maxdim 100
end
```

### %cis：CI Singles设置 / CIS Settings

```orca
%cis
  nroots 5
end
```

## 溶剂化%块 / Solvation % Blocks

### %cpcm：CPCM溶剂模型 / CPCM Solvent Model

```orca
%cpcm
  epsilon 80.4
  refrac 1.33
end
```

## 性质计算%块 / Property Calculation % Blocks

### %eprnmr：EPR/NMR性质 / EPR/NMR Properties

```orca
%eprnmr
  gtensor 1
end
```

### %elprop：电子性质 / Electronic Properties

```orca
%elprop
  dipole true
end
```

## 高级方法%块 / Advanced Method % Blocks

### %cp：Counterpoise校正 / Counterpoise Correction

```orca
%cp
  fragments 2
  charge(1) 0 1
  charge(2) 0 1
end
```

### %rirpa：RI-RPA计算 / RI-RPA Calculations

```orca
%rirpa
  nroots 10
end
```

### %mrcc：多参考耦合簇 / Multireference Coupled Cluster

```orca
%mrcc
  method MkMRCCSD(T)
end
```

## 其他%块 / Other % Blocks

- `%basis`：基组设置
- `%loc`：轨道局域化
- `%plots`：绘图设置
- `%moinp`：MO输入
- `%output`：输出文件设置
- `%symmetry`：对称性设置
- `%rels`：相对论设置

## 相关来源 / Related Sources

- `src/orca_lsp/keywords.py`：PERCENT_BLOCKS字典
- `raw/assets/examples/td_dft.inp`
- `raw/assets/examples/solvation.inp`
- `raw/assets/examples/counterpoise.inp`

## 相关实体/概念 / Related Entities/Concepts

- [[ORCA_Quantum_Chemistry]]
- [[Job_Types]]
- [[Geometry_Section]]
