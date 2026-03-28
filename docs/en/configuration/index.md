# Configuration Guide

Detailed configuration options for littledl.

## DownloadConfig

Main configuration class for download operations.

```python
from littledl import DownloadConfig

config = DownloadConfig(
    enable_chunking=True,
    max_chunks=16,
    chunk_size=4 * 1024 * 1024,  # 4MB
    buffer_size=64 * 1024,        # 64KB
    timeout=300,
    resume=True,
    verify_ssl=True,
)
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_chunking` | bool | True | Enable multi-threaded chunked download |
| `max_chunks` | int | 16 | Maximum number of concurrent chunks |
| `chunk_size` | int | 4MB | Default size for each chunk |
| `buffer_size` | int | 64KB | Disk write buffer size |
| `timeout` | float | 300 | Read/write timeout in seconds |
| `resume` | bool | True | Enable resume support |
| `verify_ssl` | bool | True | Verify SSL certificates |
| `fallback_to_single_on_failure` | bool | True | Auto fallback to single-stream mode on chunked failure |
| `verify_hash` | bool | False | Verify downloaded file hash |
| `expected_hash` | str | None | Expected hash value |
| `hash_algorithm` | str | `sha256` | Hash algorithm used in verification |
| `min_file_size` | int | None | Reject files smaller than this size |
| `max_file_size` | int | None | Reject files larger than this size |
| `progress_update_interval` | float | 0.5 | Progress callback interval in seconds |
| `chunk_callback` | Callable | None | Per-chunk status callback during chunked download |

## Proxy Configuration

```python
from littledl import DownloadConfig, ProxyConfig, ProxyMode

proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    http_proxy="http://proxy.example.com:8080",
    https_proxy="https://proxy.example.com:8080",
)

config = DownloadConfig(proxy=proxy)
```

## Speed Limiting

```python
from littledl import DownloadConfig, SpeedLimitConfig, SpeedLimitMode

speed_limit = SpeedLimitConfig(
    enabled=True,
    mode=SpeedLimitMode.GLOBAL,
    max_speed=1024 * 1024,  # 1 MB/s
)

config = DownloadConfig(speed_limit=speed_limit)
```

## Progress Callback

`progress_callback` supports four formats:

- Legacy positional args: `(downloaded, total, speed, eta)`
- Event object: `ProgressEvent`
- Dictionary payload: `dict`
- Keyword payload: `**payload`

```python
from littledl import ProgressEvent

def on_progress(downloaded: int, total: int, speed: float, eta: int):
    percent = (downloaded / total) * 100
    print(f"\r{percent:.1f}% | {speed/1024:.1f} KB/s | ETA: {eta}s", end="")

def on_event(event: ProgressEvent):
    print(event.progress, event.remaining)

def on_dict(payload: dict):
    print(payload["downloaded"], payload["speed"])

def on_kwargs(**payload):
    print(payload["eta"])

config = DownloadConfig(progress_callback=on_progress)
```

## Chunk Status Callback

`chunk_callback` is only triggered in chunked mode. It supports the same four callback formats.

```python
from littledl import ChunkEvent

def on_chunk(event: ChunkEvent):
    print(event.chunk_index, event.status, event.progress)

config = DownloadConfig(chunk_callback=on_chunk)
```
