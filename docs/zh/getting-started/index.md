# 快速入门

快速入门指南，帮助您快速上手 littledl。

## 前置要求

- Python 3.10 或更高版本
- pip 或 uv 包管理器

## 安装

### 使用 pip

```bash
pip install littledl
```

### 使用 uv

```bash
uv add littledl
```

## 基本用法

### 同步下载

```python
from littledl import download_file_sync

path = download_file_sync("https://example.com/file.zip")
print(f"下载至: {path}")
```

### 异步下载

```python
import asyncio
from littledl import download_file

async def main():
    path = await download_file(
        "https://example.com/file.zip",
        save_path="./downloads",
        filename="my_file.zip",
    )
    print(f"下载至: {path}")

asyncio.run(main())
```

## 下一步

- [配置指南](../configuration/index.md) - 了解所有配置选项
- [认证设置](../authentication/index.md) - 为受保护资源设置认证
- [API 参考](../api-reference/index.md) - 详细的 API 文档
