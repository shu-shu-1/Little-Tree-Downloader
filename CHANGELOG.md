English | [简体中文](CHANGELOG.zh.md)

# Changelog

All notable changes to littledl will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed

- **Documentation Refresh for FUSION**: Updated English docs to reflect `fusion` as the default CLI/download style and clarified that `auto` is now an alias of `fusion`
- **Batch Download Documentation**: Documented global chunk budgeting, domain-affinity scheduling, and corrected adaptive concurrency behavior descriptions
- **Configuration/API Documentation**: Added `enable_fusion`, key `fusion_*` settings, and the `DownloadConfig.create_file_config()` helper to the docs

### Fixed

- **README Examples**: Corrected outdated style-selection examples so they match the current `StrategySelector` API and FUSION-based defaults

## 0.9.0 - 2026-04-12

### Added

- **FUSION Adaptive Scheduler**: Added a new four-phase adaptive scheduling algorithm for chunked downloads
  - Introduced `FusionScheduler` with `PROBE -> RAMP -> CRUISE -> TAIL` phases
  - Added `DownloadStyle.FUSION` and exported `FusionScheduler` from the top-level package
  - Added dedicated FUSION tuning parameters to `DownloadConfig` for probe, ramp, cruise, and tail behavior
- **Per-File Config Cloning API**: Added `DownloadConfig.create_file_config()` so batch downloads can inherit the full parent configuration safely
- **Batch Chunk Budget Control**: Added `FileScheduler.max_total_chunks` and active chunk tracking to cap total chunk fan-out across batch tasks

### Changed

- **FUSION Becomes Default Style**: FUSION is now the default strategy for CLI and automatic style selection
  - CLI `--style` now supports `fusion`
  - CLI default style changed from `hybrid_turbo` to `fusion`
  - `auto` style now maps to `fusion`
- **Strategy Selection Updates**: `StrategySelector` now prefers FUSION for medium and large files, with updated chunk heuristics for fast and unstable networks
- **Downloader Scheduler Selection**: `Downloader` now chooses `FusionScheduler` automatically when FUSION is enabled, including temporary tail-phase worker expansion
- **Batch Scheduling Efficiency**: Batch downloads now balance per-file chunk counts against a global chunk budget to reduce over-allocation under heavy workloads

### Fixed

- **Batch Per-File Config Propagation**: Fixed batch per-file downloader creation so advanced options such as FUSION, adaptive tuning, resplit parameters, speed limits, auth, and proxy settings are preserved
- **Adaptive Concurrency Direction Logic**: Fixed `AdaptiveConcurrencyController.adjust()` so it increases concurrency on strong positive trends and decreases it on negative trends instead of reacting in the wrong direction
- **Dynamic Style Priority Sorting**: Fixed `DynamicStyleAllocator.rebalance()` sorting keys so file size and priority are evaluated correctly during allocation
- **Tail Resplit Bookkeeping**: Improved FUSION tail-phase resplit bookkeeping so repeated resplits are tracked correctly and stay bounded

### Documentation

- Updated CLI documentation examples to reflect version `0.9.0`
- Updated `llms.txt` package version metadata for agent-facing project indexing

## 0.8.0 - 2026-04-11

### Added

- **Unified Callback API Exports**: Exported callback building blocks from the top-level package for downloader integrators
  - Added `EventType`, `BaseProgressEvent`, `FileProgressEvent`, `FileCompleteEvent`, `ChunkProgressEvent`, and `BatchProgressEvent`
  - Added `UnifiedCallbackAdapter`, `ThrottledCallback`, `CallbackChain`, `ProgressAggregator`, and `detect_callback_mode`
- **CLI Adaptive Batch Concurrency**: Added automatic batch concurrency selection tuned by workload size and connection pool limits
  - `--max-concurrent` now supports `0 = auto`
  - Added `--auto-concurrency` and `--no-auto-concurrency`
- **Rich Batch Progress UI**: Added optional Rich-powered live batch display with graceful fallback to plain text when Rich or TTY support is unavailable

### Changed

- **Progress Callback Context**: `ProgressEvent` now includes `filename` and `url`, making it easier to build custom downloaders and UI layers without external state tracking
- **CLI Callback Integration**: Single-file CLI progress now consumes `ProgressEvent`; batch CLI progress now consumes `BatchProgress` directly instead of per-file positional callbacks
- **Batch Scheduler Optimizations**: Improved multi-file throughput with domain-aware scheduling and better startup behavior
  - Added domain affinity for pending task selection
  - Added hot-domain prewarming before batch downloads
  - Added small-file-heavy concurrency boost heuristics
- **Dependency Layout**: `rich` is now part of the main runtime dependencies so the enhanced CLI UI is available out of the box

### Fixed

- **Single File Output Path Resolution**: Fixed suffixless output paths such as `./downloads` being mistaken for a file path during single-file downloads
- **Chunk Retry Range Handling**: Fixed retry logic to rebuild `Range` headers correctly after partial chunk failures
- **Dynamic Chunk Resplit Execution**: Fixed chunked downloads so newly resplit chunks are scheduled and downloaded during the same run instead of being skipped
- **Chunk State Bookkeeping**: Improved `ChunkManager` completion and status tracking for resplit, failed, and completed chunks
- **Shared Connection Pool Cleanup**: Fixed `Downloader` cleanup so externally injected/shared pools are not closed accidentally in batch scenarios
- **Single-Stream Speed Limiting**: Fixed single-stream downloads so they also respect configured speed limits
- **Safer Final File Move**: Added a fallback move path when temp file rename fails on Windows or cross-device situations
- **Speed History Tracking**: Fixed `SpeedMonitor` history recording so stability and smoothing calculations have real data to work with
- **Buffered Writer Compatibility**: Fixed `BufferedFileWriter` startup in environments where `fileno()` is unavailable or unsupported

### Documentation

- Updated English and Chinese getting-started docs with progress callback examples
- Expanded English and Chinese API reference with unified callback system types and `ProgressEvent` file context fields
- Reorganized `llms.txt` into a concise task-oriented index for LLM and agent consumption

## 0.7.0 - 2026-03-29

### Fixed

- **Batch Progress Callback Fix**: Fixed `BatchProgressCallbackAdapter._detect_mode()` to correctly recognize 4-parameter callbacks `(task_id, downloaded, total, speed)` as FILE_PROGRESS mode instead of misclassifying as LEGACY_5_PARAM
- **FileTask Progress Sync**: Fixed `BatchDownloader._download_single_file()` and `EnhancedBatchDownloader._download_single_file()` to properly sync progress via `ProgressAggregator`

### Changed

- **Speed Stability Improvements in GlobalThreadPool**: Made thread appending logic more conservative
  - `should_append_thread()` now requires 4+ consecutive low-speed predictions (was 2+)
  - Added variance check: won't append if variance > 0.5 (network unstable)
  - `ewma_alpha` changed from 0.3 to 0.15 for smoother speed tracking
  - `_predict_next_speed()` now uses dynamic stability weight based on variance
- **SpeedMonitor EWMA Improvements**: Better speed smoothing for more stable ETA
  - Window size increased from 10 to 20 for more history
  - `MovingAverage` window from 5 to 10
  - Added EWMA smoothing with `_ewma_alpha = 0.15`
  - `smoothed_speed` now uses EWMA instead of simple average
- **Algorithm Optimizations**: Enhanced download efficiency with smarter scheduling
  - **GlobalThreadPool**: Increased speed history to 30 samples, dual MovingAverage tracking (10 + 20 windows), variance caching for performance, improved speed prediction with EWMA mixing
  - **SpeedMonitor**: Hybrid speed calculation (30% instant + 70% EWMA), adaptive alpha based on network conditions
  - **FileScheduler**: Dynamic chunk allocation based on network speed and stability, target ~3s chunk download time
  - **AdaptiveConcurrencyController**: Increased history to 20 samples, proper EWMA smoothing, magnitude-based adjustments, trend-based concurrency control
  - **ChunkManager**: Lowered resplit cutoff from 90% to 75%, added speed-based veto (won't resplit fast chunks), variable split count support
  - **SmartScheduler**: EWMA-based speed gain calculation, process sqrt(total_chunks) slow chunks per cycle, cross-chunk coordination hints

## 0.6.1 - 2026-03-29

### Added

- **Dual Progress Mode for Batch Download**: Provides both byte-based and file-based progress
  - `BatchProgress.progress` - byte-based progress (`downloaded_bytes / total_bytes`)
  - `BatchProgress.files_progress` - file-based progress (`completed_files / total_files`)
  - Callback payload now includes `files_progress` field for dict/kwargs modes

### Changed

- `BatchProgress.files_completed_ratio` property renamed to `files_progress` for consistency

## 0.6.0 - 2026-03-29

### Added

- **Pre-connection Mechanism**: Pre-establish HTTP/2 connections before download starts

  - `ConnectionPool.preconnect()` method for batch pre-warming TLS connections
  - Reduces first-request latency for multiple downloads
- **Direct Write Path (sendfile)**: High-performance file writing for large sequential data

  - `BufferedFileWriter.direct_write_threshold` - 256KB threshold for direct os.pwrite
  - Bypasses Python I/O layer for zero-copy writes
  - Reduces CPU overhead for large chunk downloads

### Changed

- **Increased Default Concurrency**: Better throughput out of the box

  - `max_concurrent_files` default: 5 → 8 (4 locations updated)
  - `FileScheduler`, `BatchDownloader`, `EnhancedBatchDownloader`, `AdaptiveStrategySelector`
- **Larger Write Buffer**: Reduced system call overhead

  - `BufferedFileWriter.buffer_size`: 512KB → 1MB
  - `H2MultiPlexDownloader` default buffer: 64KB → 1MB

## 0.5.0 - 2026-03-29

### Added

- **Enhanced Batch Progress Callback System**: High-performance, standardized, and customizable callbacks

  - `BatchProgressCallbackAdapter` - Normalizes different callback styles (event, dict, kwargs, legacy)
  - `FileProgress` dataclass - Individual file progress information
  - `BatchProgress` now includes `files` tuple for per-file details
- **Improved Speed Calculation**: More accurate ETA prediction in multi-file download mode

  - Added `smooth_speed` - Smoothed speed using exponential weighted average
  - Added `speed_stability` - Metric indicating ETA reliability (0.0-1.0)
  - Added `pending_files` and `elapsed_time` fields to `BatchProgress`
  - Speed history tracking in `FileScheduler` for stable calculations
- **Per-File Progress Visibility**: See which files are downloading and their individual progress

  - `BatchProgress.files` contains `FileProgress` tuple for all files
  - Helper methods: `get_active_files()`, `get_pending_files()`, `get_completed_files()`, `get_failed_files()`
  - Each `FileProgress` includes: task_id, filename, url, status, file_size, downloaded, speed, progress, error, started_at, completed_at
- **MovingAverage Utility Enhancements**: Better speed averaging

  - `get_weighted_average()` - Exponential weighted average
  - `get_median()` - Median calculation to reduce outlier impact
  - `get_smoothed_average()` - EMA smoothing
  - `get_stability()` / `is_stable()` - Speed stability metrics

### Changed

- `BatchDownloader.set_progress_callback()` now wraps callbacks with `BatchProgressCallbackAdapter`
- `EnhancedBatchDownloader.set_progress_callback()` now wraps callbacks with `BatchProgressCallbackAdapter`
- Progress callbacks now receive `BatchProgress` object (standardized format)
- Legacy 5-argument callbacks still supported via automatic detection

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
