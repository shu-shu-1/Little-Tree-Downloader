# Command Line Interface

littledl provides a full-featured command-line interface for both interactive use and scripting.

## Installation

After installing littledl, the CLI is available as the `littledl` command:

```bash
pip install littledl
```

Verify installation:

```bash
littledl --version
# Output: littledl 0.6.1
```

## Basic Usage

### Download a Single File

```bash
littledl "https://example.com/large-file.zip" -o ./downloads
```

### Download Multiple Files Directly

```bash
littledl "https://example.com/file1.zip" "https://example.com/file2.pdf" "https://example.com/file3.doc" -o ./downloads
```

### Batch Download

Create a file `urls.txt` with one URL per line:

```text
# Comments are supported
https://example.com/file1.zip
https://example.com/file2.pdf
https://example.com/file3.doc
```

Then download:

```bash
littledl -F urls.txt -o ./downloads
```

## Common Options

| Option                    | Description                   | Default         |
| ------------------------- | ----------------------------- | --------------- |
| `-o, --output PATH`     | Output directory or file path | `./downloads` |
| `-f, --filename NAME`   | Specify output filename       | Server-provided |
| `-c, --max-chunks N`    | Maximum parallel chunks       | `16`          |
| `-t, --timeout SECONDS` | Request timeout               | `300`         |
| `--proxy URL`           | HTTP proxy                    | None            |
| `--speed-limit BYTES/s` | Limit download speed          | Unlimited       |
| `--retry N`             | Maximum retry attempts        | `3`           |
| `-v, --verbose`         | Verbose output                | False           |
| `--temp-dir PATH`       | Temporary files directory     | Same as output  |

## Download Styles

| Style            | Description                     | Best For                                   |
| ---------------- | ------------------------------- | ------------------------------------------ |
| `single`       | Single-threaded download        | Small files, servers without Range support |
| `multi`        | Multi-threaded segmented        | Large files, stable connections            |
| `adaptive`     | Auto-select based on conditions | Most use cases                             |
| `hybrid_turbo` | Adaptive with AIMD control      | Maximum speed, unstable networks           |
| `auto`         | Let littledl analyze and decide | Recommended for beginners                  |

### Examples

```bash
# Auto-select best style
littledl "https://example.com/file.zip" -s auto

# Force single-threaded
littledl "https://example.com/file.zip" -s single

# Maximum performance
littledl "https://example.com/file.zip" -s hybrid_turbo -c 32
```

## Progress Display

### Interactive Mode (TTY)

When stdout is a terminal, littledl displays an animated progress bar:

```
[=============>                ]  45.2% |  45.2MB / 100.0MB | 10.5MB/s | ETA: 00:05
```

### Non-Interactive Mode (Pipe/Redirect)

When output is piped or redirected, littledl automatically switches to minimal output:

```bash
# Piped to file
littledl "https://example.com/file.zip" > download.log

# Piped to another tool
littledl "https://example.com/file.zip" | head -c 100
```

## Output Formats

Use `--output-format` to control output style:

| Format   | Description                                         |
| -------- | --------------------------------------------------- |
| `auto` | Automatic (default) - TTY uses text, pipe uses JSON |
| `text` | Human-readable text output                          |
| `json` | Structured JSON for scripting                       |

### JSON Output

For programmatic use, specify JSON output:

```bash
littledl "https://example.com/file.zip" -o /tmp --output-format json
```

JSON output example:

```json
{
  "type": "download",
  "success": true,
  "path": "/tmp/file.zip",
  "size": 104857600
}
```

Batch download JSON output:

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

## Exit Codes

littledl uses specific exit codes for scripting:

| Code  | Meaning                       |
| ----- | ----------------------------- |
| `0` | Success                       |
| `1` | General error                 |
| `2` | URL error or invalid argument |
| `3` | Download failed after retries |
| `4` | Cancelled by user (Ctrl+C)    |

Example in scripts:

```bash
littledl "https://example.com/file.zip" -o /tmp
if [ $? -eq 0 ]; then
    echo "Download successful"
else
    echo "Download failed with code $?"
fi
```

## Advanced Examples

### Resume Interrupted Download

```bash
littledl "https://example.com/large-file.zip" -o ./downloads --resume
```

### Skip SSL Verification (Not Recommended)

```bash
littledl "https://example.com/file.zip" --no-verify-ssl
```

### Use Proxy

```bash
littledl "https://example.com/file.zip" --proxy "http://proxy:8080"
```

### Limit Speed

```bash
# Limit to 1MB/s
littledl "https://example.com/file.zip" --speed-limit 1048576
```

### Batch Download with Concurrent Limit

```bash
littledl -F urls.txt -o ./downloads --max-concurrent 3
```

### Quiet Mode (Minimal Output)

```bash
littledl -F urls.txt --quiet
```

### Show File Info Without Downloading

```bash
littledl "https://example.com/file.zip" -i
# Output:
# File Info:
#   Filename: example.zip
#   Size: 104.5 MB
#   Content-Type: application/zip
#   Resume Support: Yes
```

### Analyze and Auto-Select Best Style

```bash
littledl "https://example.com/file.zip" -s auto -i
```

## Environment Variables

| Variable | Description                                    |
| -------- | ---------------------------------------------- |
| `LANG` | Language selection (e.g.,`zh_CN`, `en_US`) |

## Next Steps

- [Configuration Guide](../configuration/index.md) - All configuration options
- [Batch Download](../batch-download/index.md) - Advanced batch download features
- [API Reference](../api-reference/index.md) - Use littledl as a library
