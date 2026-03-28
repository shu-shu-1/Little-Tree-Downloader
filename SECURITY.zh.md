English | 简体中文

# 安全政策

## 支持的版本

我们积极为以下版本提供安全更新：

| 版本 | 支持状态 |
| ---- | -------- |
| 0.2.x | ✅ |

## 报告漏洞

我们非常重视 littledl 的安全性。如果您发现安全漏洞，请按以下步骤报告：

### 如何报告

**请勿通过公开的 GitHub issues 报告安全漏洞。**

请通过以下方式报告：

1. **GitHub 安全公告**（首选）
   - 进入我们的仓库的 [安全标签页](https://github.com/little-tree/little-tree-downloader/security)
   - 点击"报告漏洞"
   - 填写包含漏洞详情的表格

2. **电子邮件**（备选）
   - 发送电子邮件至 zsxiaoshu@outlook.com
   - 主题行中包含"SECURITY"
   - 提供漏洞的详细信息

### 应包含的内容

报告漏洞时，请包括：

- **描述**：漏洞的清晰描述
- **影响**：攻击者可能利用此漏洞做什么？
- **复现步骤**：复现问题的逐步说明
- **概念验证**：演示漏洞的代码（如有）
- **建议修复**：如果您对修复此问题有想法

### 响应时间

- **初步响应**：48 小时内
- **漏洞确认**：5 个工作日内
- **修复开发**：取决于严重程度
- **披露**：修复发布后

## 安全最佳实践

使用 littledl 时，请遵循以下最佳实践：

### 1. URL 验证

下载前始终验证 URL：

```python
from littledl import DownloadConfig

config = DownloadConfig(verify_ssl=True)
```

### 2. SSL 证书验证

生产环境中永远不要禁用 SSL 验证：

```python
# 错误 - 禁用 SSL 验证
config = DownloadConfig(verify_ssl=False)

# 正确 - 验证 SSL 证书
config = DownloadConfig(verify_ssl=True)
```

### 3. 认证凭据

保护凭据安全：

```python
import os
from littledl import AuthConfig

# 正确 - 使用环境变量
config = AuthConfig(
    auth_type="bearer",
    token=os.environ.get("API_TOKEN"),
)
```

### 4. 代理配置

谨慎使用代理设置：

```python
from littledl import ProxyConfig, ProxyMode

# 正确 - 使用系统代理设置
config = ProxyConfig(mode=ProxyMode.SYSTEM)
```

## 已知安全注意事项

### SSRF（服务器端请求伪造）

此库从 URL 下载文件。如果您接受来自不受信任来源的 URL：

1. **验证 URL** 后再传递给下载器
2. **限制允许的协议**（仅 http/https）
3. **阻止内部 IP 地址**（如适用）

### 内存使用

使用多个分块下载大文件时会消耗大量内存：

```python
# 对于超大文件，减少分块数量
config = DownloadConfig(
    max_chunks=4,
    buffer_size=64 * 1024,
)
```

## 安全更新

安全更新将通过以下方式公布：

- GitHub 安全公告
- 发布说明中带有 `[SECURITY]` 前缀
- PyPI 包更新

## 联系

安全问题：
- **安全公告**：[GitHub Security](https://github.com/little-tree/little-tree-downloader/security)
- **电子邮件**：zsxiaoshu@outlook.com

感谢您帮助保护 littledl 的安全！
