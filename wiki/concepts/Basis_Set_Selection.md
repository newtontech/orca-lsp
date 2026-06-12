# 基组选择策略 / Basis Set Selection Strategy

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

基组选择是平衡计算精度和成本的关键决策。不同任务需要不同质量的基组，盲目使用大基组可能导致资源浪费。

## 核心原则 / Core Principles

### 1. 渐进收敛

从小基组开始，逐步升级：

```
def2-SVP → def2-TZVP → def2-TZVPP → def2-QZVPP
```

### 2. 任务适配

不同任务需要不同精度：

| 任务 | 推荐基组 | 原因 |
|------|----------|------|
| 几何优化 | def2-SVP/TZVP | 快速收敛 |
| 频率计算 | def2-TZVP | 足够精度 |
| 反应能 | def2-TZVPP | 需要极化 |
| 高精度 | def2-QZVPP | 接近CBS |
| 激发态 | aug-cc-pVTZ | 需要弥散 |

### 3. 方法匹配

高精度方法需要高质量基组：

- **HF/DFT**：def2-TZVP足够
- **MP2**：def2-TZVPP + 辅助基组
- **CCSD(T)**：def2-QZVPP（小分子）

## 基组系列比较 / Basis Set Series Comparison

### Pople系列（经典但已过时）

- **优点**：熟悉、广泛测试
- **缺点**：缺乏系统性、极化不完整
- **推荐**：仅在比较旧文献时使用

### def2系列（现代标准）

- **优点**：系统性、高效、平衡
- **推荐**：大多数计算的首选

### cc-pVXZ系列（高精度）

- **优点**：系统收敛、易于外推
- **推荐**：高精度基准计算

## 弥散函数 / Diffuse Functions

### 何时需要

- **阴离子**：额外电子需要更大空间
- **激发态**：里德堡和电荷转移态
- **弱相互作用**：氢键、π-π堆积
- **偶极矩/极化率**：电子分布偏远

### 推荐基组

```orca
# 标准
aug-cc-pVDZ
aug-cc-pVTZ

# 紧凑弥散（ORCA特有）
ma-def2-SVP
ma-def2-TZVP
```

## 辅助基组 / Auxiliary Basis Sets

### RI/DF加速

分辨率恒等（RI）或密度拟合（DF）加速双电子积分：

```orca
# 辅助基组自动匹配
! MP2 def2-TZVP def2-TZVP/C

# Coulomb拟合
! B3LYP def2-TZVP def2/J
```

## 完整基组外推 / Complete Basis Set Extrapolation

向CBS极限外推：

```
E(CBS) = E(X) + (E(X) - E(Y)) / (X³ - Y³)
```

X、Y是三ζ、四ζ基组：

```orca
# 三ζ
! B3LYP def2-TZVP SP

# 四ζ
! B3LYP def2-QZVP SP

# 外推到CBS
```

## 相关概念 / Related Concepts

- [[Basis_Sets]]
- [[Basis_Set_Convergence]]
- [[Auxiliary_Basis_Sets]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/docs/ARCHITECTURE.md`
