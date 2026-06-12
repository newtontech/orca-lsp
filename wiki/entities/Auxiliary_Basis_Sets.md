# 辅助基组 / Auxiliary Basis Sets

> 类型：基组 / Basis Set
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

辅助基组用于分辨率恒等（RI）或密度拟合（DF）近似，大幅加速双电子积分计算。ORCA广泛使用RI近似加速DFT和波函数方法。

## RI/DF近似原理 / RI/DF Approximation Principle

将四中心积分转换为三中心积分：

```
(μν|λσ) ≈ Σ_Q (μν|Q) (Q|λσ)
```

其中Q是辅助基函数。复杂度从O(N⁴)降至O(N³)。

## 辅助基组类型 / Auxiliary Basis Set Types

### Coulomb拟合基组 / Coulomb Fitting Basis Sets

用于电子排斥积分的密度拟合：

- **def2/J**：Karlsruhe Coulomb拟合基组
  - 与def2-SVP/TZVP/QZVP配套使用
  - 自动用于RI-J近似

```orca
! B3LYP def2-TZVP def2/J
```

### 相关辅助基组 / Correlation Auxiliary Basis Sets

用于MP2、CCSD等相关方法：

- **def2-TZVP/C**：TZVP相关辅助基组
- **def2-QZVP/C**：QZVP相关辅助基组

```orca
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C
```

### F12方法辅助基组 / F12 Auxiliary Basis Sets

用于显式相关F12方法：

- **cc-pVTZ-f12-optri**：F12方法最优RI辅助基组
- **cc-pVQZ-f12-optri**：更高精度F12辅助基组

## 加速效果 / Speedup

| 方法 | 无RI | 有RI | 加速比 |
|------|------|------|--------|
| DFT | 1x | 3-5x | 3-5x |
| MP2 | 1x | 5-10x | 5-10x |
| CCSD | 1x | 3-5x | 3-5x |

## 精度损失 / Accuracy Loss

RI/DF近似的精度损失通常可忽略：

- **能量**：<0.1 kcal/mol
- **梯度**：<10⁻⁴ a.u.
- **频率**：<1 cm⁻¹

## 自动匹配规则 / Automatic Matching Rules

ORCA通常自动选择合适的辅助基组：

```orca
# 自动选择def2/J
! B3LYP def2-TZVP

# 手动指定（可选）
! B3LYP def2-TZVP def2/J

# MP2需要相关辅助基组
! MP2 def2-TZVP def2-TZVP/C
```

## 相关来源 / Related Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/examples/benzene.inp`

## 相关实体/概念 / Related Entities/Concepts

- [[Basis_Sets]]
- [[Resolution_of_Identity]]
- [[DLPNO_Methods]]
