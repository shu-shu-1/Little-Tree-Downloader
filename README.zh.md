English | [简体中文](README.zh.md)

# littledl

高性能下载库，支持 aria2 风格的多线程分段下载、智能策略选择和自适应优化。

## 特性

### 核心功能
- 🚀 **Aria2 风格多线程分段下载**：使用 HTTP Range 请求将文件分块并行下载，最大化速度
- 🧠 **智能策略选择**：根据文件大小、服务器能力和网络状况自动选择最优下载风格（单线程/多线程/自适应）
- 🎯 **直接写入文件**：直接写入最终文件，无需临时文件合并
- ⏯️ **断点续传**：支持从上次中断处继续下载
- 📊 **实时速度监控**：实时速度计算、预计剩余时间和趋势分析
- 🔁 **可靠回退**：分块下载失败时自动回退到单连接下载

### 高级功能
- 🔐 **多种认证方式**：Basic、Bearer、Digest、API Key、OAuth2
- 🌐 **完整代理支持**：系统代理自动检测、PAC 文件、SOCKS5
- ⏱️ **速度限制**：令牌桶、漏桶和自适应算法
- ✅ **完整性校验**：支持下载后哈希校验（`verify_hash`、`expected_hash`）
- 🔍 **服务器检测**：自动检测服务器能力以优化下载策略
- 💾 **文件复用**：内容感知匹配，复用已有文件节省带宽
- 🔄 **多源备份**：支持多个备用 URL，故障自动切换
- 💻 **跨平台**：Windows、macOS、Linux、FreeBSD
- 🔒 **安全**：SSL 验证，安全路径处理

## 安装

```bash
pip install littledl
```

或使用 uv：

```bash
uv add littledl
```

## 文档

完整的文档请参阅 [https://littledl.zsxiaoshu.cn/](https://littledl.zsxiaoshu.cn/)

- [快速入门](https://littledl.zsxiaoshu.cn/zh/getting-started/) - 快速入门指南
- [配置指南](https://littledl.zsxiaoshu.cn/zh/configuration/) - 配置选项
- [批量下载](https://littledl.zsxiaoshu.cn/zh/batch-download/) - 多文件批量下载
- [代理配置](https://littledl.zsxiaoshu.cn/zh/proxy/) - 代理配置
- [错误处理](https://littledl.zsxiaoshu.cn/zh/error-handling/) - 错误处理
- [高级用法](https://littledl.zsxiaoshu.cn/zh/advanced/) - 高级功能
- [API 参考](https://littledl.zsxiaoshu.cn/zh/api-reference/) - 完整的 API 参考

## 快速开始

### 基本用法

```python
from littledl import download_file_sync

path = download_file_sync("https://example.com/large_file.zip")
print(f"保存至: {path}")
```

### 异步用法

```python
import asyncio
from littledl import download_file

async def main():
    path = await download_file(
        "https://example.com/large_file.zip",
        save_path="./downloads",
        filename="my_file.zip",
    )
    print(f"保存至: {path}")

asyncio.run(main())
```

## 下载风格

littledl 支持三种下载风格，您可以根据需要选择：

| 风格 | 说明 | 适用场景 |
|------|------|---------|
| `single` | 单线程下载 | 小文件、不支持 Range 的服务器 |
| `multi` | 多线程分段下载（aria2 风格） | 大文件、稳定网络 |
| `adaptive` | 自动选择最优风格 | 大多数场景 |

### 自动风格选择（推荐）

```bash
littledl "https://example.com/file.zip" --style adaptive
```

```python
from littledl import DownloadStyle

# 根据文件和网络自动选择
config = DownloadConfig()
# 系统自动选择最优风格
```

### 手动风格选择

```bash
# 强制单线程
littledl "https://example.com/file.zip" --style single

# 强制多线程
littledl "https://example.com/file.zip" --style multi --max-chunks 8
```

```python
from littledl import StrategySelector, DownloadStyle

selector = StrategySelector(
    default_style=DownloadStyle.MULTI,
    enable_single=True,
    enable_multi=True,
)
```

### 下载前分析

使用 `--info` 参数分析并获取下载策略建议：

```bash
littledl "https://example.com/large_file.zip" --info
```

输出：
```
文件信息:
  文件名: large_file.zip
  大小: 1.5 GB
  内容类型: application/zip
  断点续传: 支持

策略分析:
  文件: large_file.zip
  大小: 1.5 GB
  推荐风格: MULTI
  推荐分块: 8
  预估加速: 3.5x
  原因: 大文件 + 稳定快速网络
  大小分类: 大文件 (> 100MB)
  Range 支持: 是
```

## 进度回调

```python
from littledl import download_file_sync

def on_progress(downloaded: int, total: int, speed: float, eta: int):
    percent = (downloaded / total) * 100
    print(f"\r进度: {percent:.1f}% | 速度: {speed/1024/1024:.2f} MB/s | 剩余: {eta}s", end="")

path = download_file_sync(
    "https://example.com/large_file.zip",
    progress_callback=on_progress,
)
```

还支持多种回调格式：event/dict/kwargs。

```python
from littledl import ProgressEvent

def on_event(event: ProgressEvent):
    print(event.progress, event.remaining)

def on_dict(payload: dict):
    print(payload["downloaded"], payload["speed"])

def on_kwargs(**payload):
    print(payload["eta"])
```

## 批量下载

### 高性能批量下载

```python
from littledl import EnhancedBatchDownloader

downloader = EnhancedBatchDownloader(
    max_concurrent_files=5,
    max_total_threads=15,
    enable_existing_file_reuse=True,
    enable_multi_source=True,
)

# 添加带备用 URL 的文件
await downloader.add_url(
    "https://example.com/file.zip",
    backup_urls=["https://backup.com/file.zip"]
)

await downloader.start()
```

### 简单批量下载

```python
from littledl import batch_download_sync

results = batch_download_sync(
    urls=[
        "https://example.com/file1.zip",
        "https://example.com/file2.zip",
        "https://example.com/file3.zip",
    ],
    save_path="./downloads",
    max_concurrent_files=5,
)

for url, path, error in results:
    if path:
        print(f"✓ {url} -> {path}")
    else:
        print(f"✗ {url}: {error}")
```

## 配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_chunking` | bool | True | 启用多线程分块下载 |
| `max_chunks` | int | 16 | 最大并发分块数 |
| `chunk_size` | int | 4MB | 默认分块大小 |
| `buffer_size` | int | 64KB | 磁盘写入缓冲区大小 |
| `timeout` | float | 300 | 读写超时（秒） |
| `resume` | bool | True | 启用断点续传 |
| `verify_ssl` | bool | True | 验证 SSL 证书 |
| `fallback_to_single_on_failure` | bool | True | 分块失败时回退到单连接下载 |
| `verify_hash` | bool | False | 校验下载文件哈希 |
| `expected_hash` | str | None | 预期哈希值 |
| `hash_algorithm` | str | sha256 | 哈希算法 |
| `min_file_size` | int | None | 最小文件大小限制 |
| `max_file_size` | int | None | 最大文件大小限制 |

## CLI 用法

```bash
# 自动风格选择下载
littledl "https://example.com/file.zip" -o ./downloads

# 分析并获取下载策略建议
littledl "https://example.com/file.zip" --info

# 强制多线程模式
littledl "https://example.com/file.zip" --style multi --max-chunks 8

# 限速下载
littledl "https://example.com/file.zip" --speed-limit 1048576

# 禁用断点续传
littledl "https://example.com/file.zip" --no-resume
```

## 跨平台支持

| 功能 | Windows | macOS | Linux | FreeBSD |
|------|---------|-------|-------|---------|
| 多线程下载 | ✅ | ✅ | ✅ | ✅ |
| 断点续传 | ✅ | ✅ | ✅ | ✅ |
| 系统代理检测 | ✅ | ✅ | ✅ | ✅ |
| 直接文件写入 | ✅ | ✅ | ✅ | ✅ |

## 贡献

参见 CONTRIBUTING.md 了解开发设置和贡献指南。

## 安全

参见 SECURITY.md 了解安全政策和漏洞报告。

## 许可证

Apache-2.0 许可证 - 详见 [LICENSE](LICENSE) 文件。
