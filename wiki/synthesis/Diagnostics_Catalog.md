# 诊断目录 / Diagnostics Catalog

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：3

## 核心论点 / Core Argument

ORCA-LSP提供全面的诊断能力，检测从缺失必需部分到方法组合冲突的各种问题。诊断按严重级别分类，支持自动化修复工作流。

## 诊断分类 / Diagnostic Categories

### Syntax Errors / 语法错误

#### 缺失简单输入行 / Missing Simple Input Line

```json
{
  "code": "MISSING_SIMPLE_INPUT",
  "severity": "error",
  "message": "Missing simple input line (!) with method and basis set",
  "category": "schema"
}
```

**解决方案**：添加`!`行并指定方法和基组。

### Schema Errors / 架构错误

#### 缺失方法 / Missing Method

```json
{
  "code": "NO_METHOD_SPECIFIED",
  "severity": "error",
  "message": "No method specified in simple input (e.g., B3LYP, HF, MP2)",
  "category": "schema"
}
```

**解决方案**：在`!`行添加方法（如`B3LYP`）。

#### 缺失基组 / Missing Basis Set

```json
{
  "code": "NO_BASIS_SET_SPECIFIED",
  "severity": "error",
  "message": "No basis set specified in simple input (e.g., def2-TZVP, 6-31G*)",
  "category": "schema"
}
```

**解决方案**：在`!`行添加基组（如`def2-TZVP`）。

#### 缺失几何部分 / Missing Geometry Section

```json
{
  "code": "MISSING_GEOMETRY",
  "severity": "error",
  "message": "Missing geometry section (* xyz charge multiplicity ...)",
  "category": "schema"
}
```

**解决方案**：添加`* xyz ... *`部分并指定分子几何。

### Type/Value Errors / 类型/值错误

#### 无效元素符号 / Invalid Element Symbol

```json
{
  "code": "INVALID_ELEMENT",
  "severity": "error",
  "message": "Invalid element symbol: Xx",
  "category": "type/value"
}
```

**解决方案**：使用有效的元素符号（H、C、N、O等）。

### Semantic Consistency / 语义一致性

#### 互斥SCF类型 / Mutually Exclusive SCF Types

```json
{
  "code": "CONFLICTING_SCF_TYPES",
  "severity": "error",
  "message": "Mutually exclusive SCF types: RHF UHF",
  "category": "semantic consistency"
}
```

**解决方案**：只使用一种SCF类型（RHF、UHF或ROHF）。

#### DFT与MP2混合 / DFT with MP2

```json
{
  "code": "DFT_MP2_COMBINATION",
  "severity": "warning",
  "message": "DFT combined with MP2 is not standard. Consider double-hybrid functionals",
  "category": "semantic consistency"
}
```

**建议**：使用双杂化泛函（如B2PLYP）替代。

### Preflight/Runtime Risk / 运行前风险

#### 缺失%maxcore / Missing %maxcore

```json
{
  "code": "MISSING_MAXCORE",
  "severity": "warning",
  "message": "Missing %maxcore setting. Recommended: %maxcore 2000-4000 (MB per core)",
  "category": "preflight/runtime-risk"
}
```

**解决方案**：添加`%maxcore 4000`块。

#### 基组兼容性 / Basis Set Compatibility

```json
{
  "code": "BASIS_SET_MISMATCH",
  "severity": "warning",
  "message": "Basis set may not be compatible with method",
  "category": "preflight/runtime-risk"
}
```

**建议**：检查基组是否适合所选方法。

## 严重级别策略 / Severity Policy

### Error（错误）

- 高置信度的语法、架构、类型/值或引用问题
- 应阻止自动化提交，因为运行时会拒绝

### Warning（警告）

- 高风险或可疑输入
- 可能是有意的，不应阻止修复循环

### Information（信息）

- 风格或文档性事实

### Hint（提示）

- 可选优化建议

## 快速修复 / Quick Fixes

### 添加%maxcore块

```python
{
  "title": "Add %maxcore block",
  "kind": "quickfix",
  "edit": {
    "newText": "%maxcore 4000\n",
    "range": {"start": {"line": 1, "character": 0}}
  }
}
```

### 添加%pal nprocs块

```python
{
  "title": "Add %pal nprocs block",
  "kind": "quickfix",
  "edit": {
    "newText": "%pal nprocs 4 end\n",
    "range": {"start": {"line": 2, "character": 0}}
  }
}
```

## 来源列表 / Source List

- `src/orca_lsp/validator.py`
- `src/orca_lsp/rich_diagnostics.py`
- `raw/assets/docs/DIAGNOSTIC_ENGINE_V1.md`
