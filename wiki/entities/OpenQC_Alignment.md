# OpenQC对齐 / OpenQC Alignment

> 类型：规范 / Specification
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

OpenQC是newtontech的计算化学LSP系列，包括VSCode扩展和语言服务器。`orca-lsp`作为独立语言服务器，需要与OpenQC-VSCode扩展保持对齐。

## 对齐范围 / Alignment Scope

### 必须保持对齐 / Must Keep Aligned

1. **文件扩展名和语言ID**：`.inp`文件的识别
2. **诊断**：无效关键字、%块、内存和并行化设置
3. **补全词汇**：方法、基组、作业类型、常用%块
4. **解析器固件**：用于烟雾测试的最小解析器

### 发布前检查 / Pre-Release Check

在OpenQC公开发布前，进行烟雾测试：

1. 对`orca-lsp`和一个有效ORCA输入运行检查
2. 对一个无效ORCA输入运行检查
3. 验证服务器和扩展的行为一致

## 变更流程 / Change Process

### 修改诊断时

1. 更新`orca-lsp`中的诊断逻辑
2. 在OpenQC-VSCode中创建对齐issue
3. 同步扩展的行为

### 添加新关键字时

1. 更新`keywords.py`中的数据库
2. 更新扩展的补全提供者
3. 测试新关键字在两边的补全行为

## 当前状态 / Current Status

### 支持的功能 / Supported Features

- **语法高亮**：完整的ORCA输入文件语法
- **自动补全**：方法、基组、作业类型、%块
- **诊断**：
  - 无效关键字检测
  - 参数验证
  - 缺失必需部分
  - 内存和并行化警告
- **悬停文档**：关键字的上下文文档
- **快速修复**：常见错误的自动建议

## 示例工作流 / Example Workflow

### 添加新的%块支持

1. **服务器端**（`orca-lsp`）：
   ```python
   # keywords.py
   PERCENT_BLOCKS = {
       ...
       "newblock": {
           "description": "New block description",
           "example": "%newblock param value end"
       }
   }
   ```

2. **扩展端**（OpenQC-VSCode）：
   - 创建对齐issue
   - 更新补全提供者
   - 更新悬停文档
   - 测试新%块

3. **验证**：
   - 运行烟雾测试
   - 检查诊断一致性
   - 验证补全行为

## 相关来源 / Related Sources

- `raw/assets/docs/OPENQC_ALIGNMENT.md`
- `raw/assets/README.md`

## 相关实体/概念 / Related Entities/Concepts

- [[Language_Server_Protocol]]
- [[Diagnostics_Catalog]]
- [[ORCA_Quantum_Chemistry]]
