# 基组 / Basis Sets

> 类型：参数 / Parameter
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

基组是用于展开分子轨道的原子轨道线性组合。ORCA支持多种基组系列，`orca-lsp`包含38+种基组定义。

## 基组系列 / Basis Set Series

### Pople系列 / Pople Basis Sets

经典的分裂价键基组：

- **STO-3G**：最小基组（3个高斯函数拟合Slater型轨道）
- **3-21G**：小型分裂价键基组
- **6-31G**：中等分裂价键基组
- **6-31G***：6-31G加d极化（非氢原子）
- **6-31G****：6-31G加d极化（非氢）和p极化（氢）
- **6-31+G***：6-31G*加弥散函数（非氢）
- **6-311G**：三ζ分裂价键基组
- **6-311G***、**6-311G****、**6-311+G***、**6-311++G****

### Karlsruhe def2系列 / Karlsruhe def2 Basis Sets

现代高效基组：

- **def2-SVP**：分裂价键极化基组（中等大小）
- **def2-TZVP**：三ζ价键极化基组（大型）
- **def2-TZVPP**：三ζ加更多极化（大型）
- **def2-QZVP**：四ζ价键极化基组（超大）
- **def2-QZVPP**：四ζ加更多极化（超大）
- **def2-SVPD**、**def2-TZVPD**：带弥散函数

### Dunning cc-pVXZ系列 / Dunning cc-pVXZ Basis Sets

相关一致基组：

- **cc-pVDZ**：相关一致极化价键双ζ基组
- **cc-pVTZ**：相关一致极化价键三ζ基组
- **cc-pVQZ**：相关一致极化价键四ζ基组
- **cc-pV5Z**：相关一致极化价键五ζ基组
- **aug-cc-pVDZ**、**aug-cc-pVTZ**、**aug-cc-pVQZ**：加弥散函数

### 辅助基组 / Auxiliary Basis Sets

用于RI/DF近似：

- **def2/J**：Karlsruhe辅助基组（Coulomb拟合）
- **def2-TZVP/C**：TZVP相关辅助基组
- **def2-QZVP/C**：QZVP相关辅助基组
- **cc-pVTZ-f12-optri**：F12方法最优RI辅助基组

### Jensen极化一致基组 / Jensen pc Basis Sets

- **pc-1**、**pc-2**、**pc-3**：极化一致基组（双ζ、三ζ、四ζ）
- **aug-pc-1**、**aug-pc-2**：增强版pc基组

### EPR优化基组 / EPR-Optimized Basis Sets

- **EPR-II**：EPR超精细耦合基组
- **EPR-III**：扩展EPR基组

### 最小增强基组 / Minimal Augmented Basis Sets

- **ma-def2-SVP**：用于DFT的最小增强def2-SVP
- **ma-def2-TZVP**：用于DFT的最小增强def2-TZVP

## 使用示例 / Usage Examples

```orca
# 中等精度优化
! B3LYP def2-SVP OPT

# 高精度单点
! B3LYP def2-TZVP SP

# 超高精度相关能
! CCSD(T) def2-QZVPP SP

# 激发态计算（需弥散函数）
! TD-DFT cam-b3lyp aug-cc-pVTZ SP
```

## 相关来源 / Related Sources

- `src/orca_lsp/keywords.py`：BASIS_SETS字典

## 相关实体/概念 / Related Entities/Concepts

- [[ORCA_Quantum_Chemistry]]
- [[DFT_Functionals]]
- [[Auxiliary_Basis_Sets]]
