# 错误处理

littledl 如何处理错误和异常。

## 异常类型

### DownloadException

所有下载相关错误的基础异常。

```python
from littledl import DownloadException

try:
    path = download_file_sync("https://example.com/file.zip")
except DownloadException as e:
    print(f"下载失败: {e}")
```

### NetworkError

网络相关错误（连接超时、DNS 失败等）。

```python
from littledl import NetworkError

try:
    path = download_file_sync("https://example.com/file.zip")
except NetworkError as e:
    print(f"网络错误: {e}")
```

### AuthenticationError

认证失败。

```python
from littledl import AuthenticationError

try:
    path = download_file_sync("https://example.com/protected.zip", config=config)
except AuthenticationError as e:
    print(f"认证失败: {e}")
```

### FileExistsError

文件已存在且 `overwrite` 设置为 `False`。

```python
from littledl import FileExistsError

try:
    path = download_file_sync("https://example.com/file.zip", overwrite=False)
except FileExistsError as e:
    print(f"文件已存在: {e}")
```

## 重试配置

为失败的下载配置自动重试。

```python
from littledl import DownloadConfig, RetryConfig, RetryMode

retry = RetryConfig(
    enabled=True,
    mode=RetryMode.EXPONENTIAL,
    max_retries=3,
    initial_delay=1.0,
    max_delay=60.0,
)

config = DownloadConfig(retry=retry)
```

## 验证错误

### URL 验证

下载前始终验证 URL：

```python
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https')

if not validate_url(url):
    raise ValueError("无效的 URL")
```

### 文件大小限制

设置最大文件大小以防止过度下载：

```python
from littledl import DownloadConfig

config = DownloadConfig(
    max_file_size=100 * 1024 * 1024,  # 100MB
)
```
