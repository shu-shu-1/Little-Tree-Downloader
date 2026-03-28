# 命令行界面

littledl 提供功能完整的命令行界面，既支持交互式使用，也支持脚本调用。

## 安装

安装 littledl 后，CLI 命令 `littledl` 即可使用：

```bash
pip install littledl
```

验证安装：

```bash
littledl --version
# 输出: littledl 0.4.0
```

## 基本用法

### 下载单个文件

```bash
littledl "https://example.com/large-file.zip" -o ./downloads
```

### 批量下载

创建文件 `urls.txt`，每行一个 URL：

```text
# 支持注释行
https://example.com/file1.zip
https://example.com/file2.pdf
https://example.com/file3.doc
```

然后执行下载：

```bash
littledl -F urls.txt -o ./downloads
```

## 常用选项

| 选项                      | 说明               | 默认值          |
| ------------------------- | ------------------ | --------------- |
| `-o, --output 路径`     | 输出目录或文件路径 | `./downloads` |
| `-f, --filename 名称`   | 指定输出文件名     | 服务器提供      |
| `-c, --max-chunks N`    | 最大并行分块数     | `16`          |
| `-t, --timeout 秒`      | 请求超时时间       | `300`         |
| `--proxy URL`           | HTTP 代理          | 无              |
| `--speed-limit 字节/秒` | 限速               | 不限速          |
| `--retry N`             | 最大重试次数       | `3`           |
| `-v, --verbose`         | 详细输出           | False           |
| `--temp-dir 路径`      | 临时文件目录       | 输出文件同级目录 |

## 下载模式

| 模式             | 说明                   | 适用场景                      |
| ---------------- | ---------------------- | ----------------------------- |
| `single`       | 单线程下载             | 小文件、不支持 Range 的服务器 |
| `multi`        | 多线程分段下载         | 大文件、稳定连接              |
| `adaptive`     | 根据条件自动选择       | 大多数场景                    |
| `hybrid_turbo` | 自适应 + AIMD 拥塞控制 | 追求极致速度、不稳定网络      |
| `auto`         | 由 littledl 分析后决定 | 推荐给新手用户                |

### 示例

```bash
# 自动选择最佳模式
littledl "https://example.com/file.zip" -s auto

# 强制单线程
littledl "https://example.com/file.zip" -s single

# 最高性能
littledl "https://example.com/file.zip" -s hybrid_turbo -c 32
```

## 进度显示

### 交互模式 (TTY)

当标准输出是终端时，littledl 显示动态进度条：

```
[=============>                ]  45.2% |  45.2MB / 100.0MB | 10.5MB/s | 预计剩余: 00:05
```

### 非交互模式 (管道/重定向)

当输出被管道传输或重定向时，littledl 自动切换到最小化输出：

```bash
# 输出到文件
littledl "https://example.com/file.zip" > download.log

# 管道到其他工具
littledl "https://example.com/file.zip" | head -c 100
```

## 输出格式

使用 `--output-format` 控制输出样式：

| 格式     | 说明                                          |
| -------- | --------------------------------------------- |
| `auto` | 自动检测（默认）- TTY 使用文本，管道使用 JSON |
| `text` | 人类可读的文本输出                            |
| `json` | 结构化 JSON，用于脚本调用                     |

### JSON 输出

程序化调用时，指定 JSON 输出：

```bash
littledl "https://example.com/file.zip" -o /tmp --output-format json
```

JSON 输出示例：

```json
{
  "type": "download",
  "success": true,
  "path": "/tmp/file.zip",
  "size": 104857600
}
```

批量下载 JSON 输出：

```json
{
  "type": "batch",
  "success": true,
  "total": 10,
  "completed": 9,
  "failed": 1,
  "total_bytes": 104857600,
  "elapsed_seconds": 120.5,
  "average_speed": 870123.45,
  "tasks": [
    {
      "filename": "file1.zip",
      "url": "https://example.com/file1.zip",
      "status": "completed",
      "size": 10485760,
      "downloaded": 10485760,
      "error": null
    }
  ]
}
```

## 退出码

littledl 使用特定的退出码，便于脚本处理：

| 代码  | 含义               |
| ----- | ------------------ |
| `0` | 成功               |
| `1` | 一般错误           |
| `2` | URL 错误或参数无效 |
| `3` | 重试后下载失败     |
| `4` | 用户取消 (Ctrl+C)  |

脚本中的使用示例：

```bash
littledl "https://example.com/file.zip" -o /tmp
if [ $? -eq 0 ]; then
    echo "下载成功"
else
    echo "下载失败，退出码 $?"
fi
```

## 高级示例

### 断点续传

```bash
littledl "https://example.com/large-file.zip" -o ./downloads --resume
```

### 跳过 SSL 验证（不推荐）

```bash
littledl "https://example.com/file.zip" --no-verify-ssl
```

### 使用代理

```bash
littledl "https://example.com/file.zip" --proxy "http://proxy:8080"
```

### 限速下载

```bash
# 限制为 1MB/s
littledl "https://example.com/file.zip" --speed-limit 1048576
```

### 批量下载并发控制

```bash
littledl -F urls.txt -o ./downloads --max-concurrent 3
```

### 安静模式（最小输出）

```bash
littledl -F urls.txt --quiet
```

### 仅显示文件信息

```bash
littledl "https://example.com/file.zip" -i
# 输出：
# 文件信息:
#   文件名: example.zip
#   大小: 104.5 MB
#   Content-Type: application/zip
#   断点续传: 支持
```

### 自动分析并选择最佳模式

```bash
littledl "https://example.com/file.zip" -s auto -i
```

## 环境变量

| 变量     | 说明                                |
| -------- | ----------------------------------- |
| `LANG` | 语言选择（如 `zh_CN`、`en_US`） |

## 进阶阅读

- [配置指南](../configuration/index.md) - 所有配置选项详解
- [批量下载](../batch-download/index.md) - 高级批量下载功能
- [API 参考](../api-reference/index.md) - 将 littledl 作为库使用
