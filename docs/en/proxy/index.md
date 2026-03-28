# Proxy Configuration

Detailed guide on configuring proxy settings for littledl.

## ProxyConfig

```python
from littledl import ProxyConfig, ProxyMode
```

## Proxy Modes

### System Proxy (Auto-detect)

Automatically detect and use system proxy settings.

```python
proxy = ProxyConfig(mode=ProxyMode.SYSTEM)
```

### Custom Proxy

Manually specify proxy settings.

```python
proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    http_proxy="http://proxy.example.com:8080",
    https_proxy="https://proxy.example.com:8080",
)
```

### No Proxy

Explicitly disable proxy.

```python
proxy = ProxyConfig(mode=ProxyMode.NONE)
```

## SOCKS5 Proxy

```python
proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    socks5_proxy="socks5://user:pass@proxy.example.com:1080",
)
```

## Using Proxy with DownloadConfig

```python
from littledl import DownloadConfig, ProxyConfig, ProxyMode

proxy = ProxyConfig(
    mode=ProxyMode.CUSTOM,
    http_proxy="http://proxy.example.com:8080",
)

config = DownloadConfig(proxy=proxy)
path = download_file_sync("https://example.com/file.zip", config=config)
```

## Environment Variables

littledl also respects standard proxy environment variables:

- `HTTP_PROXY` / `http_proxy`
- `HTTPS_PROXY` / `https_proxy`
- `SOCKS_PROXY` / `socks_proxy`
- `NO_PROXY` / `no_proxy`
