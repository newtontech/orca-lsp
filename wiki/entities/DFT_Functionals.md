# DFT泛函 / DFT Functionals

> 类型：方法 / Method
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

密度泛函理论（DFT）泛函是ORCA中最常用的电子结构方法。`orca-lsp`支持45+种DFT泛函，包括杂化泛函、GGA、meta-GGA、双杂化泛函和范围分离泛函。

## 泛函分类 / Functional Categories

### 杂化泛函 / Hybrid Functionals

包含部分Hartree-Fock交换的泛函：

- **B3LYP**：最常用的杂化泛函（20% HF交换）
- **PBE0**：PBE0杂化泛函（25% HF交换）
- **M06-2X**：M06-2X杂化meta-GGA泛函（54% HF交换）
- **M06**、**M06-HF**、**TPSS0**、**X3LYP**、**O3LYP**

### GGA泛函 / GGA Functionals

广义梯度近似泛函：

- **PBE**：PBE GGA泛函
- **BP86**：Becke-Perdew 86 GGA泛函
- **BLYP**：Becke-Lee-Yang-Parr GGA泛函
- **B97**、**revPBE**、**RPBE**、**OLYP**

### Meta-GGA泛函 / Meta-GGA Functionals

包含动能密度的泛函：

- **TPSS**：TPSS meta-GGA泛函
- **M06L**：M06L meta-GGA泛函
- **SCAN**：强约束适当泛函
- **r2SCAN**：重新正则化的SCAN泛函
- **MN15-L**、**M11-L**

### 范围分离泛函 / Range-Separated Functionals

适用于电荷转移激发态：

- **ωB97X-D**：含色散的范围分离杂化泛函
- **ωB97X-V**：ωB97X-V范围分离杂化泛函
- **ωB97X-D3**、**ωB97X-D4**、**ωB97M-D**
- **CAM-B3LYP**：Coulomb衰减B3LYP
- **LC-ωPBE**、**LC-ωPBEh**
- **M08-HX**、**M08-SO**、**M11**

### 双杂化泛函 / Double-Hybrid Functionals

包含MP2型相关校正：

- **B2PLYP**：B2PLYP双杂化泛函
- **DSD-BLYP**：DSD-BLYP双杂化泛函
- **DSD-PBEB95**、**DSD-PBEP86**、**PWPB95**、**DOD-PBEP86**

## 使用示例 / Usage Examples

```orca
# 杂化泛函优化
! B3LYP def2-TZVP OPT

# 范围分离泛函用于电荷转移
! CAM-B3LYP def2-TZVP SP

# 双杂化泛函用于高精度
! B2PLYP def2-QZVPP SP
```

## 相关来源 / Related Sources

- `src/orca_lsp/keywords.py`：DFT_FUNCTIONALS字典

## 相关实体/概念 / Related Entities/Concepts

- [[ORCA_Quantum_Chemistry]]
- [[Basis_Sets]]
- [[Job_Types]]
