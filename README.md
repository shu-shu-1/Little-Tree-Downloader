English | [简体中文](README.zh.md)

# littledl

High-performance download library with multi-threaded segmented downloading, intelligent strategy selection, and adaptive optimization.

## Features

### Core Features

- 🚀 **Multi-threaded Segmented Download**: Split files into chunks and download in parallel using HTTP Range requests for maximum speed (inspired by aria2, IDM and other tools)
- 🧠 **Intelligent Strategy Selection**: Automatically choose optimal download style (single/multi/adaptive/fusion/hybrid_turbo) based on file size, server capabilities, and network conditions
- 🎨 **Multiple Download Styles**: Support for single-threaded, multi-threaded, adaptive, FUSION, and hybrid_turbo download styles to suit different scenarios and preferences
- 🎯 **Direct File Writing**: Write directly to final file, no temporary file merging
- ⏯️ **Resume Support**: Continue interrupted downloads from where they left off
- 📊 **Real-time Speed Monitoring**: Live speed calculation, ETA estimation, and trend analysis
- 🔁 **Reliable Fallback**: Auto fallback to single-stream mode when chunked download fails

### Advanced Features

- 🔐 **Multiple Authentication Methods**: Basic, Bearer, Digest, API Key, OAuth2
- 🌐 **Full Proxy Support**: System proxy auto-detection, PAC files, SOCKS5
- ⏱️ **Speed Limiting**: Token bucket, leaky bucket, and adaptive algorithms
- ✅ **Integrity Verification**: Optional post-download hash verification (`verify_hash`, `expected_hash`)
- 🔍 **Server Detection**: Automatic detection of server capabilities for optimal download strategy
- 💾 **File Reuse**: Content-aware matching to reuse existing files and save bandwidth
- 🔄 **Multi-source Backup**: Support for multiple backup URLs with automatic failover
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

For full documentation, visit [https://shu-shu-1.github.io/Little-Tree-Downloader/](https://shu-shu-1.github.io/Little-Tree-Downloader/)

- [Getting Started](https://shu-shu-1.github.io/Little-Tree-Downloader/getting-started/) - Quick start guide
- [Configuration](https://shu-shu-1.github.io/Little-Tree-Downloader/configuration/) - Configuration options
- [Batch Download](https://shu-shu-1.github.io/Little-Tree-Downloader/batch-download/) - Multi-file batch download
- [Proxy](https://shu-shu-1.github.io/Little-Tree-Downloader/proxy/) - Proxy configuration
- [Error Handling](https://shu-shu-1.github.io/Little-Tree-Downloader/error-handling/) - Error handling
- [Advanced](https://shu-shu-1.github.io/Little-Tree-Downloader/advanced/) - Advanced features
- [API Reference](https://shu-shu-1.github.io/Little-Tree-Downloader/api-reference/) - Complete API reference

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

## Download Styles

littledl supports five download styles that you can choose based on your needs:

| Style | Description | Best For |
| ------------ | ------------------------------------------------------------ | -------------------------------------------------- |
| `single` | Single-threaded download | Small files, servers without Range support |
| `multi` | Multi-threaded segmented download | Large files, stable connections |
| `adaptive` | Traditional adaptive chunk scheduler | Compatibility with older tuning preferences |
| `fusion` | Four-phase adaptive scheduler (PROBE -> RAMP -> CRUISE -> TAIL) | Default choice for speed and stability |
| `hybrid_turbo` | Aggressive AIMD-based adaptive mode | Unstable networks where maximum burst speed matters |

### Automatic Style Selection (Recommended)

```bash
# FUSION is the default, so --style can be omitted
littledl "https://example.com/file.zip"
```

```python
from littledl import DownloadConfig, DownloadStyle

# Use the default FUSION strategy
config = DownloadConfig().apply_style(DownloadStyle.FUSION)
```

### Manual Style Selection

```bash
# Force multi-threaded
littledl "https://example.com/file.zip" --style multi --max-chunks 8

# Force the four-phase FUSION scheduler
littledl "https://example.com/file.zip" --style fusion

# Force hybrid_turbo mode for aggressive AIMD behavior
littledl "https://example.com/file.zip" --style hybrid_turbo
```

```python
from littledl import StrategySelector, DownloadStyle

selector = StrategySelector(
    default_style=DownloadStyle.FUSION,
    enable_single=True,
    enable_multi=True,
    max_chunks=16,
)
```

```python
from littledl import StrategySelector, DownloadStyle

selector = StrategySelector(
    default_style=DownloadStyle.MULTI,
    enable_single=True,
    enable_multi=True,
)
```

### Analyze Before Download

Use `--info` flag to analyze and get download strategy recommendations:

```bash
littledl "https://example.com/large_file.zip" --info
```

Output:

```
File Info:
  Filename: large_file.zip
  Size: 1.5 GB
  Content-Type: application/zip
  Resume Support: Yes

Strategy Analysis:
  File: large_file.zip
  Size: 1.5 GB
    Recommended Style: FUSION
    Recommended Chunks: 12
    Estimated Speedup: 4.0x
    Reason: Large file + stable fast network, FUSION full-speed mode
  Size Category: large (> 100MB)
  Range Support: Yes
```

## Progress Callback

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

## Batch Download

### High-Performance Batch Download

```python
from littledl import EnhancedBatchDownloader

downloader = EnhancedBatchDownloader(
    max_concurrent_files=5,
    max_total_threads=15,
    enable_existing_file_reuse=True,
    enable_multi_source=True,
)

# Global threads are reused across files, and per-file chunk counts
# are kept within the batch-wide budget automatically.

# Add files with backup URLs
await downloader.add_url(
    "https://example.com/file.zip",
    backup_urls=["https://backup.com/file.zip"]
)

await downloader.start()
```

### Simple Batch Download

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

## Configuration Options

| Option                            | Type  | Default | Description                                         |
| --------------------------------- | ----- | ------- | --------------------------------------------------- |
| `enable_chunking`               | bool  | True    | Enable multi-threaded chunked download              |
| `max_chunks`                    | int   | 16      | Maximum concurrent chunks                           |
| `chunk_size`                    | int   | 4MB     | Default chunk size                                  |
| `buffer_size`                   | int   | 64KB    | Disk write buffer size                              |
| `timeout`                       | float | 300     | Read/write timeout (seconds)                        |
| `resume`                        | bool  | True    | Enable resume support                               |
| `verify_ssl`                    | bool  | True    | Verify SSL certificates                             |
| `fallback_to_single_on_failure` | bool  | True    | Fallback to single-stream if chunked download fails |
| `verify_hash`                   | bool  | False   | Verify downloaded file hash                         |
| `expected_hash`                 | str   | None    | Expected hash value used for verification           |
| `hash_algorithm`                | str   | sha256  | Hash algorithm for verification                     |
| `min_file_size`                 | int   | None    | Reject files smaller than this size                 |
| `max_file_size`                 | int   | None    | Reject files larger than this size                  |

## CLI Usage

```bash
# Download with automatic style selection
littledl "https://example.com/file.zip" -o ./downloads

# Explicit FUSION mode
littledl "https://example.com/file.zip" --style fusion

# Analyze and recommend strategy
littledl "https://example.com/file.zip" --info

# Force multi-threaded mode
littledl "https://example.com/file.zip" --style multi --max-chunks 8

# Download with speed limit
littledl "https://example.com/file.zip" --speed-limit 1048576

# Resume disabled
littledl "https://example.com/file.zip" --no-resume
```

## Cross-platform Support

| Feature                 | Windows | macOS | Linux | FreeBSD |
| ----------------------- | ------- | ----- | ----- | ------- |
| Multi-threaded download | ✅      | ✅    | ✅    | ✅      |
| Resume support          | ✅      | ✅    | ✅    | ✅      |
| System proxy detection  | ✅      | ✅    | ✅    | ✅      |
| Direct file writing     | ✅      | ✅    | ✅    | ✅      |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and contribution guidelines.

## Security

See [SECURITY.md](SECURITY.md) for security policy and vulnerability reporting.

## License

Apache-2.0 License - See [LICENSE](LICENSE) file for details.
