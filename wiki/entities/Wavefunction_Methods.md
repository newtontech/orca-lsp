# 波函数方法 / Wavefunction Methods

> 类型：方法 / Method
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

波函数方法是基于电子薛定谔方程的从头算方法，ORCA支持多种Hartree-Fock和后HF方法。

## Hartree-Fock方法 / Hartree-Fock Methods

### HF变体 / HF Variants

- **HF**：标准Hartree-Fock方法
- **RHF**：限制闭壳层Hartree-Fock
- **UHF**：非限制开壳层Hartree-Fock
- **ROHF**：限制开壳层Hartree-Fock

## 微扰理论方法 / Perturbation Theory Methods

### MP系列 / MP Series

- **MP2**：Møller-Plesset二阶微扰理论
- **RI-MP2**：分辨率恒等MP2（加速版）
- **SCS-MP2**：自旋成分缩放MP2
- **MP3**：Møller-Plesset三阶微扰理论

## 耦合簇方法 / Coupled Cluster Methods

### CC系列 / CC Series

- **CCSD**：耦合簇单双激发
- **CCSD(T)**：CCSD加微扰三重激发（金标准）
- **DLPNO-CCSD**：域基局部对自然轨道CCSD
- **DLPNO-CCSD(T)**：DLPNO-CCSD加微扰三重激发

DLPNO方法大幅降低计算成本，适用于中等大小分子。

## 多参考方法 / Multireference Methods

对于强相关电子系统：

- **CASSCF**：完全活动空间自洽场
- **NEVPT2**：N电子价态微扰理论二阶
- **CASPT2**：完全活动空间微扰理论二阶
- **MRPT**：多参考微扰理论

## DFT方法类型 / DFT Method Types

- **DFT**：通用DFT计算
- **RKS**：限制Kohn-Sham DFT
- **UKS**：非限制Kohn-Sham DFT
- **ROKS**：限制开壳层Kohn-Sham DFT

## 使用示例 / Usage Examples

```orca
# 标准HF计算
! RHF def2-TZVP SP

# MP2相关能校正
! MP2 def2-TZVP SP

# 高精度耦合簇（小分子）
! CCSD(T) def2-QZVPP SP

# 大分子耦合簇（DLPNO近似）
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C SP

# 多参考计算
! CASSCF def2-TZVP SP
%casscf
  nel 10
  norb 8
  mult 1
end
```

## 相关来源 / Related Sources

- `src/orca_lsp/keywords.py`：WAVEFUNCTION_METHODS字典
- `raw/assets/examples/benzene.inp`

## 相关实体/概念 / Related Entities/Concepts

- [[ORCA_Quantum_Chemistry]]
- [[DFT_Functionals]]
- [[Basis_Sets]]
