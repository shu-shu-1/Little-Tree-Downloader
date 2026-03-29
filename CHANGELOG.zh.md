English | 简体中文

# 变更日志

本文档记录 littledl 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

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
