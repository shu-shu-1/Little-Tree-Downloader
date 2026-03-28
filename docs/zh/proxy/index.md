# 代理配置

littledl 代理配置详细指南。

## ProxyConfig

```python
from littledl import ProxyConfig, ProxyMode
```

## 代理模式

### 系统代理（自动检测）

自动检测并使用系统代理设置。

```python
proxy = ProxyConfig(mode=ProxyMode.SYSTEM)
```

### 自定义代理

手动指定代理设置。

```python
proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    http_proxy="http://proxy.example.com:8080",
    https_proxy="https://proxy.example.com:8080",
)
```

### 无代理

显式禁用代理。

```python
proxy = ProxyConfig(mode=ProxyMode.NONE)
```

## SOCKS5 代理

```python
proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    socks5_proxy="socks5://user:pass@proxy.example.com:1080",
)
```

## 在 DownloadConfig 中使用代理

```python
from littledl import DownloadConfig, ProxyConfig, ProxyMode

proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    http_proxy="http://proxy.example.com:8080",
)

config = DownloadConfig(proxy=proxy)
path = download_file_sync("https://example.com/file.zip", config=config)
```

## 环境变量

littledl 也支持标准代理环境变量：

- `HTTP_PROXY` / `http_proxy`
- `HTTPS_PROXY` / `https_proxy`
- `SOCKS_PROXY` / `socks_proxy`
- `NO_PROXY` / `no_proxy`
