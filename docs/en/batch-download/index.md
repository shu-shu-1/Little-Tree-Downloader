# Batch Download

littledl supports multi-file batch downloading with specialized optimizations for large numbers of small/large files or mixed scenarios.

## Core Features

- **Adaptive Concurrency**: Dynamically adjusts concurrent downloads based on network conditions
- **Small File Priority**: Automatically identifies and prioritizes small files for better UX
- **Connection Pooling**: All files share a connection pool to reduce connection overhead
- **Batch Probe**: Parallel HEAD requests to fetch file information
- **Smart Chunking**: Automatically selects optimal chunk strategy based on file size

## Quick Start

### Synchronous Batch Download

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

### Async Batch Download

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

## Progress Callback

### Batch Progress Callback

The callback system has been fully upgraded to support multiple invocation styles (event, dict, kwargs, legacy) with detailed per-file progress information.

```python
import asyncio
from littledl import BatchDownloader, BatchProgress

# Style 1: Receive BatchProgress object (recommended)
def on_batch_progress(progress: BatchProgress):
    print(f"Batch Progress: {progress.completed_files}/{progress.total_files}")
    print(f"Speed: {progress.smooth_speed/1024/1024:.1f} MB/s")
    print(f"ETA: {progress.eta:.0f}s")
    print(f"Speed Stability: {progress.speed_stability:.2f}")
    # View downloading files
    for f in progress.get_active_files():
        print(f"  Downloading: {f.filename} - {f.progress:.1f}%")

# Style 2: Receive dict
def on_batch_progress_dict(data: dict):
    print(f"Batch Progress: {data['completed_files']}/{data['total_files']}")
    print(f"Speed: {data['smooth_speed']/1024/1024:.1f} MB/s")

# Style 3: Receive kwargs
def on_batch_progress_kwargs(total_files=0, completed_files=0, smooth_speed=0, **kwargs):
    print(f"Batch Progress: {completed_files}/{total_files}")

# Style 4: Legacy format (auto-detected)
def on_batch_progress_legacy(completed: int, total: int, speed: float, eta: int, stability: float):
    print(f"Batch Progress: {completed}/{total}")

downloader = BatchDownloader()
downloader.set_progress_callback(on_batch_progress)  # Auto-detects style
```

### File Complete Callback

```python
from littledl import FileTask

def on_file_complete(task: FileTask):
    print(f"File Complete: {task.filename} ({task.file_size} bytes)")

downloader = BatchDownloader()
downloader.set_file_complete_callback(on_file_complete)
```

## Advanced Configuration

### Adaptive Concurrency Control

Adaptive concurrency is enabled by default. The system automatically adjusts concurrency based on download speed:

- Speed continuously decreasing → Increase concurrency to utilize more bandwidth
- Speed stable or increasing → Maintain or increase concurrency
- Error rate rising → Automatically reduce concurrency

```python
downloader = BatchDownloader(
    enable_adaptive_concurrency=True,
    max_concurrent_files=10,
)
```

### Manual Concurrency Control

Disable adaptive mode and manually set a fixed concurrency:

```python
downloader = BatchDownloader(
    enable_adaptive_concurrency=False,
    max_concurrent_files=3,
)
```

### File Priority

Support manual file download priority setting:

```python
downloader = BatchDownloader()

await downloader.add_url(url1, priority=0)  # High priority
await downloader.add_url(url2, priority=1)  # Normal priority
await downloader.add_url(url3, priority=2)  # Low priority
```

## Smart Chunking Strategy

The system automatically selects the optimal chunking strategy based on file size:

| File Size | Chunk Strategy | Description |
|----------|---------------|-------------|
| < 5 MB | Single chunk | Avoid chunking overhead |
| 5 MB ~ 100 MB | 4 chunks | Balance concurrency and overhead |
| > 100 MB | 8 chunks | Maximize throughput |

## Getting Download Status

### Get All Tasks

```python
downloader = BatchDownloader()
await downloader.add_urls(urls, "./downloads")
await downloader.start()

tasks = downloader.get_all_tasks()
for task in tasks:
    print(f"{task.filename}: {task.status.value} ({task.progress:.1f}%)")
```

### Get Statistics

```python
stats = downloader.get_stats()
print(f"Total files: {stats['total_files']}")
print(f"Completed: {stats['completed_files']}")
print(f"Failed: {stats['failed_files']}")
print(f"Current concurrency: {stats['current_concurrency']}")
print(f"Total progress: {stats['progress_percent']:.1f}%")
```

### Get Batch Progress

```python
progress = downloader.get_progress()
print(f"Total size: {progress.total_bytes / 1024 / 1024:.1f} MB")
print(f"Downloaded: {progress.downloaded_bytes / 1024 / 1024:.1f} MB")
print(f"Speed: {progress.overall_speed / 1024 / 1024:.1f} MB/s")
print(f"ETA: {progress.eta:.0f}s")
```

## Pause, Resume and Cancel

```python
downloader = BatchDownloader()
await downloader.add_urls(urls, "./downloads")

task = asyncio.create_task(downloader.start())

await asyncio.sleep(5)
await downloader.pause()

await asyncio.sleep(2)
await downloader.resume()

await asyncio.sleep(5)
await downloader.cancel()

await task
```

## API Reference

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
        """Add a single URL to the download queue"""
        ...

    async def add_urls(
        self,
        urls: list[str],
        save_path: str | Path = "./downloads",
    ) -> list[str]:
        """Batch add URLs to the download queue"""
        ...

    def set_progress_callback(self, callback) -> None:
        """Set batch progress callback (completed, total, speed, eta)"""
        ...

    def set_file_complete_callback(self, callback) -> None:
        """Set file complete callback (task: FileTask)"""
        ...

    async def start(self) -> None:
        """Start batch download"""
        ...

    async def pause(self) -> None:
        """Pause download"""
        ...

    async def resume(self) -> None:
        """Resume download"""
        ...

    async def cancel(self) -> None:
        """Cancel download"""
        ...

    async def stop(self) -> None:
        """Stop download and close connection pool"""
        ...

    def get_task(self, task_id: str) -> FileTask | None:
        """Get task by ID"""
        ...

    def get_all_tasks(self) -> list[FileTask]:
        """Get all tasks"""
        ...

    def get_progress(self) -> BatchProgress:
        """Get batch download progress"""
        ...

    def get_stats(self) -> dict:
        """Get statistics"""
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
    pending_files: int
    total_bytes: int
    downloaded_bytes: int
    overall_speed: float
    smooth_speed: float
    eta: float
    speed_stability: float
    elapsed_time: float
    files: tuple[FileProgress, ...]

    @property
    def progress(self) -> float: ...
    @property
    def files_completed_ratio(self) -> float: ...

    def get_active_files(self) -> list[FileProgress]: ...
    def get_pending_files(self) -> list[FileProgress]: ...
    def get_completed_files(self) -> list[FileProgress]: ...
    def get_failed_files(self) -> list[FileProgress]: ...


@dataclass(slots=True)
class FileProgress:
    task_id: str
    filename: str
    url: str
    status: str
    file_size: int
    downloaded: int
    speed: float
    progress: float
    error: str | None
    started_at: float | None
    completed_at: float | None
```

### Convenience Functions

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
    """Async batch download, returns [(url, path, error), ...]"""
    ...

def batch_download_sync(
    urls: list[str],
    save_path: str = "./downloads",
    config: DownloadConfig | None = None,
    **kwargs,
) -> list[tuple[str, Path | None, str | None]]:
    """Synchronous batch download"""
    ...
```

## High-Speed Download Mode (EnhancedBatchDownloader)

`EnhancedBatchDownloader` is a high-performance batch downloader optimized with aria2-style features, providing smarter download scheduling.

### Core Features

| Feature | Description |
|---------|-------------|
| Intelligent Style Selection | Automatically select optimal download style based on file size, server support, and network conditions |
| Dynamic Thread Allocation | Global thread pool unified scheduling to avoid resource waste |
| Multi-source Backup | Support for multiple backup URLs with automatic failover |
| File Reuse | Content-aware matching to avoid duplicate downloads |

### Style Selection Algorithm

The system automatically analyzes and selects the best download style:

```python
from littledl import DownloadStyle, StrategySelector

selector = StrategySelector(
    default_style=DownloadStyle.ADAPTIVE,
    enable_single=True,
    enable_multi=True,
)

profile = selector.analyze_file(
    url="https://example.com/file.zip",
    size=100 * 1024 * 1024,
    supports_range=True,
)

decision = selector.select_style(profile)
print(f"Recommended style: {decision.style.value}")
print(f"Recommended chunks: {decision.recommended_chunks}")
print(f"Estimated speedup: {decision.estimated_speedup:.1f}x")
```

### Usage Example

```python
import asyncio
from littledl import EnhancedBatchDownloader

async def main():
    downloader = EnhancedBatchDownloader(
        max_concurrent_files=5,
        max_total_threads=15,
        enable_existing_file_reuse=True,
        enable_multi_source=True,
    )
    
    await downloader.add_url(
        "https://example.com/file.zip",
        backup_urls=["https://backup.com/file.zip"]
    )
    
    await downloader.start()

asyncio.run(main())
```

### Dynamic Style Allocation

When downloading multiple files, the system dynamically allocates styles based on global resources:

```python
from littledl import DynamicStyleAllocator, DownloadStyle

allocator = DynamicStyleAllocator(
    selector=selector,
    max_concurrent_files=5,
    max_total_chunks=16,
)

decision = await allocator.add_file(
    file_id="file1",
    url="https://example.com/file.zip",
    size=100 * 1024 * 1024,
    supports_range=True,
    priority=1,
)
print(f"Allocated style: {decision.style.value}")
```

### File Reuse Statistics

```python
reuse_stats = downloader.get_file_reuse_stats()
print(f"Checks: {reuse_stats['checks']}")
print(f"Hits: {reuse_stats['hits']}")
print(f"Bytes saved: {reuse_stats['bytes_saved_formatted']}")
```

### API Reference

```python
from littledl import (
    EnhancedBatchDownloader,
    StrategySelector,
    DynamicStyleAllocator,
    DownloadStyle,
)

selector = StrategySelector(
    default_style=DownloadStyle.ADAPTIVE,
    enable_single=True,
    enable_multi=True,
    max_chunks=16,
)

allocator = DynamicStyleAllocator(
    selector=selector,
    max_concurrent_files=5,
    max_total_chunks=16,
)

downloader = EnhancedBatchDownloader(
    config: DownloadConfig | None = None,
    max_concurrent_files: int = 5,
    max_total_threads: int = 15,
    small_file_threshold: int = 1 * 1024 * 1024,
    enable_existing_file_reuse: bool = True,
    enable_multi_source: bool = True,
    enable_adaptive_speed: bool = True,
)
```
