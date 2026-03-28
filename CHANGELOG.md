English | [简体中文](CHANGELOG.zh.md)

# Changelog

All notable changes to littledl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-XX

### Added
- IDM-style multi-threaded chunked downloading
- Smart scheduling with slow chunk detection and resplitting
- Resume support with chunk-level progress tracking
- Speed monitoring with real-time calculation
- Adaptive concurrency adjustment
- Connection pooling with HTTP/2 support
- Progress callback support
- Rich configuration options
- Comprehensive error handling
- File integrity verification (SHA256, MD5)
- Automatic filename detection from various sources

### Features
- **Multi-threaded Downloads**: Split files into chunks and download in parallel
- **Smart Scheduling**: Intelligent chunk resplitting for optimal speed
- **Resume Support**: Continue interrupted downloads seamlessly
- **Speed Monitoring**: Real-time speed calculation and ETA estimation
- **Adaptive Scheduling**: Dynamic adjustment based on network conditions
- **Connection Management**: Efficient HTTP connection reuse

### Supported Platforms
- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+)
- FreeBSD 13+

[0.1.0]: https://github.com/little-tree/little-tree-downloader/releases/tag/v0.1.0