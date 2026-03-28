import asyncio
import contextlib
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from .config import DownloadConfig
from .connection import ConnectionPool
from .downloader import Downloader
from .exceptions import DownloadError
from .utils import generate_download_id, normalize_url, validate_url


class FileTaskStatus(Enum):
    PENDING = "pending"
    PROBING = "probing"
    DOWNLOADING = "downloading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class FileTask:
    task_id: str
    url: str
    save_path: Path
    filename: str | None = None
    status: FileTaskStatus = FileTaskStatus.PENDING
    file_size: int = -1
    downloaded: int = 0
    speed: float = 0.0
    error: str | None = None
    retry_count: int = 0
    priority: int = 0
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    supports_range: bool = True
    chunks: int = 1
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    @property
    def progress(self) -> float:
        if self.file_size <= 0:
            return 0.0
        return (self.downloaded / self.file_size) * 100

    @property
    def is_active(self) -> bool:
        return self.status == FileTaskStatus.DOWNLOADING

    @property
    def is_completed(self) -> bool:
        return self.status == FileTaskStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        return self.status == FileTaskStatus.FAILED

    @property
    def remaining(self) -> int:
        return max(0, self.file_size - self.downloaded)

    @property
    def is_small_file(self) -> bool:
        return 0 < self.file_size < 5 * 1024 * 1024

    @property
    def is_large_file(self) -> bool:
        return self.file_size > 100 * 1024 * 1024

    async def update_progress(self, downloaded: int, speed: float = 0.0) -> None:
        async with self._lock:
            self.downloaded = downloaded
            if speed > 0:
                self.speed = speed

    async def mark_probing(self) -> None:
        async with self._lock:
            self.status = FileTaskStatus.PROBING

    async def mark_downloading(self) -> None:
        async with self._lock:
            self.status = FileTaskStatus.DOWNLOADING
            if self.started_at is None:
                self.started_at = time.time()

    async def mark_completed(self) -> None:
        async with self._lock:
            self.status = FileTaskStatus.COMPLETED
            self.completed_at = time.time()
            self.downloaded = self.file_size

    async def mark_failed(self, error: str) -> None:
        async with self._lock:
            self.status = FileTaskStatus.FAILED
            self.error = error

    async def mark_cancelled(self) -> None:
        async with self._lock:
            self.status = FileTaskStatus.CANCELLED

    async def reset_for_retry(self) -> None:
        async with self._lock:
            self.retry_count += 1
            self.status = FileTaskStatus.PENDING
            self.error = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "url": self.url,
            "save_path": str(self.save_path),
            "filename": self.filename,
            "status": self.status.value,
            "file_size": self.file_size,
            "downloaded": self.downloaded,
            "speed": self.speed,
            "error": self.error,
            "retry_count": self.retry_count,
            "priority": self.priority,
            "supports_range": self.supports_range,
            "chunks": self.chunks,
        }


@dataclass
class BatchProgress:
    total_files: int = 0
    completed_files: int = 0
    failed_files: int = 0
    active_files: int = 0
    total_bytes: int = 0
    downloaded_bytes: int = 0
    overall_speed: float = 0.0
    eta: float = -1

    @property
    def progress(self) -> float:
        if self.total_bytes <= 0:
            return 0.0
        return (self.downloaded_bytes / self.total_bytes) * 100

    @property
    def files_completed_ratio(self) -> float:
        if self.total_files <= 0:
            return 0.0
        return (self.completed_files / self.total_files) * 100


class FileScheduler:
    def __init__(
        self,
        max_concurrent_files: int = 5,
        max_concurrent_chunks_per_file: int = 4,
        small_file_threshold: int = 5 * 1024 * 1024,
        large_file_threshold: int = 100 * 1024 * 1024,
        enable_small_file_priority: bool = True,
    ) -> None:
        self.max_concurrent_files = max_concurrent_files
        self.max_concurrent_chunks_per_file = max_concurrent_chunks_per_file
        self.small_file_threshold = small_file_threshold
        self.large_file_threshold = large_file_threshold
        self.enable_small_file_priority = enable_small_file_priority

        self._pending_tasks: list[FileTask] = []
        self._active_tasks: dict[str, FileTask] = {}
        self._completed_tasks: list[FileTask] = []
        self._failed_tasks: list[FileTask] = []
        self._lock = asyncio.Lock()
        self._paused = False

    @property
    def pending_count(self) -> int:
        return len(self._pending_tasks)

    @property
    def active_count(self) -> int:
        return len(self._active_tasks)

    @property
    def completed_count(self) -> int:
        return len(self._completed_tasks)

    @property
    def failed_count(self) -> int:
        return len(self._failed_tasks)

    @property
    def total_tasks(self) -> int:
        return len(self._pending_tasks) + len(self._active_tasks) + len(self._completed_tasks) + len(self._failed_tasks)

    async def add_task(self, task: FileTask) -> None:
        async with self._lock:
            self._pending_tasks.append(task)
            if self.enable_small_file_priority:
                self._sort_pending_by_priority()

    def _sort_pending_by_priority(self) -> None:
        def get_priority(t: FileTask) -> tuple[int, float]:
            priority = 2
            if t.is_small_file:
                priority = 0
            elif t.is_large_file:
                priority = 3
            elif t.file_size > 0:
                priority = 1
            return (priority, t.created_at)

        self._pending_tasks.sort(key=get_priority)

    async def get_next_task(self) -> FileTask | None:
        async with self._lock:
            if self._paused:
                return None
            if not self._pending_tasks:
                return None
            if len(self._active_tasks) >= self.max_concurrent_files:
                return None

            task = self._pending_tasks.pop(0)
            self._active_tasks[task.task_id] = task
            return task

    async def task_completed(self, task: FileTask) -> None:
        async with self._lock:
            if task.task_id in self._active_tasks:
                del self._active_tasks[task.task_id]
            self._completed_tasks.append(task)

    async def task_failed(self, task: FileTask) -> None:
        async with self._lock:
            if task.task_id in self._active_tasks:
                del self._active_tasks[task.task_id]
            self._failed_tasks.append(task)

    async def task_cancelled(self, task: FileTask) -> None:
        async with self._lock:
            if task.task_id in self._active_tasks:
                del self._active_tasks[task.task_id]
            self._failed_tasks.append(task)

    def get_optimal_chunks_for_task(self, task: FileTask) -> int:
        if task.is_small_file:
            return 1
        if task.is_large_file:
            return min(self.max_concurrent_chunks_per_file, 8)
        return min(self.max_concurrent_chunks_per_file, 4)

    async def pause(self) -> None:
        async with self._lock:
            self._paused = True

    async def resume(self) -> None:
        async with self._lock:
            self._paused = False

    def get_all_tasks(self) -> list[FileTask]:
        return self._completed_tasks + list(self._active_tasks.values()) + self._pending_tasks + self._failed_tasks

    def get_progress(self) -> BatchProgress:
        completed = self._completed_tasks.copy()
        active = list(self._active_tasks.values())
        pending = self._pending_tasks.copy()
        failed = self._failed_tasks.copy()

        total_files = len(completed) + len(active) + len(pending) + len(failed)
        completed_files = len(completed)
        failed_files = len(failed)
        active_files = len(active)

        total_bytes = sum(t.file_size for t in completed + active + pending if t.file_size > 0)
        downloaded_bytes = sum(t.downloaded for t in completed + active)

        active_speed = sum(t.speed for t in active if t.speed > 0)
        eta: float = -1.0
        if active_speed > 0:
            remaining = total_bytes - downloaded_bytes
            eta = remaining / active_speed

        return BatchProgress(
            total_files=total_files,
            completed_files=completed_files,
            failed_files=failed_files,
            active_files=active_files,
            total_bytes=total_bytes,
            downloaded_bytes=downloaded_bytes,
            overall_speed=active_speed,
            eta=eta,
        )


class AdaptiveConcurrencyController:
    def __init__(
        self,
        initial_concurrency: int = 3,
        min_concurrency: int = 1,
        max_concurrency: int = 10,
        speed_threshold: float = 0.3,
        adjustment_interval: float = 5.0,
        error_threshold: int = 3,
    ) -> None:
        self.initial_concurrency = initial_concurrency
        self.min_concurrency = min_concurrency
        self.max_concurrency = max_concurrency
        self.speed_threshold = speed_threshold
        self.adjustment_interval = adjustment_interval
        self.error_threshold = error_threshold

        self._current_concurrency: int = initial_concurrency
        self._speed_history: list[float] = []
        self._error_count: int = 0
        self._last_adjustment_time: float = 0.0
        self._last_speed: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def current_concurrency(self) -> int:
        return self._current_concurrency

    async def record_speed(self, speed: float) -> None:
        async with self._lock:
            self._speed_history.append(speed)
            if len(self._speed_history) > 10:
                self._speed_history.pop(0)
            self._last_speed = speed

    async def record_error(self) -> None:
        async with self._lock:
            self._error_count += 1
            if self._error_count >= self.error_threshold:
                await self._reduce_concurrency()

    async def record_success(self) -> None:
        async with self._lock:
            self._error_count = max(0, self._error_count - 1)

    async def should_adjust(self) -> bool:
        async with self._lock:
            now = time.time()
            return now - self._last_adjustment_time >= self.adjustment_interval

    async def adjust(self) -> int:
        async with self._lock:
            now = time.time()
            if now - self._last_adjustment_time < self.adjustment_interval:
                return self._current_concurrency

            self._last_adjustment_time = now

            if len(self._speed_history) < 3:
                return self._current_concurrency

            recent_speeds = self._speed_history[-3:]
            avg_speed = sum(recent_speeds) / len(recent_speeds)

            if self._last_speed > 0 and avg_speed > 0:
                speed_change = (self._last_speed - avg_speed) / avg_speed

                if speed_change < -self.speed_threshold and self._current_concurrency < self.max_concurrency:
                    self._current_concurrency = min(self.max_concurrency, self._current_concurrency + 1)
                elif speed_change > self.speed_threshold and self._current_concurrency > self.min_concurrency:
                    self._current_concurrency = max(self.min_concurrency, self._current_concurrency - 1)
                elif speed_change > 0.1 and self._current_concurrency < self.max_concurrency:
                    self._current_concurrency = min(self.max_concurrency, self._current_concurrency + 1)

            return self._current_concurrency

    async def _reduce_concurrency(self) -> None:
        self._current_concurrency = max(self.min_concurrency, self._current_concurrency - 1)
        self._error_count = 0

    async def reset(self) -> None:
        async with self._lock:
            self._current_concurrency = self.initial_concurrency
            self._speed_history.clear()
            self._error_count = 0


class BatchDownloader:
    def __init__(
        self,
        config: DownloadConfig | None = None,
        max_concurrent_files: int = 5,
        max_concurrent_chunks_per_file: int = 4,
        enable_adaptive_concurrency: bool = True,
        enable_small_file_priority: bool = True,
    ) -> None:
        self.config = config or DownloadConfig()
        self.max_concurrent_files = max_concurrent_files
        self.max_concurrent_chunks_per_file = max_concurrent_chunks_per_file
        self.enable_adaptive_concurrency = enable_adaptive_concurrency

        self._scheduler = FileScheduler(
            max_concurrent_files=max_concurrent_files,
            max_concurrent_chunks_per_file=max_concurrent_chunks_per_file,
            enable_small_file_priority=enable_small_file_priority,
        )
        self._concurrency_controller = AdaptiveConcurrencyController(
            initial_concurrency=max(1, max_concurrent_files // 2),
            min_concurrency=1,
            max_concurrency=max_concurrent_files,
        )
        self._connection_pool: ConnectionPool | None = None
        self._running = False
        self._paused = False
        self._cancelled = False
        self._lock = asyncio.Lock()
        self._tasks: dict[str, FileTask] = {}
        self._progress_callback: Any = None
        self._file_complete_callback: Any = None
        self._completed_count: int = 0
        self._total_speed: float = 0.0

    async def add_url(
        self,
        url: str,
        save_path: str | Path = "./downloads",
        filename: str | None = None,
        priority: int = 0,
    ) -> str:
        url = normalize_url(url)
        if not validate_url(url):
            raise DownloadError(f"Invalid URL: {url}")

        task_id = generate_download_id(url)
        save_path = Path(save_path).expanduser().resolve()

        task = FileTask(
            task_id=task_id,
            url=url,
            save_path=save_path,
            filename=filename,
            priority=priority,
        )
        self._tasks[task_id] = task
        await self._scheduler.add_task(task)
        return task_id

    async def add_urls(
        self,
        urls: list[str],
        save_path: str | Path = "./downloads",
    ) -> list[str]:
        task_ids = []
        for url in urls:
            task_id = await self.add_url(url, save_path)
            task_ids.append(task_id)
        return task_ids

    def set_progress_callback(self, callback: Any) -> None:
        self._progress_callback = callback

    def set_file_complete_callback(self, callback: Any) -> None:
        self._file_complete_callback = callback

    async def start(self) -> None:
        if self._running:
            return
        self._running = True

        self._connection_pool = ConnectionPool(self.config)
        await self._connection_pool.initialize()

        await self._batch_probe_all()
        await self._download_loop()

    async def _batch_probe_all(self) -> None:
        pending_tasks = [t for t in self._tasks.values() if t.status == FileTaskStatus.PENDING]
        if not pending_tasks:
            return

        probe_semaphore = asyncio.Semaphore(min(20, len(pending_tasks)))

        async def probe_single(task: FileTask) -> None:
            async with probe_semaphore:
                if self._cancelled:
                    return
                try:
                    await self._probe_single(task)
                except Exception as e:
                    await task.mark_failed(str(e))
                    await self._scheduler.task_failed(task)

        await asyncio.gather(*[probe_single(t) for t in pending_tasks], return_exceptions=True)

    async def _probe_single(self, task: FileTask) -> None:
        await task.mark_probing()

        client = self._connection_pool.client if self._connection_pool else None
        if not client:
            raise DownloadError("Connection pool not initialized")

        from .connection import RequestBuilder

        builder = RequestBuilder(self.config)
        request_config = builder.build_head_request(task.url)

        try:
            response = await client.head(
                request_config["url"],
                headers=request_config["headers"],
                follow_redirects=request_config["follow_redirects"],
            )
        except Exception as e:
            raise DownloadError(f"Failed to probe URL: {e}") from None

        if response.status_code >= 400:
            raise DownloadError(f"HTTP {response.status_code}")

        task.file_size = (
            int(response.headers.get("Content-Length", 0)) if response.headers.get("Content-Length") else -1
        )
        task.supports_range = response.headers.get("Accept-Ranges", "").lower() == "bytes"

        content_disposition = response.headers.get("Content-Disposition")
        if content_disposition and not task.filename:
            from .utils import parse_content_disposition

            task.filename = parse_content_disposition(content_disposition)

        if not task.filename:
            from .utils import determine_filename

            task.filename = determine_filename(task.url, content_disposition, response.headers.get("Content-Type"))

        if task.supports_range and task.file_size > 0:
            task.chunks = self._scheduler.get_optimal_chunks_for_task(task)

        task.status = FileTaskStatus.PENDING

    async def _download_loop(self) -> None:
        download_tasks: dict[str, asyncio.Task[None]] = {}
        last_progress_time = 0.0
        progress_interval = 0.5

        async def download_file(task: FileTask) -> None:
            try:
                await self._download_single_file(task)
            except Exception as e:
                if not task.is_failed:
                    await task.mark_failed(str(e))
                    await self._scheduler.task_failed(task)

        while self._running:
            if self._cancelled:
                for t in download_tasks.values():
                    t.cancel()
                break

            while self._paused:
                await asyncio.sleep(0.1)
                if self._cancelled:
                    break

            concurrency_limit = (
                self._concurrency_controller.current_concurrency
                if self.enable_adaptive_concurrency
                else self.max_concurrent_files
            )

            while len(download_tasks) < concurrency_limit:
                task = await self._scheduler.get_next_task()
                if task is None:
                    break
                download_tasks[task.task_id] = asyncio.create_task(download_file(task))

            done_tasks = [tid for tid, t in download_tasks.items() if t.done()]
            for tid in done_tasks:
                task = download_tasks.pop(tid)
                with contextlib.suppress(asyncio.CancelledError):
                    await task

            if self.enable_adaptive_concurrency and await self._concurrency_controller.should_adjust():
                progress = self._scheduler.get_progress()
                self._total_speed = progress.overall_speed
                await self._concurrency_controller.record_speed(progress.overall_speed)
                await self._concurrency_controller.adjust()

            now = time.time()
            if self._progress_callback and (now - last_progress_time) >= progress_interval:
                last_progress_time = now
                progress = self._scheduler.get_progress()
                try:
                    result = self._progress_callback(
                        progress.completed_files,
                        progress.total_files,
                        progress.overall_speed,
                        int(progress.eta) if progress.eta > 0 else -1,
                    )
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    pass

            if not download_tasks and self._scheduler.pending_count == 0 and self._scheduler.active_count == 0:
                break

            await asyncio.sleep(0.05)

        if download_tasks:
            await asyncio.gather(*download_tasks.values(), return_exceptions=True)

    async def _download_single_file(self, task: FileTask) -> None:
        await task.mark_downloading()

        file_config = DownloadConfig(
            enable_chunking=self.config.enable_chunking and task.supports_range,
            max_chunks=task.chunks,
            min_chunks=1,
            buffer_size=self.config.buffer_size,
            timeout=self.config.timeout,
            connect_timeout=self.config.connect_timeout,
            read_timeout=self.config.read_timeout,
            write_timeout=self.config.write_timeout,
            resume=self.config.resume,
            verify_ssl=self.config.verify_ssl,
            user_agent=self.config.user_agent,
            headers=self.config.headers.copy(),
            proxy=self.config.proxy,
            speed_limit=self.config.speed_limit,
            retry=self.config.retry,
            follow_redirects=self.config.follow_redirects,
            max_redirects=self.config.max_redirects,
        )

        downloader = Downloader(config=file_config)
        if self._connection_pool:
            downloader.set_connection_pool(self._connection_pool)

        try:
            await downloader.download(
                url=task.url,
                save_path=str(task.save_path),
                filename=task.filename,
                resume=self.config.resume,
            )
            await task.mark_completed()
            await self._scheduler.task_completed(task)
            await self._concurrency_controller.record_success()

            if self._file_complete_callback:
                with contextlib.suppress(Exception):
                    result = self._file_complete_callback(task)
                    if asyncio.iscoroutine(result):
                        await result

        except Exception as e:
            await self._concurrency_controller.record_error()
            if task.retry_count < self.config.retry.max_retries:
                await task.reset_for_retry()
                await self._scheduler.add_task(task)
            else:
                await task.mark_failed(str(e))
                await self._scheduler.task_failed(task)

    async def pause(self) -> None:
        async with self._lock:
            self._paused = True
            await self._scheduler.pause()

    async def resume(self) -> None:
        async with self._lock:
            self._paused = False
            await self._scheduler.resume()

    async def cancel(self) -> None:
        async with self._lock:
            self._cancelled = True
            self._running = False
            for task in self._tasks.values():
                if task.is_active:
                    await task.mark_cancelled()
                    await self._scheduler.task_cancelled(task)

    async def stop(self) -> None:
        self._running = False
        if self._connection_pool:
            await self._connection_pool.close()

    def get_task(self, task_id: str) -> FileTask | None:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> list[FileTask]:
        return self._scheduler.get_all_tasks()

    def get_progress(self) -> BatchProgress:
        return self._scheduler.get_progress()

    def get_stats(self) -> dict[str, Any]:
        progress = self.get_progress()
        return {
            "total_files": progress.total_files,
            "completed_files": progress.completed_files,
            "failed_files": progress.failed_files,
            "active_files": progress.active_files,
            "pending_files": self._scheduler.pending_count,
            "total_bytes": progress.total_bytes,
            "downloaded_bytes": progress.downloaded_bytes,
            "progress_percent": progress.progress,
            "overall_speed": progress.overall_speed,
            "current_concurrency": self._concurrency_controller.current_concurrency,
        }


class SharedConnectionBatchDownloader(BatchDownloader):
    def __init__(self, config: DownloadConfig | None = None, **kwargs: Any) -> None:
        super().__init__(config, **kwargs)


async def batch_download(
    urls: list[str],
    save_path: str = "./downloads",
    config: DownloadConfig | None = None,
    max_concurrent_files: int = 5,
    max_concurrent_chunks_per_file: int = 4,
    progress_callback: Any = None,
    file_complete_callback: Any = None,
) -> list[tuple[str, Path | None, str | None]]:
    downloader = BatchDownloader(
        config=config,
        max_concurrent_files=max_concurrent_files,
        max_concurrent_chunks_per_file=max_concurrent_chunks_per_file,
    )

    if progress_callback:
        downloader.set_progress_callback(progress_callback)
    if file_complete_callback:
        downloader.set_file_complete_callback(file_complete_callback)

    await downloader.add_urls(urls, save_path)
    await downloader.start()

    results: list[tuple[str, Path | None, str | None]] = []
    for task in downloader.get_all_tasks():
        if task.is_completed:
            final_path = task.save_path / (task.filename or "unknown")
            results.append((task.url, final_path, None))
        else:
            results.append((task.url, None, task.error))

    return results


def batch_download_sync(
    urls: list[str],
    save_path: str = "./downloads",
    config: DownloadConfig | None = None,
    **kwargs: Any,
) -> list[tuple[str, Path | None, str | None]]:
    return asyncio.run(
        batch_download(
            urls=urls,
            save_path=save_path,
            config=config,
            **kwargs,
        )
    )
