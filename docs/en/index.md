# littledl Documentation

Welcome to littledl — a high-performance file download library and CLI focused on single-file and batch downloads. It supports HTTP Range based chunked downloading, resume, adaptive scheduling, and a rich callback system.

```python
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

- [Getting Started](getting-started/index.md) - Quick start guide
- [Installation](getting-started/index.md#installation) - Installation instructions

## User Guides

- [Configuration](configuration/index.md) - Configuration options
- [Authentication](authentication/index.md) - Authentication setup
- [Proxy](proxy/index.md) - Proxy configuration
- [Error Handling](error-handling/index.md) - Error handling and retries

## Advanced Topics

- [Advanced Usage](advanced/index.md) - Advanced features and optimizations
- [Batch Download](batch-download/index.md) - Multi-file batch download
- [CLI](cli/index.md) - Command-line usage
- [API Reference](api-reference/index.md) - Complete API reference

## Other

- [Contributing](../../CONTRIBUTING.md) - Contribution guidelines
- [Changelog](../../CHANGELOG.md) - Version history
- [Security](../../SECURITY.md) - Security policy
