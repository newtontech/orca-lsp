# 元素符号 / Element Symbols

> 类型：数据 / Data
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

ORCA支持前86号元素（氢到氡）的元素符号，用于几何结构部分定义原子。元素符号验证是输入验证的重要组成部分。

## 支持的元素 / Supported Elements

### 主族元素 / Main Group Elements

| 周期 | 1 | 2 | 13 | 14 | 15 | 16 | 17 | 18 |
|------|---|---|----|----|----|----|----|----|
| 1 | **H** | **He** | | | | | | |
| 2 | **Li** | **Be** | **B** | **C** | **N** | **O** | **F** | **Ne** |
| 3 | **Na** | **Mg** | **Al** | **Si** | **P** | **S** | **Cl** | **Ar** |
| 4 | **K** | **Ca** | **Ga** | **Ge** | **As** | **Se** | **Br** | **Kr** |
| 5 | **Rb** | **Sr** | **In** | **Sn** | **Sb** | **Te** | **I** | **Xe** |
| 6 | **Cs** | **Ba** | **Tl** | **Pb** | **Bi** | **Po** | **At** | **Rn** |

### 过渡金属 / Transition Metals

| 系列 | 3B | 4B | 5B | 6B | 7B | 8B | 1B | 2B |
|------|----|----|----|----|----|----|----|----|
| 4d | **Sc** | **Ti** | **V** | **Cr** | **Mn** | **Fe** **Co** **Ni** | **Cu** | **Zn** |
| 5d | **Y** | **Zr** | **Nb** | **Mo** | **Tc** | **Ru** **Rh** **Pd** | **Ag** | **Cd** |

### 镧系元素 / Lanthanides

**La, Ce, Pr, Nd, Pm, Sm, Eu, Gd, Tb, Dy, Ho, Er, Tm, Yb, Lu**

### 锕系元素 / Actinides

**Ac, Th, Pa, U, Np, Pu, Am, Cm, Bk, Cf, Es, Fm, Md, No**

## 元素符号格式 / Element Symbol Format

- **大小写**：首字母大写，第二字母小写（如"C"、"Cl"）
- **全小写**：ORCA通常接受小写（如"o"、"h"）
- **全大写**：部分情况可接受

## 常见错误 / Common Errors

### 拼写错误

```orca
# 错误
* xyz 0 1
  C   0.0   0.0   0.0
  Hh  1.0   0.0   0.0    # 错误：Hh
*

# 正确
* xyz 0 1
  C   0.0   0.0   0.0
  H   1.0   0.0   0.0
*
```

### 不支持的元素

ORCA不支持超重元素（>86号，如Fr、Ra等）。

## 同位素指定 / Isotope Specification

ORCA支持同位素质量指定（在几何部分之后）：

```orca
* xyz 0 1
  H   0.0   0.0   0.0
  D   1.0   0.0   0.0    # 氘
*
%basis
  newgto D
    1s, 1.0
   end
end
```

## 赝原子 / Dummy Atoms

用于约束或对称性：

```orca
* xyz 0 1
  C   0.0   0.0   0.0
  H   1.0   0.0   0.0
  X   2.0   0.0   0.0    # 赝原子（无电子）
*
```

## 验证规则 / Validation Rules

orca-lsp会检查：

1. 元素符号是否在支持的元素列表中
2. 拼写是否正确
3. 大小写是否规范（警告而非错误）

## 相关来源 / Related Sources

- `src/orca_lsp/keywords.py`：ELEMENTS列表

## 相关实体/概念 / Related Entities/Concepts

- [[Geometry_Section]]
- [[Atomic_Coordinates]]
