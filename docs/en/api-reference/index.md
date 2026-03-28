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

## Callback Events

### ProgressEvent

```python
ProgressEvent(
    downloaded: int,
    total: int,
    speed: float,
    eta: int,
    progress: float,
    remaining: int,
    timestamp: float,
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
