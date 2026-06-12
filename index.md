# ORCA-LSP 知识库索引 / ORCA-LSP Knowledge Base Index

> 最后更新：2026-06-12

欢迎使用ORCA-LSP知识库，这是一个基于Karpathy风格的LLM维护的wiki，专注于ORCA量子化学软件的Language Server Protocol实现。

## 导航结构 / Navigation Structure

### 原始资料 / Raw Sources
- **raw/assets/**: 源文件、文档、示例的原始副本
  - `orca-input-format.md` -- ORCA输入文件格式官方文档
  - `orca-keywords-reference.md` -- ORCA关键字完整参考
  - `orca-examples.md` -- 18个ORCA输入文件示例
  - `orca-output-format.md` -- ORCA输出文件格式参考
  - `orca-compound-jobs.md` -- 复合作业与工作流文档
  - `orca-basis-sets-reference.md` -- ORCA基组完整参考
  - `orca-github-tools.md` -- GitHub ORCA工具与解析器
  - `orca-tutorials.md` -- ORCA教程与学习资源

### 知识库 / Wiki

#### 实体页面 / Entities (wiki/entities/)
ORCA特定的概念、方法和数据结构：

- [[ORCA_Quantum_Chemistry]] - ORCA量子化学软件概述
- [[DFT_Functionals]] - DFT泛函数据库（45+种泛函）
- [[Basis_Sets]] - 基组数据库（38+种基组）
- [[Wavefunction_Methods]] - 波函数方法（HF、MP2、CCSD等）
- [[Job_Types]] - 计算作业类型（SP、OPT、FREQ、TS等）
- [[Percent_Blocks]] - %参数块设置
- [[Geometry_Section]] - 几何结构部分
- [[Auxiliary_Basis_Sets]] - 辅助基组（RI/DF加速）
- [[Element_Symbols]] - 支持的元素符号
- [[Language_Server_Protocol]] - LSP服务器实现
- [[Diagnostic_Engine_v1]] - 诊断引擎v1规范
- [[OpenQC_Alignment]] - OpenQC对齐规范
- [[ORCA_Official_Documentation]] - ORCA官方文档资源汇总
- [[ORCA_GitHub_Tools]] - ORCA相关工具与解析器

#### 概念页面 / Concepts (wiki/concepts/)
跨领域的量子化学概念：

- [[Density_Functional_Theory]] - 密度泛函理论
- [[Coupled_Cluster_Theory]] - 耦合簇理论
- [[Time_Dependent_DFT]] - 含时密度泛函理论（TD-DFT）
- [[Transition_State_Search]] - 过渡态搜索
- [[Solvation_Models]] - 溶剂化模型（CPCM）
- [[Basis_Set_Selection]] - 基组选择策略
- [[DLPNO_Methods]] - DLPNO近似耦合簇
- [[Dispersion_Corrections]] - 色散校正（D3/D3BJ/D4）
- [[Frequency_Calculation]] - 频率计算
- [[Geometry_Optimization]] - 几何优化
- [[Compound_Jobs]] - 复合作业与工作流

#### 综合页面 / Synthesis (wiki/synthesis/)
API参考、诊断目录、使用指南：

- [[ORCA_LSP_API_Reference]] - ORCA-LSP API参考
- [[Diagnostics_Catalog]] - 诊断目录
- [[Input_File_Guide]] - 输入文件指南
- [[ORCA_Output_Guide]] - ORCA输出文件解析指南

## 快速开始 / Quick Start

1. **新手入门**：从 [[ORCA_Quantum_Chemistry]] 开始了解ORCA
2. **学习语法**：阅读 [[Input_File_Guide]] 掌握输入文件格式
3. **选择方法**：参考 [[DFT_Functionals]] 和 [[Basis_Set_Selection]]
4. **设置计算**：查看 [[Job_Types]] 和 [[Percent_Blocks]]
5. **理解诊断**：浏览 [[Diagnostics_Catalog]] 了解错误处理
6. **多步工作流**：参考 [[Compound_Jobs]] 了解复合作业
7. **解析输出**：查看 [[ORCA_Output_Guide]] 了解输出文件

## 统计信息 / Statistics

- **实体页面**：14
- **概念页面**：11
- **综合页面**：4
- **总Wiki文件**：29
- **原始资料文件**：18+

## 搜索建议 / Search Tips

- 查找特定泛函：搜索"B3LYP"、"PBE0"等
- 查找基组：搜索"def2-"、"cc-pVXZ"等
- 查找计算类型：搜索"OPT"、"FREQ"、"TS"等
- 查找%块：搜索"%maxcore"、"%tddft"等
- 查找输出格式：搜索"FINAL SINGLE POINT ENERGY"等

## 更新日志 / Change Log

参见 [[log.md]] 了解知识库的详细变更历史。

## 外部链接 / External Links

- ORCA 6.1.1 Manual: https://orca-manual.mpi-muelheim.mpg.de/
- ORCA 6.0 Tutorials: https://www.faccts.de/docs/orca/6.0/tutorials/
- ORCA Input Library: https://sites.google.com/site/orcainputlibrary/home
- CompoundScripts: https://github.com/ORCAQuantumChemistry/CompoundScripts
- ORCA-LSP GitHub: https://github.com/newtontech/orca-lsp
- OpenQC-VSCode: https://github.com/newtontech/OpenQC-VSCode

---

*本知识库由LLM维护，遵循Karpathy风格的Wiki模式：原始证据与衍生wiki页面分离，每个持久性声明都可追溯到来源。*
