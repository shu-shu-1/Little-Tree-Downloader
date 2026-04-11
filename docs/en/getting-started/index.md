# Getting Started

A quick start guide to help you get up and running with littledl.

## Prerequisites

- Python 3.10 or higher
- pip or uv package manager

## Installation

### Using pip

```bash
pip install littledl
```

### Using uv

```bash
uv add littledl
```

## Basic Usage

### Synchronous Download

```python
from littledl import download_file_sync

path = download_file_sync("https://example.com/file.zip")
print(f"Downloaded to: {path}")
```

### Asynchronous Download

```python
import asyncio
from littledl import download_file

async def main():
    path = await download_file(
        "https://example.com/file.zip",
        save_path="./downloads",
        filename="my_file.zip",
    )
    print(f"Downloaded to: {path}")

asyncio.run(main())
```

### Progress Tracking

Use the `progress_callback` parameter to receive download progress events. littledl auto-detects your callback signature style:

```python
from littledl import download_file_sync, ProgressEvent

# Style 1 (Recommended): Receive ProgressEvent object
def on_progress(event: ProgressEvent):
    print(f"[{event.filename}] {event.progress:.1f}% - {event.speed / 1024 / 1024:.1f} MB/s")

path = download_file_sync(
    "https://example.com/file.zip",
    progress_callback=on_progress,
)

# Style 2: Receive keyword arguments
def on_progress_kwargs(*, downloaded=0, total=0, speed=0, filename="", **kw):
    print(f"[{filename}] {downloaded}/{total} bytes")

# Style 3: Legacy positional arguments
def on_progress_legacy(downloaded, total, speed, eta):
    print(f"{downloaded}/{total}")
```

## Next Steps

- [Configuration Guide](../configuration/index.md) - Learn about all configuration options
- [Authentication](../authentication/index.md) - Set up authentication for protected resources
- [API Reference](../api-reference/index.md) - Detailed API documentation
