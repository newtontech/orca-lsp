# 耦合簇理论 / Coupled Cluster Theory

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

耦合簇（CC）理论是一种高精度的电子相关方法，通过指数参数化波函数包含电子激发：

```
|Ψ⟩ = e^(T̂)|Φ₀⟩
```

其中T̂ = T₁ + T₂ + T₃ + ... 包含单、双、三重等激发算符。

## 核心机制 / Core Mechanism

### CCSD：耦合簇单双激发

考虑所有单重和双重激发：

- **精度**：通常能达到化学精度（~1 kcal/mol）
- **标度**：O(N⁶）
- **适用**：中小分子（<50原子）

### CCSD(T)：CCSD加微扰三重激发

"金标准"方法，添加三重激发的微扰校正：

- **精度**：接近全CI极限
- **标度**：O(N⁷）
- **适用**：小分子高精度计算

### DLPNO近似：域基局域对自然轨道

大幅降低计算成本的近似方法：

- **DLPNO-CCSD(T)**：适用于中等大小分子（~100原子）
- **精度损失**：通常<1 kcal/mol
- **加速比**：10-100倍

## 应用场景 / Applications

- **高精度单点能**：在DFT优化几何上计算
- **反应能垒**：精确计算过渡态能量
- **非共价相互作用**：氢键、π-π堆积
- **基准数据**：验证DFT泛函性能

## 实践建议 / Practical Recommendations

1. **几何优化**：用DFT（B3LYP/def2-TZVP）
2. **单点能**：用DLPNO-CCSD(T)/def2-TZVPP
3. **基准计算**：用CCSD(T)/def2-QZVPP（小分子）
4. **辅助基组**：配合def2-TZVPP/C加速

## 相关概念 / Related Concepts

- [[Perturbation_Theory]]
- [[Basis_Set_Extrapolation]]
- [[Accuracy_vs_Cost]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/examples/benzene.inp`
