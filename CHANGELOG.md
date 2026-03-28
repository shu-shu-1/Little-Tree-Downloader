English | [简体中文](CHANGELOG.zh.md)

# Changelog

All notable changes to littledl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 0.4.1 - 2026-03-29

### Fixed

- Fixed `httpx.Timeout` initialization in `probe_url` missing `write` and `pool` parameters
- Fixed `asyncio.run()` cannot be called from a running event loop in `run_download`
- Fixed filename fallback when server doesn't send `Content-Disposition` header (CDN downloads defaulting to `download.bin`)
- Fixed `--temp-dir` CLI option not wired to `DownloadConfig`

### Added

- `--temp-dir` CLI option to specify temporary directory for download temp files

## 0.4.0 - 2026-03-29

### Added

- **CLI Batch Download Support**: Full-featured batch download from file
  - `-F, --batch-file` option to read URLs from a text file
  - `--max-concurrent` option to control parallel download count
  - `read_urls_from_file()` function with validation and comment support

- **CLI Output Format Control**: Multiple output modes for different use cases
  - `--output-format {auto,json,text}` option
  - `OutputMode` class for intelligent TTY detection
  - JSON output for programmatic use (third-party integration)
  - Text output for human readability

- **CLI Progress Improvements**:
  - `BatchProgressDisplay` class for multi-file progress tracking
  - TTY detection for automatic mode switching
  - Quiet mode (`-q, --quiet`) for minimal output
  - Summary statistics at batch download completion

- **CLI Exit Codes**: Well-defined exit codes for scripting
  - `0` Success, `1` General error, `2` Invalid argument, `3` Retry failed, `4` Cancelled

- **CLI Version Option**: `--version` flag for version information

### Changed

- Refactored callback adapters to reduce code duplication (`_detect_callback_mode()`)
- Split `__post_init__` validation in `DownloadConfig` into separate methods
- Improved exception handling specificity in `H2MultiPlexDownloader.download_chunk()`
- Added `_chunk_index_map` for O(1) chunk lookup in `ChunkManager`
- Removed duplicate `DirectFileWriter` class (already existed in `writer.py`)
- Updated `apply_style()` type signature to accept `DownloadStyle | str`

### Documentation

- Added comprehensive CLI documentation (`docs/en/cli/index.md`, `docs/zh/cli/index.md`)
- Updated `mkdocs.yml` navigation structure

## 0.3.0 - 2026-03-28

### Added

- **Multi-Source Manager**: Robust multiple URL downloading
  - Dynamic `MultiSourceManager` with reliable automatic failover control
  - P2P style multiple backup URL capability
- **Content-Aware File Reuse**: Skip downloading files that already exist
  - Introduces `FileReuseChecker` using file signatures and rapid hashing techniques
  - Pre-verifications and incremental block hashing matching across the entire directory
  - Integration with `SharedFileRegistry` to eliminate concurrent duplicate task fetching
- **Intelligent Strategy Overhaul**: Upgraded underlying download strategy assignment algorithms
  - `StrategySelector` class for profiling resources and adapting download methodology based strictly on dynamic evaluations (e.g., file sizes, server capabilities)
  - `DynamicStyleAllocator` efficiently handles download styles across batch sessions combining concurrency and network capacity
- **Hybrid Turbo Strategy Implementation**: Introducing AIMD logic to scheduling
  - Exposed advanced congestion control parameters (Increase Step, Decrease Factor, Speedup Threshold) in `DownloadConfig`
  - Integrated multiplicative decrease (`hybrid_aimd_decrease_factor`) mechanics on severe drops mimicking aggressive network fetchers like IDM/aria2
  - Exposed direct configuration mutation function `apply_style` within the configuration object

### Changed

- Enhanced global connection and thread pooling via `GlobalThreadPool` and `SpeedAdaptiveController`
- Migrated AIMD step settings mapping code correctly out of internal CLI parsers and strictly into API objects

## 0.2.0 - 2026-03-28

### Added

- **Batch Download Mode**: Multi-file parallel download support
  - `BatchDownloader` class: Complete batch download control
  - `batch_download_sync` / `batch_download` convenience functions
  - `FileScheduler`: Adaptive file scheduler
  - `AdaptiveConcurrencyController`: Adaptive concurrency controller
  - `BatchProgress`: Batch progress tracking
  - `FileTask`: Single file task encapsulation

### Optimizations

- Shared connection pool for batch downloads, reducing connection overhead
- Parallel HEAD requests for batch file info probing
- Fixed adaptive concurrency logic: increase concurrency when speed drops to utilize bandwidth
- `Downloader` supports external connection pool injection

### Features

- **Small File Priority**: Auto-identify and prioritize small files
- **Smart Chunking**: Auto-select optimal chunk count based on file size
  - Small files (<5MB): Single chunk
  - Medium files (5MB~100MB): 4 chunks
  - Large files (>100MB): 8 chunks
- **Progress Callbacks**: Batch overall progress and per-file completion callbacks
- **Pause/Resume/Cancel**: Complete download control

## 0.1.0 - 2026-03-28

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
