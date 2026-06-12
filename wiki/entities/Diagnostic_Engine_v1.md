# 诊断引擎v1 / Diagnostic Engine v1

> 类型：框架 / Framework
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

诊断引擎v1是newtontech科学LSP系列共享的诊断规范，受python-lsp-server提供者模型启发。它将编辑器面向的LSP功能与代理面向的JSON API分离。

## 核心设计 / Core Design

### 编辑器 vs 代理分离 / Editor vs Agent Separation

- **编辑器层**：标准LSP协议（completion、hover、diagnostics）
- **代理层**：确定性JSON输出（check/repair/recheck循环）

### 严重级别策略 / Severity Policy

| 级别 | 用途 | 阻塞 |
|------|------|------|
| error | 高置信度语法/架构问题 | 是 |
| warning | 高风险但可能有意的输入 | 否 |
| information | 信息性提示 | 否 |
| hint | 可选优化建议 | 否 |

### 诊断类别 / Diagnostic Categories

1. **syntax**：语法错误
2. **schema**：架构验证
3. **type/value**：类型/值错误
4. **cross-file reference**：跨文件引用
5. **semantic consistency**：语义一致性
6. **preflight/runtime-risk**：运行前风险
7. **style/deprecation**：风格/废弃

## 富诊断形状 / Rich Diagnostic Shape

```json
{
  "code": "STABLE_CODE",
  "severity": "error",
  "category": "schema",
  "confidence": 1.0,
  "source": "orca-lsp",
  "range": {
    "start": {"line": 0, "character": 0},
    "end": {"line": 0, "character": 1}
  },
  "software": "orca",
  "file_type": "input",
  "path": "input",
  "expected": null,
  "actual": null,
  "manual_ref": null,
  "fix_hints": [],
  "blocking": true
}
```

## Agent CLI工具 / Agent CLI Tool

### check命令

检查输入文件并返回JSON格式诊断：

```bash
orca-lsp-tool check path/to/input --format json
```

### context命令

获取文件上下文信息：

```bash
orca-lsp-tool context path/to/input --format json
```

### complete命令

获取补全建议：

```bash
orca-lsp-tool complete path/to/input --format json
```

### hover命令

获取悬停文档：

```bash
orca-lsp-tool hover path/to/input --format json
```

### symbols命令

获取文档符号：

```bash
orca-lsp-tool symbols path/to/input --format json
```

### fix命令

获取快速修复：

```bash
orca-lsp-tool fix path/to/input --format json
```

## ORCA-LSP实现 / ORCA-LSP Implementation

### 模块结构

- `rich_diagnostics.py`：诊断序列化辅助函数
- `validator.py`：输入验证器
- `agent_lsp.py`：代理API提供者
- `tool.py`：CLI工具入口

### 诊断示例 / Diagnostic Examples

#### 缺失简单输入行

```json
{
  "code": "MISSING_SIMPLE_INPUT",
  "severity": "error",
  "category": "schema",
  "message": "Missing simple input line (!) with method and basis set"
}
```

#### 缺失方法

```json
{
  "code": "NO_METHOD_SPECIFIED",
  "severity": "error",
  "category": "schema",
  "message": "No method specified in simple input"
}
```

#### 缺失%maxcore

```json
{
  "code": "MISSING_MAXCORE",
  "severity": "warning",
  "category": "preflight/runtime-risk",
  "message": "Missing %maxcore setting"
}
```

## 相关来源 / Related Sources

- `raw/assets/docs/DIAGNOSTIC_ENGINE_V1.md`
- `src/orca_lsp/rich_diagnostics.py`

## 相关实体/概念 / Related Entities/Concepts

- [[Language_Server_Protocol]]
- [[ORCA_Quantum_Chemistry]]
- [[Diagnostics_Catalog]]
