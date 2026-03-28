English | [简体中文](README.zh.md)

# littledl

High-performance download library with IDM-style multi-threaded chunked downloading, intelligent scheduling, and resume support.

## Features

### Core Features
- 🚀 **Multi-threaded Chunked Downloads**: Split files into chunks and download in parallel for maximum speed
- 🎯 **Direct File Writing**: Write directly to final file, no temporary file merging
- 🧠 **Intelligent Scheduling**: Smart chunk reassignment and adaptive concurrency
- ⏯️ **Resume Support**: Continue interrupted downloads from where they left off
- 📊 **Real-time Speed Monitoring**: Live speed calculation, ETA estimation, and trend analysis
- 🔁 **Reliable Fallback**: Auto fallback to single-stream mode when chunked download fails

### Advanced Features
- 🔐 **Multiple Authentication Methods**: Basic, Bearer, Digest, API Key, OAuth2
- 🌐 **Full Proxy Support**: System proxy auto-detection, PAC files, SOCKS5
- ⏱️ **Speed Limiting**: Token bucket, leaky bucket, and adaptive algorithms
- ✅ **Integrity Verification**: Optional post-download hash verification (`verify_hash`, `expected_hash`)
- 🔍 **Server Detection**: Automatic detection of server capabilities for optimal download strategy
- 💻 **Cross-platform**: Windows, macOS, Linux, FreeBSD
- 🔒 **Security**: SSL verification, safe path handling

## Installation

```bash
pip install littledl
```

Or with uv:

```bash
uv add littledl
```

## Documentation

For full documentation, visit [https://littledl.zsxiaoshu.cn/](https://littledl.zsxiaoshu.cn/)

- [Getting Started](https://littledl.zsxiaoshu.cn/getting-started/) - Quick start guide
- [Configuration](https://littledl.zsxiaoshu.cn/configuration/) - Configuration options
- [Proxy](https://littledl.zsxiaoshu.cn/proxy/) - Proxy configuration
- [Error Handling](https://littledl.zsxiaoshu.cn/error-handling/) - Error handling
- [Advanced](https://littledl.zsxiaoshu.cn/advanced/) - Advanced features
- [API Reference](https://littledl.zsxiaoshu.cn/api-reference/) - Complete API reference

## Quick Start

### Basic Usage

```python
from littledl import download_file_sync

path = download_file_sync("https://example.com/large_file.zip")
print(f"Saved to: {path}")
```

### Async Usage

```python
import asyncio
from littledl import download_file

async def main():
    path = await download_file(
        "https://example.com/large_file.zip",
        save_path="./downloads",
        filename="my_file.zip",
    )
    print(f"Saved to: {path}")

asyncio.run(main())
```

### Progress Callback

```python
from littledl import download_file_sync

def on_progress(downloaded: int, total: int, speed: float, eta: int):
    percent = (downloaded / total) * 100
    print(f"\rProgress: {percent:.1f}% | Speed: {speed/1024/1024:.2f} MB/s | ETA: {eta}s", end="")

path = download_file_sync(
    "https://example.com/large_file.zip",
    progress_callback=on_progress,
)
```

Also supports callback payload as event/dict/kwargs:

```python
from littledl import ProgressEvent

def on_event(event: ProgressEvent):
    print(event.progress, event.remaining)

def on_dict(payload: dict):
    print(payload["downloaded"], payload["speed"])

def on_kwargs(**payload):
    print(payload["eta"])
```

### Chunk Status Callback

```python
from littledl import ChunkEvent, download_file_sync

def on_chunk(event: ChunkEvent):
    print(
        f"chunk={event.chunk_index} status={event.status} "
        f"progress={event.progress:.1f}% speed={event.speed/1024:.1f}KB/s"
    )

path = download_file_sync(
    "https://example.com/large_file.zip",
    chunk_callback=on_chunk,
)
```

## Advanced Usage

### Batch Download

Multi-file batch download with specialized optimizations for large numbers of small/large files:

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

Async version:

```python
from littledl import BatchDownloader

downloader = BatchDownloader(max_concurrent_files=5)
await downloader.add_urls(urls, "./downloads")
await downloader.start()
```

### Authentication Configuration

```python
from littledl import DownloadConfig, AuthConfig, AuthType

auth = AuthConfig(
    auth_type=AuthType.BEARER,
    token="your-api-token",
)

config = DownloadConfig(auth=auth)
```

### Proxy Configuration

```python
from littledl import DownloadConfig, ProxyConfig, ProxyMode

# System proxy (auto-detect)
proxy = ProxyConfig(mode=ProxyMode.SYSTEM)

# Custom proxy
proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    http_proxy="http://proxy.example.com:8080",
)

config = DownloadConfig(proxy=proxy)
```

### Speed Limiting

```python
from littledl import DownloadConfig, SpeedLimitConfig, SpeedLimitMode

speed_limit = SpeedLimitConfig(
    enabled=True,
    mode=SpeedLimitMode.GLOBAL,
    max_speed=1024 * 1024,  # 1 MB/s
)

config = DownloadConfig(speed_limit=speed_limit)
```

## Multi-language Support

Set language via environment variable:

```bash
export LITTLELDL_LANGUAGE=zh  # Chinese
export LITTLELDL_LANGUAGE=en  # English
```

Or in code:

```python
from littledl import set_language, get_available_languages

set_language("zh")  # Switch to Chinese
print(get_available_languages())  # {'en': 'English', 'zh': '中文'}
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enable_chunking` | bool | True | Enable multi-threaded chunked download |
| `max_chunks` | int | 16 | Maximum concurrent chunks |
| `chunk_size` | int | 4MB | Default chunk size |
| `buffer_size` | int | 64KB | Disk write buffer size |
| `timeout` | float | 300 | Read/write timeout (seconds) |
| `resume` | bool | True | Enable resume support |
| `verify_ssl` | bool | True | Verify SSL certificates |
| `fallback_to_single_on_failure` | bool | True | Fallback to single-stream if chunked download fails |
| `verify_hash` | bool | False | Verify downloaded file hash |
| `expected_hash` | str | None | Expected hash value used for verification |
| `hash_algorithm` | str | sha256 | Hash algorithm for verification |
| `min_file_size` | int | None | Reject files smaller than this size |
| `max_file_size` | int | None | Reject files larger than this size |

## Cross-platform Support

| Feature | Windows | macOS | Linux | FreeBSD |
|---------|---------|-------|-------|---------|
| Multi-threaded download | ✅ | ✅ | ✅ | ✅ |
| Resume support | ✅ | ✅ | ✅ | ✅ |
| System proxy detection | ✅ | ✅ | ✅ | ✅ |
| Direct file writing | ✅ | ✅ | ✅ | ✅ |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policy and vulnerability reporting.

## License

Apache-2.0 License - See [LICENSE](LICENSE) file for details.
