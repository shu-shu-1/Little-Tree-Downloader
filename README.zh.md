English | 简体中文

# littledl

高性能下载库，支持 IDM 风格的多线程分块下载、智能调度和断点续传。

## 特性

### 核心功能
- 🚀 **多线程分块下载**：将文件分块并行下载，最大化速度
- 🎯 **直接写入文件**：直接写入最终文件，无需临时文件合并
- 🧠 **智能调度**：智能分块重分配和自适应并发
- ⏯️ **断点续传**：支持从上次中断处继续下载
- 📊 **实时速度监控**：实时速度计算、预计剩余时间和趋势分析
- 🔁 **可靠回退**：分块下载失败时自动回退单连接下载

### 高级功能
- 🔐 **多种认证方式**：Basic、Bearer、Digest、API Key、OAuth2
- 🌐 **完整代理支持**：系统代理自动检测、PAC 文件、SOCKS5
- ⏱️ **速度限制**：令牌桶、漏桶和自适应算法
- ✅ **完整性校验**：支持下载后哈希校验（`verify_hash`、`expected_hash`）
- 🔍 **服务器检测**：自动检测服务器能力以优化下载策略
- 💻 **跨平台**：Windows、macOS、Linux、FreeBSD
- 🔒 **安全**：SSL 验证、安全路径处理

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

### 进度回调

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

### 分块状态回调

```python
from littledl import ChunkEvent, download_file_sync

def on_chunk(event: ChunkEvent):
    print(
        f"chunk={event.chunk_index} status={event.status} "
        f"progress={event.progress:.1f}% speed={event.speed/1024:.1f}KB/s"
    )

path = download_file_sync(
    "https://example.com/large_file.zip",
    chunk_callback=on_chunk,
)
```

## 高级用法

### 认证配置

```python
from littledl import DownloadConfig, AuthConfig, AuthType

auth = AuthConfig(
    auth_type=AuthType.BEARER,
    token="your-api-token",
)

config = DownloadConfig(auth=auth)
```

### 代理配置

```python
from littledl import DownloadConfig, ProxyConfig, ProxyMode

# 系统代理（自动检测）
proxy = ProxyConfig(mode=ProxyMode.SYSTEM)

# 自定义代理
proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    http_proxy="http://proxy.example.com:8080",
)

config = DownloadConfig(proxy=proxy)
```

### 速度限制

```python
from littledl import DownloadConfig, SpeedLimitConfig, SpeedLimitMode

speed_limit = SpeedLimitConfig(
    enabled=True,
    mode=SpeedLimitMode.GLOBAL,
    max_speed=1024 * 1024,  # 1 MB/s
)

config = DownloadConfig(speed_limit=speed_limit)
```

## 多语言支持

通过环境变量设置语言：

```bash
export LITTLELDL_LANGUAGE=zh  # 中文
export LITTLELDL_LANGUAGE=en  # English
```

或代码中设置：

```python
from littledl import set_language, get_available_languages

set_language("zh")  # 切换到中文
print(get_available_languages())  # {'en': 'English', 'zh': '中文'}
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
