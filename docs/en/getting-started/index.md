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

## Next Steps

- [Configuration Guide](../configuration/index.md) - Learn about all configuration options
- [Authentication](../authentication/index.md) - Set up authentication for protected resources
- [API Reference](../api-reference/index.md) - Detailed API documentation
