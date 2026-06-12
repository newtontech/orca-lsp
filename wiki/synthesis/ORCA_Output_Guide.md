# ORCA输出文件解析指南 / ORCA Output File Parsing Guide

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：4

## 核心论点 / Core Argument

ORCA生成多种输出文件，主输出文件包含详细的人类可读计算信息，`property.txt`提供结构化的机器可读数据。理解输出文件结构对于验证计算结果和开发解析工具至关重要。

## 输出文件类型 / Output File Types

| 文件 | 扩展名/格式 | 用途 |
|------|-----------|------|
| 主输出 | 无扩展名 | 完整计算细节 |
| 波函数 | `.gbw` | 轨道和密度矩阵 |
| 性质 | `.property.txt` | 结构化关键数据 |
| Hessian | `.hess` | Hessian矩阵数据 |
| 优化轨迹 | `.opt` | 优化步骤几何 |
| 最终几何 | `.xyz` | XYZ格式几何 |
| 能量+梯度 | `.engrad` | 能量和梯度向量 |

## 主输出文件关键段 / Key Output Sections

### 1. 总能量 (FINAL SINGLE POINT ENERGY)
```
-------------------------   --------------------
FINAL SINGLE POINT ENERGY       -75.324154217672
-------------------------   --------------------
```

### 2. SCF收敛
```
               *           SCF CONVERGED AFTER  11 CYCLES          *
```

### 3. 优化收敛
```
               *         GEOMETRY OPTIMIZATION CONVERGED           *
```

### 4. 振动频率
```
VIBRATIONAL FREQUENCIES
   6:    1594.78 cm**-1
```

### 5. 激发态
```
STATE  1:  E=   0.148932 au      4.055 eV    32714.2 cm**-1
```

### 6. 偶极矩
```
Total Dipole Moment:      0.00000      -0.00000       1.49445
Magnitude (Debye):           3.79579
```

## 解析策略 / Parsing Strategies

### 基于关键字的解析

| 目标数据 | 搜索关键字 | 解析方式 |
|----------|-----------|---------|
| 最终能量 | `FINAL SINGLE POINT ENERGY` | 提取后续浮点数 |
| SCF收敛 | `SCF CONVERGED AFTER` | 提取迭代次数 |
| 频率 | `VIBRATIONAL FREQUENCIES` | 逐行读取频率值 |
| 激发态 | `TD-DFT/TDA EXCITATION` | 解析STATE块 |
| 电荷 | `MULLIKEN ATOMIC CHARGES` | 逐行读取电荷值 |

### 使用 property.txt

ORCA自动生成结构化的property.txt文件，包含以`$`标记的关键字-值对：

```
$total_energy
-232.178932

$final_single_point_energy
-232.178932
```

### 使用 orca_2JSON

ORCA内置的JSON转换工具（手册9.3节），生成标准JSON格式输出。

## 外部解析工具 / External Parsing Tools

| 工具 | 语言 | 安装 | 特点 |
|------|------|------|------|
| orca_parser | Python | `pip install orca-parser` | 专用ORCA解析 |
| cclib | Python | `pip install cclib` | 多格式支持 |
| qccodec | Python | `pip install qccodec` | 结构化数据对象 |
| ASE | Python | `pip install ase` | 完整模拟环境 |

## 对LSP的启示 / Implications for LSP

理解输出文件结构有助于：
1. **诊断信息映射**：将ORCA警告和错误映射到LSP诊断
2. **智能提示**：基于常见输出模式提供输入建议
3. **验证反馈**：解析输出以验证输入文件正确性

## 来源列表 / Source List

- `raw/assets/orca-output-format.md`
- ORCA 6.0 Tutorials Input/Output页面
- ORCA 6.1.1 Manual Property File章节
- orca_parser GitHub仓库
