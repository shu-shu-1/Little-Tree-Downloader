# 批量下载

littledl 支持多文件批量下载，针对大量小文件、大文件或混合场景进行了专门优化。

## 核心特性

- **自适应并发**：根据网络状况动态调整同时下载的文件数
- **小文件优先**：自动识别小文件并优先处理，提升用户体验
- **连接复用**：所有文件共享连接池，减少连接建立开销
- **批量Probe**：并行发送 HEAD 请求获取文件信息
- **智能分块**：根据文件大小自动选择最优分块策略

## 快速开始

### 同步批量下载

```python
from littledl import batch_download_sync

results = batch_download_sync(
    urls=[
        "https://example.com/file1.zip",
        "https://example.com/file2.zip",
        "https://example.com/file3.zip",
    ],
    save_path="./downloads",
    max_concurrent_files=5,
)

for url, path, error in results:
    if path:
        print(f"✓ {url} -> {path}")
    else:
        print(f"✗ {url}: {error}")
```

### 异步批量下载

```python
import asyncio
from littledl import BatchDownloader

async def main():
    downloader = BatchDownloader(
        max_concurrent_files=5,
        max_concurrent_chunks_per_file=4,
        enable_adaptive_concurrency=True,
    )

    await downloader.add_urls([
        "https://example.com/file1.zip",
        "https://example.com/file2.zip",
    ], "./downloads")

    await downloader.start()

asyncio.run(main())
```

## 进度回调

### 批量进度回调

```python
import asyncio
from littledl import BatchDownloader

def on_batch_progress(completed: int, total: int, speed: float, eta: int):
    print(f"批量进度: {completed}/{total} | 速度: {speed/1024/1024:.1f} MB/s | 预计剩余: {eta}s")

downloader = BatchDownloader()
downloader.set_progress_callback(on_batch_progress)
```

### 单文件完成回调

```python
from littledl import FileTask

def on_file_complete(task: FileTask):
    print(f"文件完成: {task.filename} ({task.file_size} bytes)")

downloader = BatchDownloader()
downloader.set_file_complete_callback(on_file_complete)
```

## 高级配置

### 自适应并发控制

默认启用自适应并发控制，系统会根据下载速度自动调整并发数：

- 速度持续下降 → 增加并发利用更多带宽
- 速度稳定上升 → 维持或增加并发
- 错误率上升 → 自动降低并发

```python
downloader = BatchDownloader(
    enable_adaptive_concurrency=True,
    max_concurrent_files=10,
)
```

### 手动并发控制

禁用自适应模式，手动设置固定并发数：

```python
downloader = BatchDownloader(
    enable_adaptive_concurrency=False,
    max_concurrent_files=3,
)
```

### 文件优先级

支持手动设置文件下载优先级：

```python
downloader = BatchDownloader()

# 添加文件时可指定优先级（数字越小优先级越高）
await downloader.add_url(url1, priority=0)  # 高优先级
await downloader.add_url(url2, priority=1)  # 普通优先级
await downloader.add_url(url3, priority=2)  # 低优先级
```

## 智能分块策略

系统会根据文件大小自动选择最优分块策略：

| 文件大小 | 分块策略 | 说明 |
|----------|----------|------|
| < 5 MB | 单分块 | 避免分片开销 |
| 5 MB ~ 100 MB | 4 分块 | 平衡并发和开销 |
| > 100 MB | 8 分块 | 最大化吞吐 |

## 获取下载状态

### 获取所有任务

```python
downloader = BatchDownloader()
await downloader.add_urls(urls, "./downloads")
await downloader.start()

tasks = downloader.get_all_tasks()
for task in tasks:
    print(f"{task.filename}: {task.status.value} ({task.progress:.1f}%)")
```

### 获取统计信息

```python
stats = downloader.get_stats()
print(f"总文件数: {stats['total_files']}")
print(f"已完成: {stats['completed_files']}")
print(f"失败: {stats['failed_files']}")
print(f"当前并发: {stats['current_concurrency']}")
print(f"总进度: {stats['progress_percent']:.1f}%")
```

### 获取批量进度

```python
progress = downloader.get_progress()
print(f"总大小: {progress.total_bytes / 1024 / 1024:.1f} MB")
print(f"已下载: {progress.downloaded_bytes / 1024 / 1024:.1f} MB")
print(f"速度: {progress.overall_speed / 1024 / 1024:.1f} MB/s")
print(f"预计剩余: {progress.eta:.0f}s")
```

## 暂停、恢复和取消

```python
downloader = BatchDownloader()
await downloader.add_urls(urls, "./downloads")

# 启动下载
task = asyncio.create_task(downloader.start())

# 暂停
await asyncio.sleep(5)
await downloader.pause()

# 恢复
await asyncio.sleep(2)
await downloader.resume()

# 取消
await asyncio.sleep(5)
await downloader.cancel()

# 等待完成
await task
```

## API 参考

### BatchDownloader

```python
class BatchDownloader:
    def __init__(
        self,
        config: DownloadConfig | None = None,
        max_concurrent_files: int = 5,
        max_concurrent_chunks_per_file: int = 4,
        enable_adaptive_concurrency: bool = True,
        enable_small_file_priority: bool = True,
    ) -> None:
        ...

    async def add_url(
        self,
        url: str,
        save_path: str | Path = "./downloads",
        filename: str | None = None,
        priority: int = 0,
    ) -> str:
        """添加单个URL到下载队列"""
        ...

    async def add_urls(
        self,
        urls: list[str],
        save_path: str | Path = "./downloads",
    ) -> list[str]:
        """批量添加URL到下载队列"""
        ...

    def set_progress_callback(self, callback) -> None:
        """设置批量进度回调 (completed, total, speed, eta)"""
        ...

    def set_file_complete_callback(self, callback) -> None:
        """设置单文件完成回调 (task: FileTask)"""
        ...

    async def start(self) -> None:
        """启动批量下载"""
        ...

    async def pause(self) -> None:
        """暂停下载"""
        ...

    async def resume(self) -> None:
        """恢复下载"""
        ...

    async def cancel(self) -> None:
        """取消下载"""
        ...

    async def stop(self) -> None:
        """停止下载并关闭连接池"""
        ...

    def get_task(self, task_id: str) -> FileTask | None:
        """根据ID获取任务"""
        ...

    def get_all_tasks(self) -> list[FileTask]:
        """获取所有任务"""
        ...

    def get_progress(self) -> BatchProgress:
        """获取批量下载进度"""
        ...

    def get_stats(self) -> dict:
        """获取统计信息"""
        ...
```

### FileTask

```python
@dataclass
class FileTask:
    task_id: str
    url: str
    save_path: Path
    filename: str | None
    status: FileTaskStatus
    file_size: int
    downloaded: int
    speed: float
    error: str | None
    retry_count: int
    priority: int
    supports_range: bool
    chunks: int

    @property
    def progress(self) -> float: ...
    @property
    def is_active(self) -> bool: ...
    @property
    def is_completed(self) -> bool: ...
    @property
    def is_failed(self) -> bool: ...
    @property
    def is_small_file(self) -> bool: ...
    @property
    def is_large_file(self) -> bool: ...
```

### BatchProgress

```python
@dataclass
class BatchProgress:
    total_files: int
    completed_files: int
    failed_files: int
    active_files: int
    total_bytes: int
    downloaded_bytes: int
    overall_speed: float
    eta: float

    @property
    def progress(self) -> float: ...
    @property
    def files_completed_ratio(self) -> float: ...
```

### 便捷函数

```python
async def batch_download(
    urls: list[str],
    save_path: str = "./downloads",
    config: DownloadConfig | None = None,
    max_concurrent_files: int = 5,
    max_concurrent_chunks_per_file: int = 4,
    progress_callback=None,
    file_complete_callback=None,
) -> list[tuple[str, Path | None, str | None]]:
    """异步批量下载，返回 [(url, path, error), ...]"""
    ...

def batch_download_sync(
    urls: list[str],
    save_path: str = "./downloads",
    config: DownloadConfig | None = None,
    **kwargs,
) -> list[tuple[str, Path | None, str | None]]:
    """同步批量下载"""
    ...
```
