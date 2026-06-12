# 过渡态搜索 / Transition State Search

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

过渡态（TS）是化学反应势能面上的一阶鞍点，对应于反应路径上的能量最高点。TS搜索对于理解反应机理和计算反应能垒至关重要。

## 核心机制 / Core Mechanism

### Hessian矩阵分析

- **鞍点特征**：一个负本征值（虚频）
- **虚频方向**：对应于反应坐标
- **能量**：反应能垒高度

### TS优化算法

1. **Berny算法**：基于梯度和Hessian
2. **Dimer方法**：沿最低曲率方向搜索
3. **NEB（弹性带）**：连接反应物和产物

## ORCA中的TS搜索 / TS Search in ORCA

### 基本TS计算

```orca
! B3LYP def2-TZVP TS
```

### 高级设置 / Advanced Settings

```orca
%geom
  Calc_Hess true      # 计算初始Hessian
  Recalc_Hess 5       # 每5步重新计算Hessian
end
```

## 工作流程 / Workflow

### 1. 反应物和产物优化

```orca
# 反应物
! B3LYP def2-TZVP OPT

# 产物
! B3LYP def2-TZVP OPT
```

### 2. 初始TS猜测

- 从反应物/产物插值
- 使用经验键长
- 从类似反应的TS结构修改

### 3. TS优化

```orca
! B3LYP def2-TZVP TS
%geom
  Calc_Hess true
end
```

### 4. 频率验证

必须有一个虚频：

```orca
! B3LYP def2-TZVP FREQ
```

### 5. IRC验证

确认TS连接正确的反应物和产物：

```orca
! B3LYP def2-TZVP IRC
```

## 难点与解决方案 / Challenges and Solutions

| 问题 | 解决方案 |
|------|----------|
| 收敛到极小点 | 提供更好的初始猜测 |
| Hessian计算昂贵 | 使用RI近似或%geom Recalc_Hess |
| 找到错误的TS | 分析虚频模式，调整结构 |
| IRC计算失败 | 增加点数，减小步长 |

## 相关概念 / Related Concepts

- [[Intrinsic_Reaction_Coordinate]]
- [[Frequency_Calculation]]
- [[Energy_Barrier]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/examples/transition_state.inp`
