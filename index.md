# littledl Documentation

Welcome to littledl — a high-performance file download library and CLI focused on single-file and batch downloads. It supports HTTP Range based chunked downloading, resume, adaptive scheduling, and a rich callback system.

```
from littledl import download_file_sync

path = download_file_sync("https://example.com/file.zip")
print(f"Downloaded to: {path}")
```

## Why littledl

- **Fast and steady FUSION scheduling**: four-phase adaptive control (probe → ramp → cruise → tail) with bandwidth-ceiling estimation and marginal-gain detection; the cruise phase locks concurrency and uses smoothed signals, so it stays smooth like IDM instead of sawtooth jitter
- **Intelligent strategy selection**: automatically picks a download style (single / multi / adaptive / fusion / hybrid_turbo) from file size, server capability, and network conditions — no manual tuning
- **Multi-threaded segmented download**: HTTP Range based concurrent segments that detect slow chunks and steal work in the tail phase to maximize bandwidth
- **Atomic writes, never corrupts**: chunked data lands in a preallocated `.part` file with lock-serialized positional writes and is atomically renamed on success; a failed run never destroys an existing file
- **Reliable resume**: restores exact chunk byte ranges (including resplit chunks) and validates ETag/Last-Modified compatibility before resuming
- **Real-time progress callbacks**: a unified callback system auto-adapts to event / dict / kwargs / legacy signatures, exposing speed, ETA, and per-chunk status
- **Enterprise-grade features**: authentication (Basic / Bearer / Digest / API Key / OAuth2), proxy (system / custom / SOCKS5), speed limiting, hash verification, content-aware file reuse, and multi-source failover
- **Graceful fallback**: automatically falls back to single-stream mode when chunked transfer is not viable

## Getting Started

- [Getting Started](https://shu-shu-1.github.io/Little-Tree-Downloader/getting-started/index.md) - Quick start guide
- [Installation](https://shu-shu-1.github.io/Little-Tree-Downloader/getting-started/#installation) - Installation instructions

## User Guides

- [Configuration](https://shu-shu-1.github.io/Little-Tree-Downloader/configuration/index.md) - Configuration options
- [Authentication](https://shu-shu-1.github.io/Little-Tree-Downloader/authentication/index.md) - Authentication setup
- [Proxy](https://shu-shu-1.github.io/Little-Tree-Downloader/proxy/index.md) - Proxy configuration
- [Error Handling](https://shu-shu-1.github.io/Little-Tree-Downloader/error-handling/index.md) - Error handling and retries

## Advanced Topics

- [Advanced Usage](https://shu-shu-1.github.io/Little-Tree-Downloader/advanced/index.md) - Advanced features and optimizations
- [Batch Download](https://shu-shu-1.github.io/Little-Tree-Downloader/batch-download/index.md) - Multi-file batch download
- [CLI](https://shu-shu-1.github.io/Little-Tree-Downloader/cli/index.md) - Command-line usage
- [API Reference](https://shu-shu-1.github.io/Little-Tree-Downloader/api-reference/index.md) - Complete API reference

## Other

- [Contributing](https://shu-shu-1.github.io/CONTRIBUTING.md) - Contribution guidelines
- [Changelog](https://shu-shu-1.github.io/CHANGELOG.md) - Version history
- [Security](https://shu-shu-1.github.io/SECURITY.md) - Security policy
