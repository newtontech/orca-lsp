# 几何结构部分 / Geometry Section

> 类型：输入部分 / Input Section
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

几何结构部分定义分子中的原子及其坐标，是ORCA输入文件的必需部分。

## XYZ格式 / XYZ Format

最常用的坐标格式：

```orca
* xyz charge multiplicity
  element   x   y   z
  element   x   y   z
  ...
*
```

### 示例：水分子 / Water Molecule

```orca
* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
*
```

### 电荷和自旋多重度 / Charge and Multiplicity

- **电荷**：体系的总电荷（整数）
- **多重度**：2S+1，S为总自旋量子数

常见情况：
- 闭壳层中性分子：`0 1`
- 阳离子：`1 2`（单电子）
- 阴离子：`-1 2`
- 三线态：`0 3`

## 内坐标格式 / Internal Coordinates Format

使用键长、键角、二面角定义结构：

```orca
* int
  geometry {
    O
    H 1 R
    H 1 R 2 A
  }
  values {
    R = 0.96
    A = 104.5
  }
*
```

## 原子坐标单位 / Coordinate Units

- **单位**：埃（Ångström）
- **精度**：通常保留6位小数
- **顺序**：x, y, z笛卡尔坐标

## 元素符号 / Element Symbols

ORCA支持前86号元素（氢到氡）：

```python
H, He, Li, Be, B, C, N, O, F, Ne, Na, Mg, Al, Si, P, S, Cl, Ar,
K, Ca, Sc, Ti, V, Cr, Mn, Fe, Co, Ni, Cu, Zn, Ga, Ge, As, Se, Br, Kr,
Rb, Sr, Y, Zr, Nb, Mo, Tc, Ru, Rh, Pd, Ag, Cd, In, Sn, Sb, Te, I, Xe,
Cs, Ba, La, Ce, Pr, Nd, Pm, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu,
Hf, Ta, W, Re, Os, Ir, Pt, Au, Hg, Tl, Pb, Bi, Po, At, Rn
```

## 验证规则 / Validation Rules

1. 必须以`*`开始，后跟格式类型
2. 必须指定电荷和多重度
3. 每行一个原子：元素符号 + x + y + z
4. 元素符号必须有效
5. 必须以`*`结束

## 相关来源 / Related Sources

- `src/orca_lsp/parser.py`：Geometry解析器
- `raw/assets/examples/water.inp`
- `raw/assets/examples/benzene.inp`

## 相关实体/概念 / Related Entities/Concepts

- [[ORCA_Quantum_Chemistry]]
- [[Percent_Blocks]]
- [[Element_Symbols]]
