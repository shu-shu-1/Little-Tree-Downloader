English | 简体中文

# 变更日志

本文档记录 littledl 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/spec/v2.0.0.html)。

## [0.1.0] - 2024-01-XX

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