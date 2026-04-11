# 高级用法

littledl 的高级功能和优化。

## 下载风格

littledl 支持多种下载风格：

| 风格 | 说明 | 适用场景 |
| -------------- | ------------------------------------------------ | ----------------------------------- |
| `single` | 单线程下载 | 小文件、不支持 Range 的服务器 |
| `multi` | 多线程分段下载 | 大文件、稳定网络 |
| `adaptive` | 传统自适应调度器 | 兼容旧版调参流程 |
| `fusion` | 四阶段自适应调度器（PROBE -> RAMP -> CRUISE -> TAIL） | 默认推荐，兼顾速度与稳定性 |
| `hybrid_turbo` | 基于 AIMD 的激进自适应模式 | 不稳定网络和强突发吞吐场景 |

### 应用下载风格

```python
from littledl import DownloadConfig, DownloadStyle

config = DownloadConfig()
config.apply_style(DownloadStyle.FUSION)

# hybrid_turbo 仍可用于更激进的旧版调优
config.apply_style(DownloadStyle.HYBRID_TURBO)
```

## 分块管理

### 手动分块大小

为特定用例覆盖自动分块大小：

```python
from littledl import DownloadConfig

config = DownloadConfig(
    enable_chunking=True,
    chunk_size=8 * 1024 * 1024,  # 8MB 分块
    max_chunks=8,
)
```

### 禁用分块

对于小文件或特定场景：

```python
from littledl import DownloadConfig

config = DownloadConfig(enable_chunking=False)
```

## 并发下载

### 多个同时下载

```python
import asyncio
from littledl import download_file

async def download_multiple(urls: list[str]):
    tasks = [download_file(url) for url in urls]
    return await asyncio.gather(*tasks)

paths = asyncio.run(download_multiple([
    "https://example.com/file1.zip",
    "https://example.com/file2.zip",
    "https://example.com/file3.zip",
]))
```

## 自定义请求头

```python
from littledl import DownloadConfig

config = DownloadConfig(
    headers={
        "User-Agent": "MyApp/1.0",
        "Accept": "application/octet-stream",
    }
)
```

## Cookie 处理

```python
from littledl import DownloadConfig

config = DownloadConfig(
    cookies={
        "session_id": "abc123",
    }
)
```

## 自定义 SSL 验证

### 使用自定义 CA 验证

```python
from littledl import DownloadConfig

config = DownloadConfig(
    verify_ssl=True,
    ssl_cert="/path/to/ca-bundle.crt",
)
```

### 禁用 SSL 验证（不推荐）

```python
from littledl import DownloadConfig

config = DownloadConfig(verify_ssl=False)
```

## 流式处理

下载并分块处理内容而不保存到磁盘：

```python
from littledl import download_file_stream

async for chunk in download_file_stream("https://example.com/large_file.zip"):
    process(chunk)
```

## 进度跟踪

### 自定义进度显示

```python
from littledl import download_file_sync

class ProgressTracker:
    def __init__(self, total: int):
        self.total = total
        self.downloaded = 0

    def __call__(self, downloaded: int, total: int, speed: float, eta: int):
        self.downloaded = downloaded
        percent = (downloaded / total) * 100
        print(f"\r{percent:.1f}% | {speed/1024:.1f} KB/s | 剩余: {eta}s", end="")

tracker = ProgressTracker(total=1000000)
path = download_file_sync(
    "https://example.com/file.zip",
    progress_callback=tracker,
)
```

### 分块状态跟踪

```python
from littledl import ChunkEvent, download_file_sync

def on_chunk(event: ChunkEvent):
    print(
        f"chunk={event.chunk_index} status={event.status} "
        f"progress={event.progress:.1f}%"
    )

path = download_file_sync(
    "https://example.com/file.zip",
    chunk_callback=on_chunk,
)
```

## 性能调优

### 缓冲区大小

为您的存储调整缓冲区大小：

```python
from littledl import DownloadConfig

config = DownloadConfig(
    buffer_size=256 * 1024,  # 256KB 缓冲区
)
```

### 连接池

配置连接池设置：

```python
from littledl import DownloadConfig

config = DownloadConfig(
    max_connections=32,
    max_keepalive_connections=16,
)
```
