# ORCA-LSP API参考 / ORCA-LSP API Reference

> 创建日期：2026-06-12
> 最后更新：2026-06-12
> 覆盖来源：5

## 核心论点 / Core Argument

ORCA-LSP提供完整的LSP功能，包括解析、验证、补全、悬停和诊断。服务器通过stdin/stdout与编辑器通信，支持Agent CLI工具接口。

## 模块架构 / Module Architecture

```python
src/orca_lsp/
├── __init__.py          # 包初始化
├── parser.py            # ORCAParser类
├── keywords.py          # 关键字数据库
├── validator.py         # ORCAValidator类
├── server.py            # OrcaLanguageServer类
├── rich_diagnostics.py  # 诊断序列化
├── agent_lsp.py         # Agent API提供者
├── tool.py              # CLI入口
└── features/            # 功能模块
    ├── __init__.py
    ├── code_actions.py  # 快速修复
    ├── diagnostic.py    # 诊断提供者
    ├── agent_api.py     # Agent API
    └── ...
```

## 数据结构 / Data Structures

### ParseResult

```python
@dataclass
class ParseResult:
    simple_input: Optional[SimpleInput]
    percent_blocks: List[PercentBlock]
    geometry: Optional[Geometry]
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
```

### SimpleInput

```python
@dataclass
class SimpleInput:
    methods: List[str]
    basis_sets: List[str]
    job_types: List[str]
    other_keywords: List[str]
    raw: str
    line_number: int
```

### PercentBlock

```python
@dataclass
class PercentBlock:
    name: str
    parameters: Dict[str, Any]
    raw_content: str
    line_start: int
    line_end: int
```

### Geometry

```python
@dataclass
class Geometry:
    charge: int
    multiplicity: int
    atoms: List[Atom]
    format_type: str  # xyz, int
    line_start: int
    line_end: int
```

## 关键字数据库 / Keywords Database

### DFT_FUNCTIONALS

45+种DFT泛函，包括：
- 杂化泛函（B3LYP、PBE0、M06-2X）
- GGA泛函（PBE、BP86、BLYP）
- Meta-GGA泛函（TPSS、M06L、SCAN）
- 范围分离泛函（ωB97X-D、CAM-B3LYP）
- 双杂化泛函（B2PLYP、DSD-BLYP）

### WAVEFUNCTION_METHODS

20+种波函数方法，包括：
- HF变体（HF、RHF、UHF、ROHF）
- 微扰方法（MP2、RI-MP2、SCS-MP2）
- 耦合簇（CCSD、CCSD(T)、DLPNO-CCSD(T)）
- 多参考（CASSCF、NEVPT2、CASPT2）

### BASIS_SETS

38+种基组，包括：
- Pople系列（6-31G*、6-311G**）
- def2系列（def2-SVP到def2-QZVPP）
- cc-pVXZ系列（cc-pVDZ到cc-pV5Z）
- 辅助基组（def2/J、def2-TZVP/C）

### PERCENT_BLOCKS

21+种%块，包括：
- 核心设置（%maxcore、%pal、%scf）
- 几何设置（%geom、%coords）
- 激发态（%tddft、%cis）
- 溶剂化（%cpcm）

## 诊断引擎 / Diagnostic Engine

### 严重级别 / Severity Levels

- **error**：高置信度错误，阻止提交
- **warning**：高风险输入，显示警告
- **information**：信息性提示
- **hint**：建议性提示

### 诊断类别 / Diagnostic Categories

- syntax：语法错误
- schema：架构验证
- type/value：类型/值错误
- cross-file reference：跨文件引用
- semantic consistency：语义一致性
- preflight/runtime-risk：运行时风险
- style/deprecation：风格/废弃

### 诊断形状 / Diagnostic Shape

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
  "blocking": true
}
```

## Agent CLI / Agent命令行工具

### check命令

```bash
orca-lsp-tool check path/to/input --format json
```

返回完整的诊断列表。

### complete命令

```bash
orca-lsp-tool complete path/to/input --format json
```

返回补全建议列表。

### hover命令

```bash
orca-lsp-tool hover path/to/input --format json
```

返回悬停文档。

### symbols命令

```bash
orca-lsp-tool symbols path/to/input --format json
```

返回文档符号列表。

### fix命令

```bash
orca-lsp-tool fix path/to/input --format json
```

返回快速修复建议。

## 来源列表 / Source List

- `src/orca_lsp/parser.py`
- `src/orca_lsp/keywords.py`
- `src/orca_lsp/server.py`
- `src/orca_lsp/rich_diagnostics.py`
- `src/orca_lsp/tool.py`
