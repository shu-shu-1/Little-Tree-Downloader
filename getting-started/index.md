# Getting Started

A quick start guide to help you get up and running with littledl.

## Prerequisites

- Python 3.10 or higher
- pip or uv package manager

## Installation

### Using pip

```
pip install littledl
```

### Using uv

```
uv add littledl
```

## Basic Usage

### Synchronous Download

```
from littledl import download_file_sync

path = download_file_sync("https://example.com/file.zip")
print(f"Downloaded to: {path}")
```

### Asynchronous Download

```
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

- [Configuration Guide](https://littledl.zsxiaoshu.cn/configuration/index.md) - Learn about all configuration options
- [Authentication](https://littledl.zsxiaoshu.cn/authentication/index.md) - Set up authentication for protected resources
- [API Reference](https://littledl.zsxiaoshu.cn/api-reference/index.md) - Detailed API documentation
