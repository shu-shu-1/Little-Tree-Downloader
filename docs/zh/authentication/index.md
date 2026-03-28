# 认证设置

如何为受保护的资源配置认证。

## AuthConfig

```python
from littledl import AuthConfig, AuthType
```

## 认证类型

### Basic 认证

```python
auth = AuthConfig(
    auth_type=AuthType.BASIC,
    username="user",
    password="pass",
)
```

### Bearer Token

```python
auth = AuthConfig(
    auth_type=AuthType.BEARER,
    token="your-api-token",
)
```

### API Key

```python
auth = AuthConfig(
    auth_type=AuthType.API_KEY,
    api_key="your-api-key",
    api_key_header="X-API-Key",
)
```

### Digest 认证

```python
auth = AuthConfig(
    auth_type=AuthType.DIGEST,
    username="user",
    password="pass",
)
```

### OAuth2

```python
auth = AuthConfig(
    auth_type=AuthType.OAUTH2,
    client_id="client-id",
    client_secret="client-secret",
    token_url="https://example.com/oauth/token",
)
```

## 使用认证

```python
from littledl import DownloadConfig, AuthConfig, AuthType

auth = AuthConfig(
    auth_type=AuthType.BEARER,
    token="your-token",
)

config = DownloadConfig(auth=auth)
path = download_file_sync("https://example.com/protected/file.zip", config=config)
```
