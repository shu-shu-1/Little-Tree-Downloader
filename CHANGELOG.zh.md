English | 简体中文

# 变更日志

本文档记录 littledl 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

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
