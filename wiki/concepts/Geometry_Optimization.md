# 几何优化 / Geometry Optimization

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

几何优化是通过迭代调整核坐标寻找势能面上极小点（能量最低点）或鞍点（过渡态）的过程。

## 核心机制 / Core Mechanism

### 优化算法 / Optimization Algorithms

1. **Berny算法**：基于梯度和Hessian的准牛顿法
2. **共轭梯度**：无需显式Hessian
3. **阻尼分子动力学**：用于初始粗糙结构

### 收敛判据 / Convergence Criteria

ORCA默认收敛标准：
- **能量变化**：<10⁻⁶ Hartree
- **最大梯度**：<3×10⁻⁴ Hartree/Bohr
- **RMS梯度**：<1×10⁻⁴ Hartree/Bohr
- **最大位移**：<3×10⁻⁴ Bohr
- **RMS位移**：<1×10⁻⁴ Bohr

## 基本优化设置 / Basic Optimization Setup

### 简单优化

```orca
! B3LYP def2-TZVP OPT
%maxcore 4000
%pal nprocs 4 end

* xyz 0 1
  C   0.000000   0.000000   0.000000
  H   1.089000   0.000000   0.000000
  H  -0.544500   0.943180   0.000000
  H  -0.544500  -0.943180   0.000000
*
```

### 带频率的优化

```orca
! B3LYP def2-TZVP OPT FREQ
```

确认优化到真正的极小点（无虚频）。

## 高级设置 / Advanced Settings

### 收敛控制

```orca
%geom
  maxiter 50        # 最大迭代次数
  convergence tight # 收紧收敛标准
end
```

### Hessian控制

```orca
%geom
  Calc_Hess true      # 计算初始Hessian
  Recalc_Hess 5       # 每5步重新计算Hessian
end
```

### 约束优化 / Constrained Optimization

```orca
%geom
  Constraints
    { B 1 2 1.09 }    # 固定键长
    { A 1 2 3 109.5 } # 固定键角
  end
end
```

### 扫描优化 / Scan Optimization

```orca
%geom
  Scan
    B 1 2 0.9 1.5 10   # 扫描键长，10个点
    A 2 1 3 90 120 5   # 扫描键角，5个点
  end
end
```

## 常见问题 / Common Issues

### 优化失败 / Optimization Failure

**症状**：达到最大迭代次数仍未收敛

**解决方案**：
```orca
%geom
  maxiter 100        # 增加最大迭代次数
  Calc_Hess true     # 计算初始Hessian
end
```

### 优化到错误结构 / Wrong Structure

**症状**：优化到非预期的局部极小点

**解决方案**：
- 提供更好的初始猜测
- 使用更严格的收敛标准
- 检查是否有对称性约束

### 振荡 / Oscillation

**症状**：能量和梯度来回振荡

**解决方案**：
```orca
%geom
  Trust radius 0.1   # 减小步长
  Recalc_Hess 3      # 更频繁重新计算Hessian
end
```

## 优化+频率工作流 / Optimization + Frequency Workflow

### 推荐：OPT FREQ

```orca
! B3LYP def2-TZVP OPT FREQ D3BJ
%maxcore 4000
%pal nprocs 4 end

* xyz 0 1
  [初始几何]
*
```

### 分步：先OPT后FREQ

```orca
# 步骤1：优化
! B3LYP def2-TZVP OPT D3BJ
* xyz 0 1
  [初始几何]
*

# 步骤2：频率验证
! B3LYP def2-TZVP FREQ D3BJ
* xyz 0 1
  [优化后的几何]
*
```

## 精度建议 / Accuracy Recommendations

| 任务 | 方法 | 基组 | 备注 |
|------|------|------|------|
| 初步优化 | B3LYP | def2-SVP | 快速探索 |
| 标准优化 | B3LYP | def2-TZVP | 平衡精度/速度 |
| 高精度 | ωB97X-D | def2-TZVPP | 色散重要时 |
| 大体系 | PBE0 | def2-SVP | 成本优先 |

## 相关概念 / Related Concepts

- [[Frequency_Calculation]]
- [[Transition_State_Search]]
- [[Potential_Energy_Surface]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/examples/water.inp`
