# ORCA-LSP LLM Wiki 结构计划 / ORCA-LSP LLM Wiki Structure Plan

> 创建日期：2026-06-12
> 目标：为ORCA量子化学LSP项目创建Karpathy风格的LLM Wiki

## Wiki结构设计 / Wiki Structure Design

```
orca-lsp/
├── raw/                    # 原始证据（只读）
│   └── assets/             # 源文件副本
│       ├── README.md
│       ├── CHANGELOG.md
│       ├── DEVELOPMENT.md
│       ├── docs/
│       └── examples/
│
├── wiki/                   # LLM维护的合成内容
│   ├── entities/           # ORCA特定实体
│   │   ├── ORCA_Quantum_Chemistry.md
│   │   ├── DFT_Functionals.md
│   │   ├── Basis_Sets.md
│   │   ├── Wavefunction_Methods.md
│   │   ├── Job_Types.md
│   │   ├── Percent_Blocks.md
│   │   ├── Geometry_Section.md
│   │   ├── Auxiliary_Basis_Sets.md
│   │   ├── Element_Symbols.md
│   │   ├── Language_Server_Protocol.md
│   │   ├── Diagnostic_Engine_v1.md
│   │   └── OpenQC_Alignment.md
│   │
│   ├── concepts/           # 跨领域概念
│   │   ├── Density_Functional_Theory.md
│   │   ├── Coupled_Cluster_Theory.md
│   │   ├── Time_Dependent_DFT.md
│   │   ├── Transition_State_Search.md
│   │   ├── Solvation_Models.md
│   │   ├── Basis_Set_Selection.md
│   │   ├── DLPNO_Methods.md
│   │   ├── Dispersion_Corrections.md
│   │   ├── Frequency_Calculation.md
│   │   └── Geometry_Optimization.md
│   │
│   └── synthesis/         # 综合参考
│       ├── ORCA_LSP_API_Reference.md
│       ├── Diagnostics_Catalog.md
│       └── Input_File_Guide.md
│
├── index.md               # 导航中心
└── log.md                 # 变更日志
```

## 内容规划 / Content Planning

### 实体页面（12个） / Entity Pages

| 页面 | 描述 | 数据来源 |
|------|------|----------|
| ORCA_Quantum_Chemistry | ORCA软件概述 | README, docs |
| DFT_Functionals | 45+ DFT泛函 | keywords.py |
| Basis_Sets | 38+ 基组 | keywords.py |
| Wavefunction_Methods | 波函数方法 | keywords.py |
| Job_Types | 计算类型 | keywords.py |
| Percent_Blocks | %参数块 | keywords.py |
| Geometry_Section | 几何部分 | parser.py |
| Auxiliary_Basis_Sets | 辅助基组 | keywords.py |
| Element_Symbols | 元素符号 | keywords.py |
| Language_Server_Protocol | LSP实现 | server.py, docs |
| Diagnostic_Engine_v1 | 诊断引擎 | rich_diagnostics.py, docs |
| OpenQC_Alignment | OpenQC对齐 | docs |

### 概念页面（10个） / Concept Pages

| 页面 | 描述 | 跨学科关联 |
|------|------|-----------|
| Density_Functional_Theory | DFT理论 | 量子化学 |
| Coupled_Cluster_Theory | 耦合簇理论 | 量子化学 |
| Time_Dependent_DFT | TD-DFT | 光谱学 |
| Transition_State_Search | 过渡态搜索 | 反应动力学 |
| Solvation_Models | 溶剂化模型 | 溶液化学 |
| Basis_Set_Selection | 基组选择 | 计算策略 |
| DLPNO_Methods | DLPNO方法 | 高精度计算 |
| Dispersion_Corrections | 色散校正 | 非共价相互作用 |
| Frequency_Calculation | 频率计算 | 光谱/热力学 |
| Geometry_Optimization | 几何优化 | 势能面 |

### 综合页面（3个） / Synthesis Pages

| 页面 | 描述 | 用途 |
|------|------|------|
| ORCA_LSP_API_Reference | API参考 | 开发者 |
| Diagnostics_Catalog | 诊断目录 | 调试 |
| Input_File_Guide | 输入文件指南 | 用户 |

## 双语格式规范 / Bilingual Format Convention

- **标题**：中文（主要）/ English（次要）
- **内容**：中文为主，保留专业术语原文
- **代码**：保持英文（ORCA输入、Python等）

## 引用规范 / Citation Convention

每个wiki页面必须包含：
- **相关来源**：指向`raw/assets/`的具体文件
- **相关实体/概念**：使用`[[WikiLink]]`格式
- **不确定性标记**：明确区分事实与推断

## 更新策略 / Update Strategy

1. **原始资料变更**：更新`raw/assets/`，重新生成相关页面
2. **版本发布**：在`log.md`记录所有变更
3. **依赖追踪**：使用`[[WikiLink]]`追踪概念依赖
4. **孤儿检测**：定期检查无入链的页面

## 质量标准 / Quality Standards

- 每个实体页面至少1个相关来源
- 每个概念页面至少1个跨领域关联
- 所有专业术语保留英文原文
- 代码示例可直接运行

## 执行计划 / Execution Plan

1. ✅ 创建目录结构
2. ✅ 复制原始资料到`raw/assets/`
3. ✅ 创建实体页面（12个）
4. ✅ 创建概念页面（10个）
5. ✅ 创建综合页面（3个）
6. ✅ 创建导航文件（index.md, log.md）
7. ✅ Git提交和PR创建

## 预期成果 / Expected Outcomes

- **25个wiki文件**：12实体 + 10概念 + 3综合
- **完整的知识图谱**：覆盖ORCA-LSP的所有核心概念
- **可追溯的引用**：每个声明都有来源支持
- **中英双语**：支持中文读者，保留专业术语

---

*本计划遵循Karpathy LLM Wiki模式：原始证据分离、LLM维护合成内容、可追溯引用。*
