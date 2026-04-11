# API Reference

Complete API reference for littledl.

## Core Functions

### download_file_sync

Synchronous file download.

```python
from littledl import download_file_sync

path = download_file_sync(
    url: str,
    save_path: str = ".",
    filename: str | None = None,
    config: DownloadConfig | None = None,
    progress_callback: Callable | None = None,
    chunk_callback: Callable | None = None,
) -> Path
```

### download_file

Asynchronous file download.

```python
from littledl import download_file

path = await download_file(
    url: str,
    save_path: str = ".",
    filename: str | None = None,
    config: DownloadConfig | None = None,
    progress_callback: Callable | None = None,
    chunk_callback: Callable | None = None,
) -> Path
```

## Configuration Classes

### DownloadConfig

```python
from littledl import DownloadConfig

config = DownloadConfig(
    enable_chunking: bool = True,
    max_chunks: int = 16,
    chunk_size: int = 4 * 1024 * 1024,
    buffer_size: int = 64 * 1024,
    timeout: float = 300,
    resume: bool = True,
    verify_ssl: bool = True,
    auth: AuthConfig | None = None,
    proxy: ProxyConfig | None = None,
    speed_limit: SpeedLimitConfig | None = None,
    progress_callback: Callable | None = None,
    chunk_callback: Callable | None = None,
)
```

#### Methods

**`apply_style(style: Any) -> "DownloadConfig"`**

Quickly reconfigures all internal scheduling variables, chunking thresholds, and AIMD congestion control parameters based on a provided style. Supports either a `DownloadStyle` enum or a standard string style name (e.g., `"SINGLE"`, `"MULTI"`, `"ADAPTIVE"`, or `"HYBRID_TURBO"`). Returns the modified `DownloadConfig` instance.

## Callback Events

### ProgressEvent

Single-file download progress event. Includes file context when emitted by the `Downloader`.

```python
ProgressEvent(
    downloaded: int,
    total: int,
    speed: float,
    eta: int,
    progress: float,
    remaining: int,
    timestamp: float,
    unknown_size: bool = False,
    filename: str = "",   # filename being downloaded
    url: str = "",        # URL being downloaded
)
```

### ChunkEvent

```python
ChunkEvent(
    chunk_index: int,
    status: str,  # started/downloading/completed/failed
    downloaded: int,
    total: int,
    progress: float,
    speed: float,
    error: str | None,
    timestamp: float,
)
```

## Unified Callback System

The `littledl.callback` module provides a unified event system for building custom download managers.

### EventType

```python
from littledl import EventType

EventType.FILE_PROGRESS    # Single file progress update
EventType.FILE_COMPLETE    # Single file download complete
EventType.FILE_ERROR       # Single file download error
EventType.FILE_RETRY       # Single file retry
EventType.BATCH_PROGRESS   # Batch download progress
EventType.BATCH_COMPLETE   # Batch download complete
EventType.CHUNK_PROGRESS   # Chunk-level progress
EventType.CHUNK_COMPLETE   # Chunk-level complete
EventType.CHUNK_ERROR      # Chunk-level error
```

### FileProgressEvent

Rich event object for file-level progress monitoring.

```python
from littledl import FileProgressEvent

FileProgressEvent(
    event_type: EventType = EventType.FILE_PROGRESS,
    task_id: str = "",
    filename: str = "",
    url: str = "",
    file_size: int = 0,
    downloaded: int = 0,
    speed: float = 0.0,
    progress: float = 0.0,
    eta: float = -1.0,
    chunks_total: int = 0,
    chunks_completed: int = 0,
)
```

### FileCompleteEvent

```python
from littledl import FileCompleteEvent

FileCompleteEvent(
    event_type: EventType = EventType.FILE_COMPLETE,
    task_id: str = "",
    filename: str = "",
    url: str = "",
    file_size: int = 0,
    saved_path: str = "",
    error: str | None = None,
)
```

### ThrottledCallback

Wraps a callback adapter to throttle emission frequency, preventing UI jank.

```python
from littledl import UnifiedCallbackAdapter, ThrottledCallback

adapter = UnifiedCallbackAdapter(my_callback)
throttled = ThrottledCallback(adapter, min_interval=0.1)  # max 10 calls/sec
await throttled.emit(event)
await throttled.flush()  # emit any pending event
```

### CallbackChain

Chain multiple callbacks together.

```python
from littledl import CallbackChain

chain = CallbackChain()
chain.add(logging_callback)
chain.add(ui_callback)
await chain.emit(event)
```
```

### AuthConfig

```python
from littledl import AuthConfig, AuthType

auth = AuthConfig(
    auth_type: AuthType,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    api_key: str | None = None,
    api_key_header: str | None = None,
)
```

### ProxyConfig

```python
from littledl import ProxyConfig, ProxyMode

proxy = ProxyConfig(
    mode: ProxyMode = ProxyMode.SYSTEM,
    http_proxy: str | None = None,
    https_proxy: str | None = None,
    socks5_proxy: str | None = None,
)
```

### SpeedLimitConfig

```python
from littledl import SpeedLimitConfig, SpeedLimitMode

speed_limit = SpeedLimitConfig(
    enabled: bool = False,
    mode: SpeedLimitMode = SpeedLimitMode.GLOBAL,
    max_speed: int = 0,
)
```

## Enums

### AuthType

- `BASIC`
- `BEARER`
- `DIGEST`
- `API_KEY`
- `OAUTH2`

### ProxyMode

- `SYSTEM` - Auto-detect system proxy
- `CUSTOM` - Use custom proxy settings
- `NONE` - No proxy

### SpeedLimitMode

- `GLOBAL` - Limit overall speed
- `PER_CHUNK` - Limit per-chunk speed

## Language Support

```python
from littledl import set_language, get_available_languages

set_language("zh")  # or "en"
print(get_available_languages())  # {'en': 'English', 'zh': '中文'}
```

## File Writers

### BufferedFileWriter

High-performance buffered file writer for optimized concurrent download performance.

```python
from littledl import BufferedFileWriter

writer = BufferedFileWriter(
    file_path="/path/to/file.zip",
    mode="wb",
    buffer_size=512 * 1024,  # 512KB buffer
    flush_interval=0.5,      # 500ms auto flush
    max_buffers=16,          # Maximum concurrent buffers
)

await writer.open()
await writer.write_at(offset=0, data=b"chunk data")
await writer.close()
```

### DirectFileWriter

Direct file writer (traditional implementation, kept for backward compatibility).

```python
from littledl import DirectFileWriter

writer = DirectFileWriter(file_path="/path/to/file.zip")
await writer.open()
await writer.write_at(offset=0, data=b"chunk data")
await writer.close()
```

**Note**: BufferedFileWriter is automatically used in chunked downloads, no manual configuration needed.
