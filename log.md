# ORCA-LSP 知识库变更日志 / ORCA-LSP Knowledge Base Change Log

> 创建日期：2026-06-12

## 2026-06-12 - 初始创建 / Initial Creation

### 操作 / Operation
初始化ORCA-LSP LLM Wiki知识库

### 创建的文件 / Created Files

#### 原始资料 / Raw Assets
- `raw/assets/README.md` - 项目README副本
- `raw/assets/CHANGELOG.md` - 变更日志副本
- `raw/assets/DEVELOPMENT.md` - 开发文档副本
- `raw/assets/docs/` - 文档目录副本
- `raw/assets/examples/` - 示例文件副本

#### 实体页面 / Entity Pages (wiki/entities/)
1. `ORCA_Quantum_Chemistry.md` - ORCA软件概述
2. `DFT_Functionals.md` - DFT泛函数据库
3. `Basis_Sets.md` - 基组数据库
4. `Wavefunction_Methods.md` - 波函数方法
5. `Job_Types.md` - 作业类型
6. `Percent_Blocks.md` - %参数块
7. `Geometry_Section.md` - 几何结构部分
8. `Auxiliary_Basis_Sets.md` - 辅助基组
9. `Element_Symbols.md` - 元素符号
10. `Language_Server_Protocol.md` - LSP实现
11. `Diagnostic_Engine_v1.md` - 诊断引擎
12. `OpenQC_Alignment.md` - OpenQC对齐

#### 概念页面 / Concept Pages (wiki/concepts/)
1. `Density_Functional_Theory.md` - DFT理论
2. `Coupled_Cluster_Theory.md` - 耦合簇理论
3. `Time_Dependent_DFT.md` - TD-DFT
4. `Transition_State_Search.md` - 过渡态搜索
5. `Solvation_Models.md` - 溶剂化模型
6. `Basis_Set_Selection.md` - 基组选择
7. `DLPNO_Methods.md` - DLPNO方法
8. `Dispersion_Corrections.md` - 色散校正
9. `Frequency_Calculation.md` - 频率计算
10. `Geometry_Optimization.md` - 几何优化

#### 综合页面 / Synthesis Pages (wiki/synthesis/)
1. `ORCA_LSP_API_Reference.md` - API参考
2. `Diagnostics_Catalog.md` - 诊断目录
3. `Input_File_Guide.md` - 输入文件指南

#### 导航文件 / Navigation Files
1. `index.md` - 知识库索引
2. `log.md` - 本文件
3. `docs/LLM-WIKI-PLAN.md` - Wiki结构计划

### 关键发现 / Key Findings

1. **ORCA支持45+ DFT泛函**：包括杂化、GGA、meta-GGA、范围分离、双杂化
2. **38+基组**：涵盖Pople、def2、cc-pVXZ、辅助基组等系列
3. **21+%块**：支持内存、并行、SCF、激发态、溶剂化等设置
4. **100%测试覆盖**：338个测试，全部通过
5. **诊断引擎v1**：标准化诊断格式，支持Agent工作流

### 数据来源 / Data Sources

- `src/orca_lsp/keywords.py` - 关键字数据库
- `src/orca_lsp/parser.py` - 解析器实现
- `src/orca_lsp/validator.py` - 验证器
- `src/orca_lsp/server.py` - LSP服务器
- `src/orca_lsp/rich_diagnostics.py` - 诊断序列化
- `docs/` - 项目文档
- `examples/` - 输入文件示例

### 统计 / Statistics

- **总Wiki文件**：25
- **实体页面**：12
- **概念页面**：10
- **综合页面**：3
- **原始资料**：10+文件

---

## 2026-06-12 - 文档扩展 / Documentation Expansion

### 操作 / Operation
通过网络搜索收集ORCA官方文档，扩展原始资料和wiki知识库。

### 新增原始资料 / New Raw Assets

1. `raw/assets/orca-input-format.md` -- ORCA输入文件格式官方文档（ORCA 6.1.1 Manual Section 2.1）
2. `raw/assets/orca-keywords-reference.md` -- ORCA关键字完整参考（方法、基组、作业类型、SCF控制、色散、RI等）
3. `raw/assets/orca-examples.md` -- 18个ORCA输入文件示例（涵盖DFT、TD-DFT、MP2、DLPNO-CCSD(T)、CPCM、TS等）
4. `raw/assets/orca-output-format.md` -- ORCA输出文件格式参考（主输出、property.txt、解析模式）
5. `raw/assets/orca-compound-jobs.md` -- 复合作业与多步工作流文档（$new_job、Compound模块、OPI）
6. `raw/assets/orca-basis-sets-reference.md` -- ORCA基组完整参考（def2、cc-pVXZ、SARC、ANO、ECP等）
7. `raw/assets/orca-github-tools.md` -- GitHub ORCA工具与解析器（orca_parser、cclib、ASE、OPI等）
8. `raw/assets/orca-tutorials.md` -- ORCA教程与学习资源汇总

### 新增Wiki页面 / New Wiki Pages

#### 实体页面 / Entity Pages (wiki/entities/)
1. `ORCA_Official_Documentation.md` - ORCA官方文档资源汇总（7个核心来源）
2. `ORCA_GitHub_Tools.md` - ORCA相关工具与解析器

#### 概念页面 / Concept Pages (wiki/concepts/)
1. `Compound_Jobs.md` - 复合作业与工作流（4种实现方式、4种常见模式）

#### 综合页面 / Synthesis Pages (wiki/synthesis/)
1. `ORCA_Output_Guide.md` - ORCA输出文件解析指南（6个关键段、3种解析策略）

### 更新的Wiki页面 / Updated Wiki Pages

1. `ORCA_Quantum_Chemistry.md` - 添加新原始资料来源引用
2. `Basis_Sets.md` - 添加基组参考文档来源
3. `Input_File_Guide.md` - 添加5个新原始资料来源

### 关键发现 / Key Findings

1. **ORCA 6.1.1 Manual** 是最全面的文档来源，在线托管于 orca-manual.mpi-muelheim.mpg.de
2. **ORCA 6.0 Tutorials** (FACCTs) 提供面向新用户的教程，覆盖安装到高级计算
3. **ORCA Input Library** 是社区维护的输入示例库，但尚未更新至ORCA 6.0
4. **CompoundScripts** 是ORCA官方GitHub组织的唯一公开仓库
5. **RIJCOSX** 从ORCA 5.0起对杂化泛函默认启用
6. **DefGrid1/2/3** 取代了ORCA 5.0前的GridX关键字
7. **orca_parser** 和 **cclib** 是两个主要的ORCA输出解析Python库

### 数据来源 / Data Sources

- ORCA 6.1.1 Manual (MPI Mulheim): https://orca-manual.mpi-muelheim.mpg.de/
- ORCA 6.0 Tutorials (FACCTs): https://www.faccts.de/docs/orca/6.0/tutorials/
- ORCA Input Library: https://sites.google.com/site/orcainputlibrary/home
- CompoundScripts GitHub: https://github.com/ORCAQuantumChemistry/CompoundScripts
- GitHub Topics orca-quantum-chemistry: https://github.com/topics/orca-quantum-chemistry
- Texas A&M HPRC Tutorial: https://hprc.tamu.edu/training/intro_orca.html

### 统计 / Statistics

- **总Wiki文件**：29（新增4个）
- **实体页面**：14（新增2个）
- **概念页面**：11（新增1个）
- **综合页面**：4（新增1个）
- **原始资料**：18+文件（新增8个）

---

*本文档由LLM自动维护，记录知识库的所有重要变更。*
