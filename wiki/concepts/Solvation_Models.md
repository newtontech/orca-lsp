# 溶剂化模型 / Solvation Models

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

溶剂化模型用于模拟溶液中分子的电子结构和性质，无需显式溶剂分子。连续介质模型将溶剂视为介电连续体。

## 核心机制 / Core Mechanism

### CPCM：导体极化连续模型

CPCM是ORCA中最常用的溶剂模型：

- **介电常数（ε）**：表征溶剂极化能力
- **折射率（n）**：用于非静电项
- **溶剂腔**：由分子范德华表面构建

### ORCA中的CPCM使用 / CPCM in ORCA

```orca
! B3LYP def2-SVP OPT CPCM(Water)
%cpcm
  epsilon 80.4    # 水的介电常数
  refrac 1.33     # 水的折射率
end
```

## 常用溶剂参数 / Common Solvent Parameters

| 溶剂 | ε | n |
|------|-------|-----|
| 水 | 80.4 | 1.33 |
| 甲醇 | 32.6 | 1.33 |
| 乙醇 | 24.3 | 1.36 |
| 乙腈 | 35.9 | 1.34 |
| DMSO | 46.7 | 1.48 |
| 氯仿 | 4.7 | 1.44 |
| 苯 | 2.2 | 1.50 |
| 环己烷 | 2.0 | 1.43 |

## 应用场景 / Applications

- **溶液相反应**：反应能和能垒
- **光谱性质**：UV-Vis、荧光位移
- **氧化还原电位**：电极电势计算
- **构象平衡**：极性/非极性构象稳定性

## 溶剂化能计算 / Solvation Energy

```orca
# 气相计算
! B3LYP def2-TZVP SP

# 溶液相计算
! B3LYP def2-TZVP SP CPCM(Water)
%cpcm epsilon 80.4 end
```

溶剂化能 = E溶液 - E气相

## 精度考虑 / Accuracy Considerations

- **优点**：快速、无需显式溶剂
- **局限**：忽略氢键特异性、熵效应
- **改进**：SMD模型（ORCA 5+）、显式-隐式混合

## 相关概念 / Related Concepts

- [[Dielectric_Constant]]
- [[Solvation_Energy]]
- [[Explicit_Solvent_Modeling]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/examples/solvation.inp`
