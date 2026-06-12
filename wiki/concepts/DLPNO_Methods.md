# DLPNO方法 / DLPNO Methods

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

域基局域对自然轨道（DLPNO）方法是一类近似耦合簇技术，通过局域化轨道大幅降低计算成本，同时保持接近 canonical CCSD(T) 的精度。

## 核心机制 / Core Mechanism

### 局域化策略 / Localization Strategy

1. **轨道局域化**：将占据轨道变换到局域化基（Pipek-Mezey或Boys）
2. **对的截断**：基于轨道距离和占据数筛选电子对
3. **阈值控制**：通过TCutPNO和TCutPairs控制精度

### PNO截断 / PNO Truncation

```orca
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C
%dlpno
  TCutPNO 1.0E-7    # PNO占据数阈值
  TCutPairs 1.0E-5  # 对筛选阈值
end
```

## DLPNO方法系列 / DLPNO Method Series

### DLPNO-CCSD

局域化耦合簇单双激发：
- **精度**：~0.5 kcal/mol
- **标度**：接近O(N⁴）
- **适用**：中等大小分子（~100原子）

### DLPNO-CCSD(T)

DLPNO-CCSD加微扰三重激发：
- **精度**：~1 kcal/mol（"化学精度"）
- **标度**：O(N⁴)-O(N⁵）
- **适用**：大分子高精度计算

### 其他DLPNO方法

- **DLPNO-MP2**：局域化MP2
- **DLPNO-CEPA**：局域化CEPA方法
- **DLPNO-CCSDT**：包含三重激发（非常昂贵）

## 精度与成本 / Accuracy vs Cost

| 方法 | 分子大小 | 基组 | 时间 | 精度 |
|------|----------|------|------|------|
| CCSD(T) | <20原子 | def2-QZVPP | 小时 | 基准 |
| DLPNO-CCSD(T) | ~100原子 | def2-TZVPP | 小时 | ~1 kcal/mol |
| DLPNO-CCSD(T) | ~200原子 | def2-TZVP | 分钟-小时 | ~2 kcal/mol |

## 使用建议 / Usage Recommendations

### 1. 辅助基组

DLPNO方法强烈推荐使用辅助基组：

```orca
! DLPNO-CCSD(T) def2-TZVPP def2-TZVPP/C
```

### 2. 内存设置

DLPNO需要较大内存：

```orca
%maxcore 4000    # 4 GB per core
%pal nprocs 8 end
```

### 3. 阈值调整

默认阈值通常足够。对更高精度：

```orca
%dlpno
  TCutPNO 1.0E-8    # 更严格
  TCutPairs 1.0E-6  # 更多对
end
```

## 典型工作流 / Typical Workflow

1. **几何优化**：DFT（B3LYP/def2-TZVP）
2. **预筛选**：检查哪些结构需要高精度
3. **DLPNO-CCSD(T)**：在优化几何上计算单点能
4. **验证**：对小分子比较canonical CCSD(T)

## 局限性 / Limitations

- **多参考体系**：强相关电子系统可能失效
- **金属有机**：d电子局域化可能不够
- **电荷转移**：长程相互作用可能被低估

## 相关概念 / Related Concepts

- [[Coupled_Cluster_Theory]]
- [[Basis_Sets]]
- [[Auxiliary_Basis_Sets]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/examples/benzene.inp`
