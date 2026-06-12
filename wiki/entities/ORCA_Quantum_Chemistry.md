# ORCA量子化学软件 / ORCA Quantum Chemistry Software

> 类型：软件 / Software
> 创建日期：2026-06-12
> 来源数：10

## 简介 / Introduction

ORCA是由德国马克斯·普朗克研究所开发的量子化学计算软件包，广泛应用于分子结构优化、频率计算、激发态计算等领域。`orca-lsp`项目为ORCA输入文件提供Language Server Protocol支持。

## 关键特性 / Key Features

- **多种计算方法**：DFT、波函数方法（HF、MP2、CCSD(T)等）
- **丰富的基组库**：支持Pople、Karlsruhe def2、Dunning cc-pVXZ等系列
- **高级功能**：DLPNO-CCSD(T)、TD-DFT、EPR/NMR性质计算
- **溶剂化模型**：CPCM等连续介质模型

## 输入文件格式 / Input File Format

ORCA输入文件使用`.inp`扩展名，包含三个主要部分：

1. **简单输入行（!）**：指定方法、基组、作业类型
2. **%块（% blocks）**：设置计算参数
3. **几何结构部分（* xyz ... *）**：定义分子几何结构

```orca
! B3LYP def2-TZVP OPT FREQ
%maxcore 4000
%pal nprocs 4 end

* xyz 0 1
  O   0.000000   0.000000   0.000000
  H   0.757160   0.586260   0.000000
  H  -0.757160   0.586260   0.000000
*
```

## 相关来源 / Related Sources

- `raw/assets/README.md`
- `raw/assets/docs/ARCHITECTURE.md`
- `raw/assets/examples/water.inp`
- `raw/assets/examples/benzene.inp`

## 相关实体/概念 / Related Entities/Concepts

- [[DFT_Functionals]]
- [[Basis_Sets]]
- [[Wavefunction_Methods]]
- [[Job_Types]]
- [[Percent_Blocks]]

## 历史更新 / History Updates

- 2026-06-12：初始创建，基于项目文档和源代码
