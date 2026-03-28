English | [简体中文](SECURITY.zh.md)

# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.2.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of littledl seriously. If you discover a security vulnerability, please follow these steps:

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via:

1. **GitHub Security Advisories** (Preferred)
   - Go to the [Security tab](https://github.com/little-tree/little-tree-downloader/security) of our repository
   - Click "Report a vulnerability"
   - Fill out the form with details about the vulnerability

2. **Email** (Alternative)
   - Send an email to zsxiaoshu@outlook.com
   - Include "SECURITY" in the subject line
   - Provide detailed information about the vulnerability

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Impact**: What could an attacker do with this vulnerability?
- **Reproduction**: Step-by-step instructions to reproduce the issue
- **Proof of Concept**: Code that demonstrates the vulnerability (if available)
- **Suggested Fix**: If you have ideas for fixing the issue

### Response Timeline

- **Initial Response**: Within 48 hours
- **Vulnerability Confirmation**: Within 5 business days
- **Fix Development**: Depends on severity
- **Disclosure**: After fix is released

## Security Best Practices

When using littledl, follow these best practices:

### 1. URL Validation

Always validate URLs before downloading:

```python
from littledl import DownloadConfig

config = DownloadConfig(verify_ssl=True)
```

### 2. SSL Certificate Verification

Never disable SSL verification in production:

```python
# Bad - Disables SSL verification
config = DownloadConfig(verify_ssl=False)

# Good - Verify SSL certificates
config = DownloadConfig(verify_ssl=True)
```

### 3. Authentication Credentials

Keep credentials secure:

```python
import os
from littledl import AuthConfig

# Good - Use environment variables
config = AuthConfig(
    auth_type="bearer",
    token=os.environ.get("API_TOKEN"),
)
```

### 4. Proxy Configuration

Use caution with proxy settings:

```python
from littledl import ProxyConfig, ProxyMode

# Good - Use system proxy settings
config = ProxyConfig(mode=ProxyMode.SYSTEM)
```

## Known Security Considerations

### SSRF (Server-Side Request Forgery)

This library downloads files from URLs. If you accept URLs from untrusted sources:

1. **Validate the URL** before passing it to the downloader
2. **Restrict allowed protocols** (only http/https)
3. **Block internal IP addresses** if appropriate

### Memory Usage

Large file downloads can consume significant memory when using multiple chunks:

```python
# For very large files, reduce chunk count
config = DownloadConfig(
    max_chunks=4,
    buffer_size=64 * 1024,
)
```

## Security Updates

Security updates will be announced via:

- GitHub Security Advisories
- Release notes with `[SECURITY]` prefix
- PyPI package updates

## Contact

For security concerns:
- **Security Advisories**: [GitHub Security](https://github.com/little-tree/little-tree-downloader/security)
- **Email**: zsxiaoshu@outlook.com

Thank you for helping keep littledl secure!
