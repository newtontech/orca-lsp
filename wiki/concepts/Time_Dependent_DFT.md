# 含时密度泛函理论 / Time-Dependent DFT

> 类型：概念 / Concept
> 学科/领域：量子化学 / Quantum Chemistry

## 定义 / Definition

含时密度泛函理论（TD-DFT）是处理分子激发态和动力学的DFT扩展框架。通过线性响应理论计算激发能和激发态性质。

## 核心机制 / Core Mechanism

### 线性响应TD-DFT

响应方程求解：

```
( A  B )(X) = ω( 1  0 )(X)
( B  A )(Y)      ( 0 -1 )(Y)
```

其中A、B是耦合矩阵，ω是激发能，X、Y是激发向量。

### 激发态数量控制

使用%nroots指定计算的激发态数量：

```orca
%tddft
  nroots 10    # 计算10个最低激发态
  maxdim 100   # 展开空间维度
end
```

## 应用场景 / Applications

- **紫外-可见光谱**：电子跃迁能量和振子强度
- **荧光发射**：S₁ → S₀跃迁
- **电荷转移态**：分子间电子转移
- **激发态优化**：激发态几何结构

## 泛函选择 / Functional Selection

### 标准泛函

- **B3LYP**：适用于价态-价态跃迁
- **PBE0**：类似B3LYP，稍高精度

### 范围分离泛函（推荐用于电荷转移）

- **CAM-B3LYP**：Coulomb衰减B3LYP
- **ωB97X-D**：含色散校正
- **LC-ωPBE**：长程校正PBE

## 基组要求 / Basis Set Requirements

- **价态激发**：def2-TZVP或cc-pVTZ
- **电荷转移**：aug-cc-pVTZ（需要弥散函数）
- **里德堡态**：aug-cc-pVQZ（高精度）

## 输出示例 / Output Example

```
EXCITED STATE PROPERTIES
STATE  1:  E=  4.253 eV  291.5 nm  f=0.125
         Spin:  Singlet A
Dominant transitions:
  38 -> 39 :  0.65 (HOMO -> LUMO)
```

## 相关概念 / Related Concepts

- [[Density_Functional_Theory]]
- [[Charge_Transfer_Excitations]]
- [[Oscillator_Strength]]

## 来源 / Sources

- `src/orca_lsp/keywords.py`
- `raw/assets/examples/td_dft.inp`
