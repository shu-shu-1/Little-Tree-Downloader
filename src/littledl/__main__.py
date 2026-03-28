import argparse
import asyncio
import shutil
import sys
from pathlib import Path

import httpx

from . import DownloadConfig, download_file_sync
from .i18n import gettext as _
from .utils import determine_filename


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="littledl",
        description=_("A high-performance download tool with multi-threaded chunked downloading"),
    )
    parser.add_argument("url", help=_("URL to download"))
    parser.add_argument("-o", "--output", dest="output", help=_("Output directory or file path"))
    parser.add_argument("-f", "--filename", dest="filename", help=_("Specify output filename"))
    parser.add_argument("-i", "--info", dest="info_only", action="store_true", help=_("Show file info and exit"))
    parser.add_argument("--no-resume", dest="resume", action="store_false", default=True, help=_("Disable resume"))
    parser.add_argument(
        "-c", "--max-chunks", dest="max_chunks", type=int, default=16, help=_("Maximum number of chunks")
    )
    parser.add_argument("-t", "--timeout", dest="timeout", type=int, default=300, help=_("Timeout in seconds"))
    parser.add_argument("--proxy", dest="proxy", help=_("HTTP proxy (e.g., http://proxy:8080)"))
    parser.add_argument("--user-agent", dest="user_agent", help=_("Custom User-Agent"))
    parser.add_argument(
        "--verify-ssl", dest="verify_ssl", action="store_true", default=True, help=_("Verify SSL certificates")
    )
    parser.add_argument("--no-verify-ssl", dest="verify_ssl", action="store_false", help=_("Skip SSL verification"))
    parser.add_argument("--speed-limit", dest="speed_limit", type=int, help=_("Speed limit in bytes per second"))
    parser.add_argument("--retry", dest="retry", type=int, default=3, help=_("Maximum retry attempts"))
    parser.add_argument("-v", "--verbose", action="store_true", help=_("Verbose output"))
    return parser.parse_args(args)


async def probe_url(url: str, config: DownloadConfig) -> dict:
    timeout = httpx.Timeout(connect=config.connect_timeout, read=config.read_timeout)

    async with httpx.AsyncClient(verify=config.verify_ssl) as client:
        headers = config.get_headers(url)
        response = await client.head(url, headers=headers, follow_redirects=True, timeout=timeout)

        content_disposition = response.headers.get("Content-Disposition")
        content_type = response.headers.get("Content-Type")
        content_length = response.headers.get("Content-Length")
        accept_ranges = response.headers.get("Accept-Ranges", "").lower()

        file_size = int(content_length) if content_length else -1
        supports_range = accept_ranges == "bytes"
        supports_resume = supports_range and file_size > 0

        filename = determine_filename(url, content_disposition, content_type)

        return {
            "url": url,
            "filename": filename,
            "size": file_size,
            "supports_range": supports_range,
            "supports_resume": supports_resume,
            "content_type": content_type,
            "etag": response.headers.get("ETag"),
            "last_modified": response.headers.get("Last-Modified"),
        }


def print_file_info(info: dict) -> None:
    print(f"\n{_('File Info')}:")
    print(f"  {_('Filename')}: {info['filename']}")
    if info["size"] > 0:
        print(f"  {_('Size')}: {format_size(info['size'])}")
    else:
        print(f"  {_('Size')}: {_('Unknown')}")
    print(f"  {_('Content-Type')}: {info['content_type'] or _('Unknown')}")
    print(f"  {_('Resume Support')}: {_('Yes') if info['supports_resume'] else _('No')}")


def get_unique_path(path: Path) -> Path:
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    parent = path.parent
    counter = 1

    while True:
        new_name = f"{stem} ({counter}){suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1


class ProgressDisplay:
    def __init__(self) -> None:
        self.last_len = 0

    def clear(self) -> None:
        if self.last_len > 0:
            sys.stdout.write("\r" + " " * self.last_len)
            sys.stdout.write("\r")
            sys.stdout.flush()
            self.last_len = 0

    def update(self, downloaded: int, total: int, speed: float, eta: int) -> None:
        if total <= 0:
            return

        downloaded_str = format_size(downloaded)
        total_str = format_size(total)
        speed_str = f"{format_size(speed)}/s"

        progress = downloaded / total
        bar_len = min(40, shutil.get_terminal_size().columns - 60)
        filled = int(bar_len * progress)
        bar = "[" + "=" * filled + " " * (bar_len - filled) + "]"

        if eta > 0:
            eta_str = format_time(eta)
            line = f"{bar} {progress * 100:5.1f}% | {downloaded_str:>8} / {total_str:<8} | {speed_str:>10} | ETA: {eta_str}"
        else:
            line = f"{bar} {progress * 100:5.1f}% | {downloaded_str:>8} / {total_str:<8} | {speed_str:>10}"

        self.clear()
        sys.stdout.write(line)
        sys.stdout.flush()
        self.last_len = len(line)

    def finish(self) -> None:
        self.clear()


def format_size(bytes_num: float) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_num < 1024:
            return f"{bytes_num:6.1f}{unit}" if bytes_num >= 100 else f"{bytes_num:5.2f}{unit}"
        bytes_num /= 1024
    return f"{bytes_num:6.1f}PB"


def format_time(seconds: int) -> str:
    if seconds < 0:
        return "--:--"
    if seconds < 60:
        return f"  {seconds}s"
    if seconds < 3600:
        return f"{seconds // 60:02d}m {seconds % 60:02d}s"
    return f"{seconds // 3600}h {(seconds % 3600) // 60:02d}m"


async def run_probe(url: str, config: DownloadConfig) -> int:
    try:
        info = await probe_url(url, config)
        print_file_info(info)
        return 0
    except Exception as e:
        print(f"\n{_('Failed to probe URL')}: {e}")
        return 1


def main() -> int:
    args = parse_args()

    config = DownloadConfig(
        resume=args.resume,
        max_chunks=args.max_chunks,
        timeout=args.timeout,
        verify_ssl=args.verify_ssl,
    )

    if args.proxy:
        from . import ProxyConfig, ProxyMode

        config.proxy = ProxyConfig(mode=ProxyMode.CUSTOM, http_proxy=args.proxy, https_proxy=args.proxy)

    if args.user_agent:
        config.user_agent = args.user_agent

    if args.speed_limit:
        from . import SpeedLimitConfig, SpeedLimitMode

        config.speed_limit = SpeedLimitConfig(enabled=True, mode=SpeedLimitMode.GLOBAL, max_speed=args.speed_limit)

    if args.retry:
        from . import RetryConfig

        config.retry = RetryConfig(max_retries=args.retry)

    if args.info_only:
        return asyncio.run(run_probe(args.url, config))

    output_path = Path(args.output or "./downloads").expanduser().resolve()
    progress = ProgressDisplay()

    if args.verbose:
        print(f"{_('Starting download')}: {args.url}")
        print(f"{_('Output')}: {output_path}")

    final_filename = args.filename
    if output_path.is_dir() and not final_filename:
        info = asyncio.run(probe_url(args.url, config))
        final_filename = info["filename"]

    save_path = output_path / final_filename if output_path.is_dir() else output_path
    save_path = get_unique_path(save_path)

    if args.verbose and save_path.name != (final_filename or ""):
        print(f"{_('Auto-renamed to')}: {save_path.name}")

    try:
        path = download_file_sync(
            url=args.url,
            save_path=str(save_path.parent),
            filename=save_path.name,
            config=config,
            progress_callback=progress.update,
            resume=args.resume,
        )
        progress.finish()
        print(f"\n{_('Download complete')}: {path}")
        return 0
    except KeyboardInterrupt:
        progress.finish()
        print(f"\n{_('Download cancelled')}")
        return 1
    except Exception as e:
        progress.finish()
        print(f"\n{_('Download failed')}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
