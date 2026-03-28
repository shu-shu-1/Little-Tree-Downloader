English | 简体中文

# 贡献指南

首先，感谢您考虑为 littledl 做出贡献！正是因为有像您这样的人，这个项目才能变得更好。

## 目录

- [行为准则](#行为准则)
- [入门指南](#入门指南)
- [开发环境设置](#开发环境设置)
- [如何贡献](#如何贡献)
- [编码规范](#编码规范)
- [提交指南](#提交指南)
- [Pull Request 流程](#pull-request-流程)
- [报告 Bug](#报告-bug)
- [功能建议](#功能建议)

## 行为准则

参与本项目的所有人都必须遵守我们的行为准则。如发现不当行为，请向项目维护者报告。

## 入门指南

### 前置要求

- Python 3.10 或更高版本
- [uv](https://github.com/astral-sh/uv) 包管理器
- Git

### 开发环境设置

1. **Fork 并克隆仓库**

```bash
git clone https://github.com/YOUR_USERNAME/little-tree-downloader.git
cd little-tree-downloader
```

2. **安装依赖**

```bash
uv sync --all-extras
```

3. **运行测试验证设置**

```bash
uv run pytest tests/ -v
```

4. **运行代码检查**

```bash
uv run ruff check src/
```

## 如何贡献

### 报告 Bug

创建 Bug 报告之前，请先检查现有 issues。创建 Bug 报告时，请尽可能详细地包括：

- **使用清晰且描述性的标题**
- **描述复现问题的具体步骤**
- **提供带有代码片段的具体示例**
- **描述您观察到的行为和预期行为**
- **包括您的环境详情**（操作系统、Python 版本、包版本）

### 功能建议

功能建议通过 GitHub issues 跟踪。创建功能建议时：

- **使用清晰且描述性的标题**
- **提供建议功能的逐步描述**
- **提供展示用例的具体示例**
- **描述当前行为并解释预期行为**
- **解释此功能为何有用**

### Pull Requests

1. **创建分支**

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

2. **进行更改**

- 遵循[编码规范](#编码规范)
- 为新功能添加测试
- 根据需要更新文档

3. **运行测试和代码检查**

```bash
uv run pytest tests/ -v --cov
uv run ruff check src/
```

4. **提交更改**

遵循[提交指南](#提交指南)。

5. **推送并创建 Pull Request**

```bash
git push origin your-branch-name
```

## 编码规范

### Python 风格

- 遵循 [PEP 8](https://pep8.org/) 风格指南
- 为所有函数签名使用类型提示
- 为公共模块、函数、类和方法编写文档字符串
- 最大行长 120 个字符

### 代码组织

```
src/littledl/
├── __init__.py      # 公共 API 导出
├── config.py        # 配置类
├── downloader.py    # 主下载器实现
├── chunk.py         # 分块管理
├── worker.py        # 下载工作器
├── scheduler.py     # 智能调度
├── monitor.py       # 速度监控
├── resume.py        # 断点续传
├── connection.py    # 连接管理
├── auth.py          # 认证
├── proxy.py         # 代理支持
├── limiter.py       # 限速
├── detector.py      # 服务器检测
├── compat.py        # 跨平台兼容
├── exceptions.py    # 自定义异常
├── utils.py         # 工具函数
└── i18n/            # 国际化
```

## 提交指南

我们遵循 [Conventional Commits](https://www.conventionalcommits.org/)：

### 格式

```
<类型>(<范围>): <描述>

[可选正文]

[可选页脚]
```

### 类型

- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 仅文档更改
- `style`: 不影响代码含义的更改
- `refactor`: 既不修复 bug 也不添加功能的代码更改
- `perf`: 提高性能的代码更改
- `test`: 添加缺失测试或更正现有测试
- `chore`: 构建过程或辅助工具的更改

## Pull Request 流程

1. 提交前**确保所有测试通过**
2. 为任何新功能**更新文档**
3. 为任何新功能**添加测试**
4. 创建 PR 时**遵循 PR 模板**
5. **请求维护者审查**
6. **及时处理审查反馈**

## 其他资源

- [Python 类型提示](https://docs.python.org/3/library/typing.html)
- [pytest 文档](https://docs.pytest.org/)
- [httpx 文档](https://www.python-httpx.org/)

## 问题？

如有问题，请随时提交 issue 或联系维护者。

感谢您的贡献！
