# littledl 文档

欢迎使用 littledl —— 高性能文件下载库与命令行工具，专注单文件与批量下载，支持基于 HTTP Range 的分块下载、断点续传、自适应调度与丰富的回调体系。

```python
from littledl import download_file_sync

path = download_file_sync("https://example.com/file.zip")
print(f"下载至: {path}")
```

## 为什么选择 littledl

- **又快又稳的 FUSION 调度**：四阶段自适应（探测 → 爬升 → 巡航 → 收尾），带带宽天花板估算与边际收益检测；巡航期锁定并发、平滑判断，像 IDM 一样平稳，而非锯齿抖动
- **智能策略选择**：根据文件大小、服务器能力与网络状况自动选择下载风格（single / multi / adaptive / fusion / hybrid_turbo），无需手动调参
- **多线程分块下载**：基于 HTTP Range 的分段并发，自动识别慢块并在收尾阶段抢占，最大化带宽利用
- **原子化写入，永不损坏**：分块数据写入预分配的 `.part` 文件，定位写入由锁串行化，成功后原子重命名；中途失败不会破坏已有文件
- **可靠的断点续传**：精确还原分片字节区间（含重切分片），续传前校验 ETag/Last-Modified 兼容性
- **实时进度回调**：统一回调系统自动适配 event / dict / kwargs / legacy 四种签名，速度、ETA、分片状态实时可查
- **企业级特性**：认证（Basic / Bearer / Digest / API Key / OAuth2）、代理（系统 / 自定义 / SOCKS5）、限速、哈希校验、文件复用与多源故障切换
- **自动降级**：分块传输不可行时自动回退单流模式，保证可用性

## 入门指南

- [快速入门](getting-started/index.md) - 安装与首个下载
- [安装](getting-started/index.md#安装) - 安装说明

## 用户指南

- [配置指南](configuration/index.md) - 配置选项
- [认证设置](authentication/index.md) - 认证设置
- [代理配置](proxy/index.md) - 代理配置
- [错误处理](error-handling/index.md) - 错误处理和重试

## 高级主题

- [高级用法](advanced/index.md) - 高级功能和优化
- [批量下载](batch-download/index.md) - 多文件批量下载
- [命令行工具](cli/index.md) - CLI 用法
- [API 参考](api-reference/index.md) - 完整的 API 参考

## 其他

- [贡献指南](../../CONTRIBUTING.zh.md) - 贡献指南
- [变更日志](../../CHANGELOG.zh.md) - 版本历史
- [安全政策](../../SECURITY.zh.md) - 安全政策
