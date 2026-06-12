# 复合作业与工作流 / Compound Jobs and Workflows

> 类型：概念 / Concept
> 创建日期：2026-06-12
> 来源数：3

## 核心概念 / Core Concept

ORCA支持在单个输入文件中执行多步计算（复合作业），允许串联不同方法和基组的计算步骤。这是实现高效量子化学工作流的关键特性。

## 实现方式 / Implementation Methods

### 1. 组合关键字（推荐用于简单场景）

最简单的方式是在`!`行中组合多个作业类型：

```orca
! B3LYP def2-TZVP OPT FREQ D3BJ
```

这会先优化几何，再计算频率。

### 2. $new_job 分隔符（已弃用但仍可用）

用`$new_job`分隔多个独立计算步骤：

```orca
# 步骤1：廉价优化
! B3LYP def2-SVP OPT TightSCF
* xyz 0 1
  O 0 0 0
  H 0 0 1
  H 0 1 0
*

$new_job

# 步骤2：高精度单点
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C TightSCF
```

**注意**：`$new_job`已弃用，ORCA推荐使用Compound模块。

### 3. Compound 模块（推荐用于复杂场景）

ORCA 6.x引入的Compound模块提供Python风格的脚本化工作流：

- 支持变量传递和条件逻辑
- 官方脚本库: https://github.com/ORCAQuantumChemistry/CompoundScripts
- 详见ORCA手册8.2-8.4节

### 4. ORCA Python Interface (OPI)

ORCA 6.1+提供的完整Python接口：

```python
# OPI工作流伪代码
result = run_dft_optimization(geometry)
sp_energy = run_dlpno_ccsdt(result.geometry)
```

## 常见工作流模式 / Common Workflow Patterns

### 模式1：廉价优化 + 高精度单点

| 步骤 | 方法 | 基组 | 目的 |
|------|------|------|------|
| 1 | B3LYP | def2-SVP | 几何优化 |
| 2 | DLPNO-CCSD(T) | def2-TZVPP/C | 高精度能量 |

### 模式2：优化 + 频率 + 激发态

| 步骤 | 方法 | 基组 | 目的 |
|------|------|------|------|
| 1 | B3LYP | def2-TZVP | OPT FREQ |
| 2 | CAM-B3LYP | def2-TZVP | TD-DFT |

### 模式3：CBS外推

| 步骤 | 基组 | 目的 |
|------|------|------|
| 1 | def2-TZVPP/C | TZ能量 |
| 2 | def2-QZVPP/C | QZ能量 |
| 3 | 外推公式 | CBS能量 |

### 模式4：溶剂化 + 构象搜索

| 步骤 | 方法 | 目的 |
|------|------|------|
| 1 | GOAT | 全局构象搜索 |
| 2 | B3LYP/def2-TZVP + CPCM | 精确优化 |

## $new_job 行为细节 / $new_job Behavior

- 前一步的所有计算标志传递到下一步
- 只需指定需要更改的设置
- 默认使用上一步的轨道作为初始猜测
- 如果不需要继承轨道，需显式指定Guess
- RI近似等设置也会继承（如不需要需手动关闭）

## 相关来源 / Related Sources

- `raw/assets/orca-compound-jobs.md`
- ORCA 6.1.1 Manual 8.2-8.4节
- CompoundScripts GitHub仓库

## 相关实体/概念 / Related Entities/Concepts

- [[Job_Types]]
- [[Percent_Blocks]]
- [[Geometry_Optimization]]
- [[Frequency_Calculation]]
