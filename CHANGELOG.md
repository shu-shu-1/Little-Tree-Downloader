English | [简体中文](CHANGELOG.zh.md)

# Changelog

All notable changes to littledl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 1.0.0 - 2026-06-23

### Added

- Atomic chunked downloads: data is written to a preallocated `.part` file through a single OS file descriptor with lock-serialized positional writes, then atomically renamed to the final name on success
- Layout-aware resume: persisted chunk byte ranges are restored exactly, including resplit chunks, with ETag/Last-Modified compatibility validation before resuming
- FUSION four-phase adaptive scheduler (PROBE -> RAMP -> CRUISE -> TAIL) with bandwidth-ceiling estimation, P50 speed, and marginal-gain detection
- Intelligent strategy selection based on file size, server capability, and network conditions, with FUSION as the default style
- Unified callback system supporting event, dict, kwargs, and legacy signatures for single-file and batch downloads
- Batch downloads with global chunk budgeting, domain affinity, adaptive concurrency, and rich progress UI
- Authentication (Basic, Bearer, Digest, API Key, OAuth2), proxy (system, PAC, SOCKS5), speed limiting, hash verification, file reuse, and multi-source failover
- Single source of truth for the package version via `importlib.metadata`, reflected in `__version__` and the default User-Agent

### Removed

- Unused parallel implementations and dead exports, consolidating the public API surface to the actively used components
