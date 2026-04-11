# 配置指南

littledl 的详细配置选项。

## DownloadConfig

下载操作的主要配置类。

```python
from littledl import DownloadConfig

config = DownloadConfig(
    enable_chunking=True,
    max_chunks=16,
    chunk_size=4 * 1024 * 1024,  # 4MB
    buffer_size=64 * 1024,        # 64KB
    timeout=300,
    resume=True,
    verify_ssl=True,
)
```

## 配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `enable_chunking` | bool | True | 启用多线程分块下载 |
| `max_chunks` | int | 16 | 最大并发分块数 |
| `chunk_size` | int | 4MB | 每个分块的大小 |
| `buffer_size` | int | 64KB | 磁盘写入缓冲区大小 |
| `timeout` | float | 300 | 读写超时时间（秒） |
| `resume` | bool | True | 启用断点续传 |
| `verify_ssl` | bool | True | 验证 SSL 证书 |
| `fallback_to_single_on_failure` | bool | True | 分块失败时自动回退到单连接下载 |
| `enable_adaptive` | bool | True | 启用自适应网络调度 |
| `enable_hybrid_turbo` | bool | True | 启用具有 AIMD 拥塞控制和智能重切策略的混合涡轮加速 |
| `enable_fusion` | bool | True | 启用 FUSION 四阶段自适应调度器 |
| `fusion_probe_chunks` | int | 2 | PROBE 阶段的初始工作线程数 |
| `fusion_probe_duration` | float | 2.0 | 进入 RAMP 阶段前的探测时长 |
| `fusion_tail_ratio` | float | 0.20 | 剩余字节比例低于该值时进入 TAIL 阶段 |
| `fusion_tail_boost` | int | 2 | TAIL 阶段允许追加的额外并发数 |
| `hybrid_aimd_increase_step` | int | 1 | 每次增加的并发目标线程数 (加性增) |
| `hybrid_aimd_decrease_factor` | float | 0.5 | 遇到速度骤降时的并发减少系数 (乘性减) |
| `hybrid_speedup_threshold` | float | 0.08 | 触发 AIMD 提速的最小相对网络加速阈值 |
| `hybrid_slow_chunk_ratio` | float | 0.45 | 被视为极慢资源块的耗时占比阈值 |
| `verify_hash` | bool | False | 校验下载文件哈希 |
| `expected_hash` | str | None | 预期哈希值 |
| `hash_algorithm` | str | `sha256` | 校验使用的哈希算法 |
| `min_file_size` | int | None | 拒绝小于该值的文件 |
| `max_file_size` | int | None | 拒绝大于该值的文件 |
| `progress_update_interval` | float | 0.5 | 回调刷新间隔（秒） |
| `chunk_callback` | Callable | None | 分块下载过程中的分片状态回调 |

## 批量下载中的单文件配置继承

批量下载器会从父级 `DownloadConfig` 派生每个文件的配置，因此认证、代理、FUSION、自适应调优、重切控制和限速等高级设置都会自动保留。

```python
file_config = config.create_file_config(
    max_chunks=8,
    min_chunks=1,
    enable_chunking=True,
)
```

## 代理配置

```python
from littledl import DownloadConfig, ProxyConfig, ProxyMode

proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    http_proxy="http://proxy.example.com:8080",
    https_proxy="https://proxy.example.com:8080",
)

config = DownloadConfig(proxy=proxy)
```

## 速度限制

```python
from littledl import DownloadConfig, SpeedLimitConfig, SpeedLimitMode

speed_limit = SpeedLimitConfig(
    enabled=True,
    mode=SpeedLimitMode.GLOBAL,
    max_speed=1024 * 1024,  # 1 MB/s
)

config = DownloadConfig(speed_limit=speed_limit)
```

## 进度回调

`progress_callback` 支持四种格式：

- 传统位置参数：`(downloaded, total, speed, eta)`
- 事件对象：`ProgressEvent`
- 字典载荷：`dict`
- 关键字参数：`**payload`

```python
from littledl import ProgressEvent

def on_progress(downloaded: int, total: int, speed: float, eta: int):
    percent = (downloaded / total) * 100
    print(f"\r{percent:.1f}% | {speed/1024:.1f} KB/s | 剩余: {eta}s", end="")

def on_event(event: ProgressEvent):
    print(event.progress, event.remaining)

def on_dict(payload: dict):
    print(payload["downloaded"], payload["speed"])

def on_kwargs(**payload):
    print(payload["eta"])

config = DownloadConfig(progress_callback=on_progress)
```

## 分块状态回调

`chunk_callback` 仅在分块下载模式下触发，支持与 `progress_callback` 相同的四种格式。

```python
from littledl import ChunkEvent

def on_chunk(event: ChunkEvent):
    print(event.chunk_index, event.status, event.progress)

config = DownloadConfig(chunk_callback=on_chunk)
```
