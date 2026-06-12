# 作业类型 / Job Types

> 类型：计算类型 / Calculation Type
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

作业类型指定ORCA执行的计算类型，从简单的单点能到复杂的分子动力学模拟。

## 主要作业类型 / Main Job Types

### SP：单点能计算 / Single Point Energy

计算给定几何结构的电子能量：

```orca
! B3LYP def2-TZVP SP
```

### OPT：几何优化 / Geometry Optimization

寻找能量极小点的几何结构：

```orca
! B3LYP def2-TZVP OPT
%geom
  maxiter 50
end
```

### FREQ：频率计算 / Frequency Calculation

计算谐振频率和热力学性质：

```orca
! B3LYP def2-TZVP FREQ
%freq
  temp 298.15
end
```

### NUMFREQ：数值频率 / Numerical Frequency

当解析频率不可用时使用：

```orca
! B3LYP def2-TZVP NUMFREQ
```

### OPT FREQ：优化+频率 / Optimization + Frequency

先优化再计算频率，确认无虚频：

```orca
! B3LYP def2-TZVP OPT FREQ
```

### TS：过渡态优化 / Transition State Optimization

寻找一阶鞍点（过渡态）：

```orca
! B3LYP def2-TZVP TS
%geom
  Calc_Hess true
  Recalc_Hess 5
end
```

### IRC：内禀反应坐标 / Intrinsic Reaction Coordinate

从过渡态出发追踪反应路径：

```orca
! B3LYP def2-TZVP IRC
```

### SCAN：势能面扫描 / Potential Energy Surface Scan

扫描一个或多个几何参数：

```orca
! B3LYP def2-TZVP SCAN
%geom
  Scan
    B 1 2 0.9 1.5 10
  end
end
```

### MD：分子动力学 / Molecular Dynamics

经典或从头算分子动力学：

```orca
! B3LYP def2-SVP MD
%md
  timestep 0.5
  nstep 1000
  temp 298.15
end
```

## 使用建议 / Usage Recommendations

1. **初步探索**：先用小基组（def2-SVP）和SP计算
2. **优化几何**：用中等基组（def2-TZVP）做OPT
3. **验证极小**：在优化后做FREQ确认无虚频
4. **高精度能量**：用大基组（def2-QZVPP）做SP

## 相关来源 / Related Sources

- `src/orca_lsp/keywords.py`：JOB_TYPES字典
- `raw/assets/examples/water.inp`
- `raw/assets/examples/transition_state.inp`

## 相关实体/概念 / Related Entities/Concepts

- [[ORCA_Quantum_Chemistry]]
- [[Percent_Blocks]]
- [[Geometry_Section]]
