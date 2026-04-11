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

### 进度跟踪

使用 `progress_callback` 参数接收下载进度事件。littledl 自动检测回调签名风格：

```python
from littledl import download_file_sync, ProgressEvent

# 风格 1（推荐）：接收 ProgressEvent 对象
def on_progress(event: ProgressEvent):
    print(f"[{event.filename}] {event.progress:.1f}% - {event.speed / 1024 / 1024:.1f} MB/s")

path = download_file_sync(
    "https://example.com/file.zip",
    progress_callback=on_progress,
)

# 风格 2：接收关键字参数
def on_progress_kwargs(*, downloaded=0, total=0, speed=0, filename="", **kw):
    print(f"[{filename}] {downloaded}/{total} bytes")

# 风格 3：传统位置参数
def on_progress_legacy(downloaded, total, speed, eta):
    print(f"{downloaded}/{total}")
```

## 下一步

- [配置指南](../configuration/index.md) - 了解所有配置选项
- [认证设置](../authentication/index.md) - 为受保护资源设置认证
- [API 参考](../api-reference/index.md) - 详细的 API 文档
