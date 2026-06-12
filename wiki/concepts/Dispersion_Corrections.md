# 色散校正 / Dispersion Corrections

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

色散校正（ dispersion correction）是DFT泛函的补充项，用于描述标准DFT无法正确处理的伦敦色散力（瞬时偶极-偶极相互作用）。

## 问题背景 / Problem Background

标准DFT泛函（即使是杂化泛函）对色散力的描述很差：

- **低估**：非共价相互作用能量
- **失效**：π-π堆积、氢键、疏水效应
- **原因**：DFT是定域/半定域理论，色散是长程相关效应

## 色散校正方法 / Dispersion Correction Methods

### D3校正 / D3 Correction (Grimme)

最广泛使用的色散校正：

```orca
! B3LYP def2-TZVP D3
%method D3 end
```

### D3BJ校正 / D3BJ Correction (Becke-Johnson)

改进的D3阻尼函数：

```orca
! B3LYP def2-TZVP D3BJ
%method D3BJ end
```

### D4校正 / D4 Correction

最新一代色散校正：

```orca
! B3LYP def2-TZVP D4
```

### 内置色散泛函 / Built-in Dispersion Functionals

某些泛函已包含色散校正：

- **ωB97X-D**：包含D3校正
- **ωB97X-D3**、**ωB97X-D4**：指定D3/D4版本
- **B97-D**、**B97-D3**：包含色散的泛函

## 适用场景 / Applications

### 非共价相互作用 / Non-Covalent Interactions

- **氢键**：O-H···O、N-H···O等
- **π-π堆积**：芳香环叠加
- **疏水效应**：疏水分子聚集
- **卤键**：X···Y相互作用

### 主客体化学 / Host-Guest Chemistry

- 包合物、冠醚、环糊精
- 分子识别

### 团簇 / Clusters

- 分子团簇
- 纳米团簇

## 性能比较 / Performance Comparison

| 泛函+校正 | S22×5 (kcal/mol) | 平均误差 |
|----------|------------------|----------|
| B3LYP | -3.70 | 严重低估 |
| B3LYP-D3 | +0.20 | 良好 |
| B3LYP-D3BJ | +0.10 | 优秀 |
| ωB97X-D | +0.15 | 优秀 |

## 使用建议 / Usage Recommendations

### 默认选择

对于大多数涉及非共价相互作用的体系：

```orca
! B3LYP def2-TZVP D3BJ
```

### 高精度需求

```orca
! ωB97X-D4 def2-TZVPP D4
```

### 大体系

```orca
! PBE0 def2-SVP D3BJ
```

## 注意事项 / Caveats

1. **不适用**：共价键能量色散校正已包含在泛函中
2. **双重计数**：某些泛函（如ωB97X-D）不需要额外D3
3. **短程阻尼**：D3BJ比D3更好处理短程
4. **金属有机**：可能需要特殊处理

## 相关概念 / Related Concepts

- [[Density_Functional_Theory]]
- [[Non-Covalent_Interactions]]
- [[Basis_Sets]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/docs/ARCHITECTURE.md`
