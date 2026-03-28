# API 参考

littledl 的完整 API 参考。

## 核心函数

### download_file_sync

同步文件下载。

```python
from littledl import download_file_sync

path = download_file_sync(
    url: str,
    save_path: str = ".",
    filename: str | None = None,
    config: DownloadConfig | None = None,
    progress_callback: Callable | None = None,
    chunk_callback: Callable | None = None,
) -> Path
```

### download_file

异步文件下载。

```python
from littledl import download_file

path = await download_file(
    url: str,
    save_path: str = ".",
    filename: str | None = None,
    config: DownloadConfig | None = None,
    progress_callback: Callable | None = None,
    chunk_callback: Callable | None = None,
) -> Path
```

## 配置类

### DownloadConfig

```python
from littledl import DownloadConfig

config = DownloadConfig(
    enable_chunking: bool = True,
    max_chunks: int = 16,
    chunk_size: int = 4 * 1024 * 1024,
    buffer_size: int = 64 * 1024,
    timeout: float = 300,
    resume: bool = True,
    verify_ssl: bool = True,
    auth: AuthConfig | None = None,
    proxy: ProxyConfig | None = None,
    speed_limit: SpeedLimitConfig | None = None,
    progress_callback: Callable | None = None,
    chunk_callback: Callable | None = None,
)
```

#### 方法

**`apply_style(style: Any) -> "DownloadConfig"`**

根据相应的下载风格（支持 `DownloadStyle` 枚举对象，或对应名称的字符串如 `"SINGLE"`, `"MULTI"`, `"ADAPTIVE"`, `"HYBRID_TURBO"`）一次性更改当前所有相关的调度算法配置、分块开关与 AIMD 网络拥塞控制参数，返回修改后的配置对象自身。

## 回调事件

### ProgressEvent

```python
ProgressEvent(
    downloaded: int,
    total: int,
    speed: float,
    eta: int,
    progress: float,
    remaining: int,
    timestamp: float,
)
```

### ChunkEvent

```python
ChunkEvent(
    chunk_index: int,
    status: str,  # started/downloading/completed/failed
    downloaded: int,
    total: int,
    progress: float,
    speed: float,
    error: str | None,
    timestamp: float,
)
```
```

### AuthConfig

```python
from littledl import AuthConfig, AuthType

auth = AuthConfig(
    auth_type: AuthType,
    username: str | None = None,
    password: str | None = None,
    token: str | None = None,
    api_key: str | None = None,
    api_key_header: str | None = None,
)
```

### ProxyConfig

```python
from littledl import ProxyConfig, ProxyMode

proxy = ProxyConfig(
    mode: ProxyMode = ProxyMode.SYSTEM,
    http_proxy: str | None = None,
    https_proxy: str | None = None,
    socks5_proxy: str | None = None,
)
```

### SpeedLimitConfig

```python
from littledl import SpeedLimitConfig, SpeedLimitMode

speed_limit = SpeedLimitConfig(
    enabled: bool = False,
    mode: SpeedLimitMode = SpeedLimitMode.GLOBAL,
    max_speed: int = 0,
)
```

## 枚举类型

### AuthType

- `BASIC`
- `BEARER`
- `DIGEST`
- `API_KEY`
- `OAUTH2`

### ProxyMode

- `SYSTEM` - 自动检测系统代理
- `CUSTOM` - 使用自定义代理设置
- `NONE` - 不使用代理

### SpeedLimitMode

- `GLOBAL` - 限制整体速度
- `PER_CHUNK` - 限制每个分块的速度

## 多语言支持

```python
from littledl import set_language, get_available_languages

set_language("zh")  # 或 "en"
print(get_available_languages())  # {'en': 'English', 'zh': '中文'}
```

## 文件写入器

### BufferedFileWriter

高性能缓冲文件写入器，用于优化并发下载性能。

```python
from littledl import BufferedFileWriter

writer = BufferedFileWriter(
    file_path="/path/to/file.zip",
    mode="wb",
    buffer_size=512 * 1024,  # 512KB 缓冲
    flush_interval=0.5,      # 500ms 自动刷新
    max_buffers=16,          # 最大并发缓冲数
)

await writer.open()
await writer.write_at(offset=0, data=b"chunk data")
await writer.close()
```

### DirectFileWriter

直接文件写入器（传统实现，保留向后兼容）。

```python
from littledl import DirectFileWriter

writer = DirectFileWriter(file_path="/path/to/file.zip")
await writer.open()
await writer.write_at(offset=0, data=b"chunk data")
await writer.close()
```

**注意**: BufferedFileWriter 会自动在分块下载中使用，无需手动配置。
