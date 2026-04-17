English | 简体中文

# 变更日志

本文档记录 littledl 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

## 0.9.1 - 2026-04-17

### 优化变更

- **FUSION 文档刷新**：更新中文文档，明确 `fusion` 已是 CLI 和下载策略的默认模式，并说明 `auto` 现在是 `fusion` 的兼容别名
- **批量下载文档补充**：补充全局分块预算、域名亲和调度，并修正文档中对自适应并发行为的描述
- **配置/API 文档补充**：补充 `enable_fusion`、关键 `fusion_*` 参数，以及 `DownloadConfig.create_file_config()` 帮助方法说明

### 修复

- **README 示例修正**：修正文档中过时的风格选择示例，使其与当前 `StrategySelector` API 和基于 FUSION 的默认行为一致

## 0.9.0 - 2026-04-12

### 新增

- **FUSION 自适应调度器**：新增四阶段分块调度算法，用于进一步提升分块下载的速度与稳定性
  - 引入 `FusionScheduler`，包含 `PROBE -> RAMP -> CRUISE -> TAIL` 四个阶段
  - 新增 `DownloadStyle.FUSION`，并从顶层包导出 `FusionScheduler`
  - 为 `DownloadConfig` 新增 FUSION 专属参数，可分别控制探测、爬升、巡航和收尾阶段行为
- **单文件配置克隆 API**：新增 `DownloadConfig.create_file_config()`，让批量下载中的单文件任务能够安全继承完整父配置
- **批量总分块预算控制**：为 `FileScheduler` 新增 `max_total_chunks` 和活动分块统计，用于限制批量任务的总分块扩张

### 优化变更

- **FUSION 成为默认风格**：FUSION 现在是 CLI 与自动策略选择的默认下载风格
  - CLI `--style` 新增 `fusion`
  - CLI 默认风格从 `hybrid_turbo` 调整为 `fusion`
  - `auto` 现在映射到 `fusion`
- **策略选择更新**：`StrategySelector` 现在优先为中大文件选择 FUSION，并根据高速稳定网络或不稳定网络调整推荐分块数
- **下载器调度器选择**：当启用 FUSION 时，`Downloader` 会自动切换到 `FusionScheduler`，并在收尾阶段允许临时扩大 worker 并发
- **批量调度效率提升**：批量下载会在全局分块预算下平衡每个文件的分块数，降低高负载场景下的过度分块

### 修复

- **批量单文件配置继承**：修复批量下载为单文件任务创建下载器时丢失高级配置的问题，FUSION、自适应调优、重切分参数、限速、认证、代理等设置现在都会正确保留
- **自适应并发方向判断**：修复 `AdaptiveConcurrencyController.adjust()` 趋势方向判断相反的问题，现在会在速度趋势明显向上时提高并发、在趋势下滑时降低并发
- **动态风格优先级排序**：修复 `DynamicStyleAllocator.rebalance()` 中排序键使用错误，确保按文件体积特征与优先级正确分配风格
- **收尾阶段重切分统计**：改进 FUSION 收尾阶段的重切分计数与状态记录，避免重复重切失控

### 文档

- 更新 CLI 文档示例中的版本号为 `0.9.0`
- 更新 `llms.txt` 中面向 agent 的项目版本元数据

## 0.8.0 - 2026-04-11

### 新增

- **统一回调 API 导出**：为使用 littledl 构建下载器或上层 UI 的场景，直接从顶层包导出回调相关基础类型
  - 新增 `EventType`、`BaseProgressEvent`、`FileProgressEvent`、`FileCompleteEvent`、`ChunkProgressEvent`、`BatchProgressEvent`
  - 新增 `UnifiedCallbackAdapter`、`ThrottledCallback`、`CallbackChain`、`ProgressAggregator`、`detect_callback_mode`
- **CLI 批量自适应并发**：新增基于任务规模和连接池上限的批量下载自动并发选择
  - `--max-concurrent` 现在支持 `0 = auto`
  - 新增 `--auto-concurrency` 与 `--no-auto-concurrency`
- **Rich 批量进度界面**：新增可选的 Rich 实时批量进度显示，并在没有 Rich 或非 TTY 环境下自动回退到纯文本输出

### 优化变更

- **进度回调上下文增强**：`ProgressEvent` 现在包含 `filename` 和 `url`，上层构建下载器、进度面板或日志系统时无需再额外维护文件上下文
- **CLI 回调集成优化**：单文件 CLI 进度改为直接消费 `ProgressEvent`；批量 CLI 进度改为直接消费 `BatchProgress`，不再依赖逐文件位置参数回调
- **批量调度优化**：通过域名感知调度和更合理的启动阶段处理提升多文件下载吞吐
  - 新增基于域名亲和性的待下载任务选择
  - 新增批量下载前的热点域名预热连接
  - 新增小文件占比高时的并发提升启发式策略
- **依赖调整**：`rich` 进入主运行时依赖，增强型 CLI 界面开箱即用

### 修复

- **单文件输出路径判断**：修复单文件下载时 `./downloads` 这类无后缀输出路径被错误当成文件路径的问题
- **分块重试 Range 处理**：修复分块失败后重试时 `Range` 请求头计算不正确的问题
- **动态重切分块执行**：修复分块下载过程中新增的重切分块没有在同一次任务中被继续调度和下载的问题
- **分块状态统计与完成判断**：加强 `ChunkManager` 对重切、失败、完成分块的状态维护与完成判断
- **共享连接池清理**：修复批量场景下 `Downloader` 意外关闭外部注入/共享连接池的问题
- **单流下载限速**：修复单连接下载路径未应用配置限速的问题
- **最终文件移动兜底**：当临时文件重命名失败时增加安全回退移动逻辑，提升 Windows 和跨设备场景兼容性
- **速度历史记录**：修复 `SpeedMonitor` 未正确记录速度历史导致稳定性与平滑计算依据不足的问题
- **缓冲写入器兼容性**：修复 `BufferedFileWriter` 在 `fileno()` 不可用环境下初始化失败的问题

### 文档

- 更新中英文快速入门文档，补充进度回调示例
- 扩展中英文 API 参考文档，补充统一回调系统类型和 `ProgressEvent` 文件上下文字段
- 将 `llms.txt` 重组为更适合 LLM / agent 消费的任务导向索引

## 0.7.0 - 2026-03-29

### 修复

- **批量进度回调修复**: 修复 `BatchProgressCallbackAdapter._detect_mode()` 错误地将 4 参数回调 `(task_id, downloaded, total, speed)` 识别为 LEGACY_5_PARAM 模式的问题，正确识别为 FILE_PROGRESS 模式
- **FileTask 进度同步修复**: 修复 `BatchDownloader._download_single_file()` 和 `EnhancedBatchDownloader._download_single_file()` 通过 `ProgressAggregator` 正确同步进度

### 优化变更

- **GlobalThreadPool 速度稳定性提升**: 线程追加逻辑更加保守
  - `should_append_thread()` 现在要求 4+ 次连续低速预测（原来为 2+）
  - 新增方差检查：方差 > 0.5 时不追加线程（网络不稳定）
  - `ewma_alpha` 从 0.3 改为 0.15 以获得更平滑的速度跟踪
  - `_predict_next_speed()` 现在使用基于方差的动态稳定性权重
- **SpeedMonitor EWMA 优化**: 更好的速度平滑以获得更稳定的 ETA
  - 窗口大小从 10 增加到 20 以获取更多历史数据
  - `MovingAverage` 窗口从 5 增加到 10
  - 新增 EWMA 平滑 `_ewma_alpha = 0.15`
  - `smoothed_speed` 现在使用 EWMA 而不是简单平均
- **算法优化**: 增强下载效率，更智能的调度
  - **GlobalThreadPool**: 速度历史增加到 30 个样本，双 MovingAverage 跟踪（10 + 20 窗口），方差缓存提升性能，基于 EWMA 混合的改进速度预测
  - **SpeedMonitor**: 混合速度计算（30% 即时 + 70% EWMA），基于网络条件的自适应 alpha
  - **FileScheduler**: 基于网络速度和稳定性的动态分片分配，目标分片下载时间约 3 秒
  - **AdaptiveConcurrencyController**: 历史样本增加到 20，适当的 EWMA 平滑，基于幅度的调整，基于趋势的并发控制
  - **ChunkManager**: 将重新分割阈值从 90% 降低到 75%，添加基于速度的否决（不会重新分割快速分片），支持可变分割数量
  - **SmartScheduler**: 基于 EWMA 的速度增益计算，每周期处理 sqrt(总分片数) 个慢分片，跨分片协调提示

## 0.6.1 - 2026-03-29

### 新增

- **批量下载双进度模式**：提供字节和文件数两种进度计算方式
  - `BatchProgress.progress` - 按字节进度 (`downloaded_bytes / total_bytes`)
  - `BatchProgress.files_progress` - 按文件数进度 (`completed_files / total_files`)
  - 回调 payload 现在包含 `files_progress` 字段（dict/kwargs 模式）

### 优化变更

- `BatchProgress.files_completed_ratio` 属性改名为 `files_progress` 保持一致性

## 0.6.0 - 2026-03-29

### 新增

- **预连接机制**：下载开始前预建立 HTTP/2 连接

  - `ConnectionPool.preconnect()` 方法批量预热 TLS 连接
  - 减少多文件下载的首请求延迟
- **直接写入路径 (sendfile)**：大块顺序数据的高性能写入

  - `BufferedFileWriter.direct_write_threshold` - 256KB 阈值触发直接 os.pwrite
  - 绕过 Python I/O 层实现零拷贝写入
  - 减少大块分片下载的 CPU 开销

### 优化变更

- **默认并发数提升**：开箱即用更好的吞吐

  - `max_concurrent_files` 默认值：5 → 8（4 处更新）
  - `FileScheduler`、`BatchDownloader`、`EnhancedBatchDownloader`、`AdaptiveStrategySelector`
- **更大的写入缓冲区**：减少系统调用开销

  - `BufferedFileWriter.buffer_size`：512KB → 1MB
  - `H2MultiPlexDownloader` 默认 buffer：64KB → 1MB

## 0.5.0 - 2026-03-29

### 新增

- **增强的批量进度回调系统**：高性能、标准化、可定制化的回调

  - `BatchProgressCallbackAdapter` - 标准化不同回调风格（事件、字典、关键字参数、传统格式）
  - `FileProgress` 数据类 - 单文件进度信息
  - `BatchProgress` 新增 `files` 元组，包含每个文件的详细信息
- **改进的速度计算**：多文件下载模式下更准确的 ETA 预测

  - 新增 `smooth_speed` - 使用指数加权平均的平滑速度
  - 新增 `speed_stability` - 指示 ETA 可靠性的指标（0.0-1.0）
  - 新增 `pending_files` 和 `elapsed_time` 字段
  - `FileScheduler` 中的速度历史跟踪，确保稳定计算
- **单文件进度可见性**：查看正在下载的文件及其各自进度

  - `BatchProgress.files` 包含所有文件的 `FileProgress` 元组
  - 辅助方法：`get_active_files()`、`get_pending_files()`、`get_completed_files()`、`get_failed_files()`
  - 每个 `FileProgress` 包含：task_id、filename、url、status、file_size、downloaded、speed、progress、error、started_at、completed_at
- **MovingAverage 工具增强**：更好的速度平均计算

  - `get_weighted_average()` - 指数加权平均
  - `get_median()` - 中位数计算，减少异常值影响
  - `get_smoothed_average()` - EMA 平滑
  - `get_stability()` / `is_stable()` - 速度稳定性指标

### 优化变更

- `BatchDownloader.set_progress_callback()` 现在使用 `BatchProgressCallbackAdapter` 包装回调
- `EnhancedBatchDownloader.set_progress_callback()` 现在使用 `BatchProgressCallbackAdapter` 包装回调
- 进度回调现在接收 `BatchProgress` 对象（标准化格式）
- 通过自动检测仍支持传统的 5 参数回调

## 0.4.1 - 2026-03-29

### 修复

- 修复 `probe_url` 中 `httpx.Timeout` 缺少 `write` 和 `pool` 参数
- 修复 `run_download` 中在已有事件循环中调用 `asyncio.run()` 的问题
- 修复服务器未发送 `Content-Disposition` 时文件名回退逻辑（CDN 下载默认变成 `download.bin` 的问题）
- 修复 `--temp-dir` CLI 选项未连接到 `DownloadConfig`

### 新增

- `--temp-dir` CLI 选项：指定临时文件目录

## 0.4.0 - 2026-03-29

### 新增

- **CLI 批量下载支持**：完整的批量文件下载功能

  - `-F, --batch-file` 选项：从文本文件读取 URL 进行批量下载
  - `--max-concurrent` 选项：控制并发下载数量
  - `read_urls_from_file()` 函数：支持验证和注释行处理
- **CLI 输出格式控制**：多种输出模式适应不同使用场景

  - `--output-format {auto,json,text}` 选项
  - `OutputMode` 类：智能 TTY 检测
  - JSON 输出：程序化调用（第三方集成）
  - 文本输出：人类可读
- **CLI 进度显示改进**：

  - `BatchProgressDisplay` 类：多文件进度追踪
  - TTY 检测自动切换模式
  - 安静模式 (`-q, --quiet`)：最小化输出
  - 批量下载完成时显示统计摘要
- **CLI 退出码**：为脚本处理定义的退出码

  - `0` 成功、`1` 一般错误、`2` 参数无效、`3` 重试失败、`4` 用户取消
- **CLI 版本选项**：`--version` 显示版本信息

### 优化变更

- 重构 callback adapters，提取 `_detect_callback_mode()` 消除重复代码
- 将 `DownloadConfig.__post_init__` 验证逻辑拆分为独立方法
- 改进 `H2MultiPlexDownloader.download_chunk()` 异常处理的具体性
- `ChunkManager` 添加 `_chunk_index_map` 实现 O(1) 分块查找
- 删除重复的 `DirectFileWriter` 类（已存在于 `writer.py`）
- 更新 `apply_style()` 类型签名以接受 `DownloadStyle | str`

### 文档

- 新增完整 CLI 文档（`docs/en/cli/index.md`、`docs/zh/cli/index.md`）
- 更新 `mkdocs.yml` 导航结构

## 0.3.0 - 2026-03-28

### 新增

- **多源下载管理器 (Multi-Source Manager)**：增强多备份链接的调度可靠性
  - 动态集成了自动故障转移和错误重切处理机制
- **内容感知的文件复用判定 (Content-Aware File Reuse)**：跳过当前系统中已经被下载过的相同资源
  - 引入 `FileReuseChecker` 组件，通过文件签名与快速增量哈希匹配实现重复探测
  - 新增 `SharedFileRegistry` 全局文件注册表模块来同步与剔除批量下载中同时发起的重复网络请求
- **重构智能策略选择 (Intelligent Strategy)**：算法指派与自适应调度进化
  - 设计 `StrategySelector` 以精确处理网络能力档案并赋予资源最佳调度风格及分块参数
  - 推出对于多个文件下载会话中并发生态调频专用的 `DynamicStyleAllocator` (动态策略分配器)
- **混合提升模式 (HYBRID_TURBO / AIMD 算法)**：通过高级别拥塞控制进一步榨干宽带
  - 将 AIMD 加性增与乘性减退避算法 (Multiplicative Decrease / Additive Increase) 参数正式开放到了 `DownloadConfig` 对象
  - 在配置类上新增公开的 `apply_style("HYBRID_TURBO")` 实例方法，用于对调用代码或 CLI 一键全量激活底层高级别参数。

### 优化变更

- 通过 `GlobalThreadPool` 与 `SpeedAdaptiveController` 统筹连接与线程资源，降低系统开销与内存压力
- 调整并修正了 AIMD 在速度降级情况下的线性相减为合乎预期的比例惩罚(Factor级修正调度) 逻辑

## 0.2.0 - 2026-03-28

### 新增

- **批量下载模式**：支持多文件并行下载
  - `BatchDownloader` 类：完整的批量下载控制
  - `batch_download_sync` / `batch_download` 便捷函数
  - `FileScheduler`：自适应文件调度器
  - `AdaptiveConcurrencyController`：自适应并发控制器
  - `BatchProgress`：批量下载进度追踪
  - `FileTask`：单文件任务封装

### 优化

- 批量下载时共享连接池，减少连接建立开销
- 批量 HEAD 请求并行探测文件信息
- 自适应并发逻辑修复：速度下降时增加并发以利用带宽
- `Downloader` 支持外部传入连接池

### 特性

- **小文件优先策略**：自动识别小文件并优先处理
- **智能分块**：根据文件大小自动选择最优分块数
  - 小文件（<5MB）：单分块
  - 中等文件（5MB~100MB）：4分块
  - 大文件（>100MB）：8分块
- **进度回调**：支持批量整体进度和单文件完成回调
- **暂停/恢复/取消**：完整的下载控制

## 0.1.0 - 2026-03-28

### 新增

- IDM 风格的多线程分块下载
- 智能调度（慢分块检测和重分配）
- 断点续传（分块级别进度跟踪）
- 实时速度监控
- 自适应并发调整
- HTTP/2 连接池
- 进度回调支持
- 丰富的配置选项
- 全面的错误处理
- 文件完整性验证（SHA256、MD5）
- 自动文件名检测

### 功能

- **多线程下载**：分块并行下载
- **智能调度**：智能分块重分配优化速度
- **断点续传**：无缝继续中断的下载
- **速度监控**：实时速度计算和预计剩余时间
- **自适应调度**：根据网络状况动态调整
- **连接管理**：高效的 HTTP 连接复用

### 支持的平台

- Windows 10/11
- macOS 10.15+
- Linux (Ubuntu 20.04+, Debian 11+, Fedora 35+)
- FreeBSD 13+

[0.1.0]: https://github.com/little-tree/little-tree-downloader/releases/tag/v0.1.0
