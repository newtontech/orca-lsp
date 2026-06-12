# 密度泛函理论 / Density Functional Theory

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

密度泛函理论（DFT）是一种基于电子密度而非波函数的量子化学方法。Hohenberg-Kohn定理证明，基态电子密度唯一确定体系的所有性质。

## 核心机制 / Core Mechanism

### Kohn-Sham方程 / Kohn-Sham Equations

将相互作用电子系统映射到非相互作用参考系统：

```
[-½∇² + V_eff(r)]ψ_i(r) = ε_iψ_i(r)
```

其中有效势包含：
- 外部势（核-电子吸引）
- Hartree势（电子-电子排斥）
- 交换-相关势（包含多体效应）

### 交换-相关泛函 / Exchange-Correlation Functionals

DFT的核心挑战是近似XC泛函：

1. **LDA**：局域密度近似
2. **GGA**：广义梯度近似（PBE、BP86、BLYP）
3. **Meta-GGA**：包含动能密度（TPSS、M06L、SCAN）
4. **杂化泛函**：混合Hartree-Fock交换（B3LYP、PBE0）
5. **范围分离**：长程/短程分离（ωB97X-D、CAM-B3LYP）
6. **双杂化**：添加MP2型相关（B2PLYP）

## 应用场景 / Applications

- **基态几何优化**：平衡结构和振动频率
- **热力学性质**：反应能、生成焓
- **电子性质**：偶极矩、极化率
- **周期性体系**：固体和表面

## 选择指南 / Selection Guide

| 任务 | 推荐泛函 | 基组 |
|------|----------|------|
| 一般几何优化 | B3LYP | def2-TZVP |
| 反应能 | ωB97X-D | def2-TZVPP |
| 激发态 | CAM-B3LYP | aug-cc-pVTZ |
| 高精度 | DSD-PBEB95 | def2-QZVPP |
| 大分子 | PBE0 | def2-SVP |

## 相关概念 / Related Concepts

- [[Hartree-Fock_Method]]
- [[Exchange_Correlation_Functional]]
- [[Basis_Set_Convergence]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/docs/ARCHITECTURE.md`
