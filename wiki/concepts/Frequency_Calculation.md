# 频率计算 / Frequency Calculation

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

频率计算通过计算能量对核坐标的二阶导数（Hessian矩阵）确定分子的振动模式。用于确认极小点/过渡态、计算热力学性质和光谱性质。

## 核心机制 / Core Mechanism

### Hessian矩阵 / Hessian Matrix

```
H_ij = ∂²E/∂x_i∂x_j
```

对角化得到3N-6（或3N-5）个振动频率。

### 解析 vs 数值频率 / Analytical vs Numerical Frequency

| 类型 | 精度 | 速度 | 适用方法 |
|------|------|------|----------|
| 解析频率 | 高 | 快 | DFT、HF |
| 数值频率 | 中 | 慢 | MP2、CCSD |

```orca
# 解析频率（DFT）
! B3LYP def2-TZVP FREQ

# 数值频率（MP2）
! MP2 def2-TZVP NUMFREQ
```

## 应用场景 / Applications

### 1. 确认极小点 / Confirm Minimum

极小点应无虚频（所有频率为实数）：

```
# 正常输出示例
VIBRATIONAL FREQUENCIES
  1     2     3     4     5     6
   52   112   185   247   398   452   # 全部为正
```

### 2. 确认过渡态 / Confirm Transition State

过渡态应有且仅有一个虚频：

```
# 过渡态输出示例
VIBRATIONAL FREQUENCIES
  1     2     3     4     5     6
  -52i  112   185   247   398   452   # 一个虚频
```

### 3. 热力学性质 / Thermodynamic Properties

计算零点能、焓、吉布斯自由能：

```
THERMODYNAMIC PROPERTIES AT 298.15 K
Zero-point energy:        0.012345 Hartree
Thermal correction:       0.014567 Hartree
Enthalpy:                -76.123456 Hartree
Gibbs free energy:       -76.134567 Hartree
```

### 4. 红外光谱 / IR Spectrum

频率和强度可用于模拟红外光谱：

```
IR SPECTRUM
   Frequency (cm⁻¹)   Intensity (km/mol)
       52                1.2
      112               15.3
      185                0.5
```

## 输入设置 / Input Settings

### 基本频率计算

```orca
! B3LYP def2-TZVP FREQ
%maxcore 4000
%pal nprocs 4 end
```

### 温度设置

```orca
%freq
  temp 298.15    # 温度（K）
end
```

### 使用初始Hessian（用于TS）

```orca
%freq
  start Hessian  # 从优化Hessian开始
end
```

## 工作流程 / Workflow

### 标准 OPT → FREQ

```orca
! B3LYP def2-TZVP OPT FREQ
```

先优化几何，再计算频率。

### 独立频率计算

```orca
# 步骤1：优化
! B3LYP def2-TZVP OPT
* xyz 0 1
  ...
*

# 步骤2：频率（使用优化的几何）
! B3LYP def2-TZVP FREQ
* xyz 0 1
  [优化的坐标]
*
```

### 过渡态验证

```orca
# 步骤1：TS优化
! B3LYP def2-TZVP TS
%geom Calc_Hess true end

# 步骤2：频率验证虚频
! B3LYP def2-TZVP FREQ
* xyz 0 1
  [TS坐标]
*

# 步骤3：IRC验证反应路径
! B3LYP def2-TZVP IRC
* xyz 0 1
  [TS坐标]
*
```

## 注意事项 / Caveats

1. **频率单位**：ORCA使用cm⁻¹（波数）
2. **虚频符号**：输出中用"i"标记虚频
3. **缩放因子**：DFT频率通常需要缩放（~0.96-0.98）
4. **低频率模式**：<50 cm⁻¹的频率可能是数值噪声

## 相关概念 / Related Concepts

- [[Geometry_Optimization]]
- [[Transition_State_Search]]
- [[Hessian_Matrix]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/examples/water.inp`
