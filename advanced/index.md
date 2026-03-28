# Advanced Usage

Advanced features and optimizations for littledl.

## Download Styles

littledl supports multiple download styles:

| Style          | Description                                        | Best For                           |
| -------------- | -------------------------------------------------- | ---------------------------------- |
| `single`       | Single-threaded download                           | Small files, servers without Range |
| `multi`        | Multi-threaded segmented download                  | Large files, stable connections    |
| `adaptive`     | Automatically select best style                    | Most use cases                     |
| `hybrid_turbo` | Adaptive chunk sizing with AIMD congestion control | Maximum speed on unstable networks |

### Applying Download Style

```
from littledl import DownloadConfig, DownloadStyle

config = DownloadConfig()
config.apply_style(DownloadStyle.HYBRID_TURBO)
```

## Chunk Management

### Manual Chunk Size

Override automatic chunk sizing for specific use cases:

```
from littledl import DownloadConfig

config = DownloadConfig(
    enable_chunking=True,
    chunk_size=8 * 1024 * 1024,  # 8MB chunks
    max_chunks=8,
)
```

### Disabling Chunking

For small files or specific scenarios:

```
from littledl import DownloadConfig

config = DownloadConfig(enable_chunking=False)
```

## Concurrent Downloads

### Multiple Simultaneous Downloads

```
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

## Custom Headers

```
from littledl import DownloadConfig

config = DownloadConfig(
    headers={
        "User-Agent": "MyApp/1.0",
        "Accept": "application/octet-stream",
    }
)
```

## Cookie Handling

```
from littledl import DownloadConfig

config = DownloadConfig(
    cookies={
        "session_id": "abc123",
    }
)
```

## Custom SSL Verification

### Verify with Custom CA

```
from littledl import DownloadConfig

config = DownloadConfig(
    verify_ssl=True,
    ssl_cert="/path/to/ca-bundle.crt",
)
```

### Disable SSL Verification (Not Recommended)

```
from littledl import DownloadConfig

config = DownloadConfig(verify_ssl=False)
```

## Stream Processing

Download and process content in chunks without saving to disk:

```
from littledl import download_file_stream

async for chunk in download_file_stream("https://example.com/large_file.zip"):
    process(chunk)
```

## Progress Tracking

### Custom Progress Display

```
from littledl import download_file_sync

class ProgressTracker:
    def __init__(self, total: int):
        self.total = total
        self.downloaded = 0

    def __call__(self, downloaded: int, total: int, speed: float, eta: int):
        self.downloaded = downloaded
        percent = (downloaded / total) * 100
        print(f"\r{percent:.1f}% | {speed/1024:.1f} KB/s | ETA: {eta}s", end="")

tracker = ProgressTracker(total=1000000)
path = download_file_sync(
    "https://example.com/file.zip",
    progress_callback=tracker,
)
```

### Chunk Status Tracking

```
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

## Performance Tuning

### Buffer Size

Adjust buffer size for your storage:

```
from littledl import DownloadConfig

config = DownloadConfig(
    buffer_size=256 * 1024,  # 256KB buffer
)
```

### Connection Pooling

Configure connection pool settings:

```
from littledl import DownloadConfig

config = DownloadConfig(
    max_connections=32,
    max_keepalive_connections=16,
)
```
