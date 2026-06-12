# 语言服务器协议 / Language Server Protocol

> 类型：协议 / Protocol
> 创建日期：2026-06-12
> 来源数：1

## 简介 / Introduction

语言服务器协议（LSP）是编辑器和语言工具之间的标准化通信协议。`orca-lsp`为ORCA输入文件提供完整的LSP支持。

## LSP核心功能 / Core LSP Features

### 自动完成 / Completion

根据上下文提供智能补全：

- **简单输入行（!）后**：方法、基组、作业类型
- **%块后**：块名称和参数
- **几何部分中**：元素符号

### 悬停文档 / Hover Documentation

鼠标悬停显示关键字文档：

- 方法描述和参考文献
- 基组信息
- 作业类型解释
- %块参数文档

### 诊断 / Diagnostics

实时错误和警告检测：

- 未知关键字
- 无效参数
- 缺失必需部分
- 内存和并行化警告

### 代码操作 / Code Actions

常见错误的快速修复：

- 添加缺失的%maxcore块
- 添加缺失的%pal nprocs设置
- 修复常见关键字拼写错误

## 服务器架构 / Server Architecture

```python
src/orca_lsp/
├── server.py          # LSP服务器实现
├── parser.py          # ORCA输入文件解析器
├── keywords.py        # 关键字数据库
├── validator.py       # 输入验证器
├── rich_diagnostics.py # 诊断序列化
├── agent_lsp.py       # 代理API
└── tool.py            # CLI工具入口
```

## 编辑器集成 / Editor Integration

### VS Code

```json
{
  "lsp.languageServers": {
    "orca-lsp": {
      "command": ["orca-lsp"],
      "selector": { "language": "orca", "pattern": "**/*.inp" }
    }
  }
}
```

### Neovim

```lua
lspconfig.orca_lsp.setup {
  cmd = {"orca-lsp"},
  filetypes = {"orca"},
}
```

### Emacs

```elisp
(lsp-register-client
 (make-lsp-client :new-connection (lsp-stdio-connection "orca-lsp")
                 :major-modes '(orca-mode)
                 :server-id 'orca-lsp))
```

## Agent CLI / Agent命令行接口

```bash
orca-lsp-tool check path/to/input --format json
orca-lsp-tool context path/to/input --format json
orca-lsp-tool complete path/to/input --format json
orca-lsp-tool hover path/to/input --format json
orca-lsp-tool symbols path/to/input --format json
orca-lsp-tool fix path/to/input --format json
```

## 相关来源 / Related Sources

- `raw/assets/docs/ARCHITECTURE.md`
- `raw/assets/docs/USER_GUIDE.md`
- `src/orca_lsp/server.py`

## 相关实体/概念 / Related Entities/Concepts

- [[ORCA_Quantum_Chemistry]]
- [[Diagnostic_Engine_v1]]
- [[OpenQC_Alignment]]
