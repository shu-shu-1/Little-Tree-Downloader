# Error Handling

How littledl handles errors and exceptions.

## Exception Types

### DownloadException

Base exception for all download-related errors.

```python
from littledl import DownloadException

try:
    path = download_file_sync("https://example.com/file.zip")
except DownloadException as e:
    print(f"Download failed: {e}")
```

### NetworkError

Network-related errors (connection timeout, DNS failure, etc.).

```python
from littledl import NetworkError

try:
    path = download_file_sync("https://example.com/file.zip")
except NetworkError as e:
    print(f"Network error: {e}")
```

### AuthenticationError

Authentication failures.

```python
from littledl import AuthenticationError

try:
    path = download_file_sync("https://example.com/protected.zip", config=config)
except AuthenticationError as e:
    print(f"Auth failed: {e}")
```

### FileExistsError

File already exists and `overwrite` is set to `False`.

```python
from littledl import FileExistsError

try:
    path = download_file_sync("https://example.com/file.zip", overwrite=False)
except FileExistsError as e:
    print(f"File exists: {e}")
```

## Retry Configuration

Configure automatic retries for failed downloads.

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

## Validation Errors

### URL Validation

Always validate URLs before downloading:

```python
from urllib.parse import urlparse

def validate_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in ('http', 'https')

if not validate_url(url):
    raise ValueError("Invalid URL")
```

### File Size Limits

Set maximum file size to prevent excessive downloads:

```python
from littledl import DownloadConfig

config = DownloadConfig(
    max_file_size=100 * 1024 * 1024,  # 100MB
)
```
