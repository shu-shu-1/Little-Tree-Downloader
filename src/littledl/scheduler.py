import asyncio
import contextlib
import time
from dataclasses import dataclass, field

from .chunk import Chunk, ChunkManager
from .config import DownloadConfig
from .monitor import DownloadMonitor
from .utils import MovingAverage


@dataclass
class SchedulerStats:
    active_workers: int = 0
    pending_chunks: int = 0
    slow_chunks: list[int] = field(default_factory=list)
    resplit_count: int = 0
    current_speed: float = 0.0
    average_speed: float = 0.0
    speed_trend: float = 0.0
    last_adjustment: float = 0.0
    adjustments_today: int = 0


class SmartScheduler:
    def __init__(
        self,
        chunk_manager: ChunkManager,
        config: DownloadConfig,
        monitor: DownloadMonitor | None = None,
    ) -> None:
        self.chunk_manager = chunk_manager
        self.config = config
        self.monitor = monitor
        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._last_resplit_time: float = 0.0
        self._resplit_count: int = 0
        self._speed_average = MovingAverage(window_size=10)
        self._last_adjustment_time: float = 0.0
        self._adjustment_count: int = 0
        self._lock = asyncio.Lock()
        self._current_workers: int = 0
        self._target_workers: int = 0

    @property
    def max_workers(self) -> int:
        return self.config.max_chunks

    @property
    def min_workers(self) -> int:
        return self.config.min_chunks

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        if self.config.enable_adaptive or self.config.enable_smart_resplit:
            self._task = asyncio.create_task(self._scheduler_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    async def _scheduler_loop(self) -> None:
        while self._running:
            try:
                await self._run_adaptive_adjustments()
                if self.config.enable_smart_resplit:
                    await self._check_slow_chunks()
                await asyncio.sleep(self.config.adaptive_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)

    async def _run_adaptive_adjustments(self) -> None:
        if not self.config.enable_adaptive:
            return
        if not self.monitor:
            return
        stats = self.monitor.get_stats()
        current_speed = stats.speed
        self._speed_average.add(current_speed)
        self._speed_average.get_average()
        trend = self._speed_average.get_trend()
        now = time.time()
        cooldown = 5.0
        if now - self._last_adjustment_time < cooldown:
            return
        if trend < -0.3 and self._current_workers > self.min_workers or trend > 0.2 and self._current_workers < self.max_workers:
            self._adjustment_count += 1
            self._last_adjustment_time = now

    async def _check_slow_chunks(self) -> None:
        if not self.config.enable_smart_resplit:
            return
        slow_chunks = self.chunk_manager.get_slow_chunks(self.config.resplit_threshold)
        now = time.time()
        if now - self._last_resplit_time < self.config.resplit_cooldown:
            return
        for chunk in slow_chunks:
            if chunk.can_resplit(self.config.resplit_cooldown) and await self._resplit_chunk(chunk):
                self._resplit_count += 1
                self._last_resplit_time = now
                break

    async def _resplit_chunk(self, chunk: Chunk) -> bool:
        async with self._lock:
            if chunk.remaining < self.config.min_chunk_size:
                return False
            if chunk.progress > 80:
                return False
            new_chunks = self.chunk_manager.resplit_chunk(chunk.index)
            return new_chunks

    def get_stats(self) -> SchedulerStats:
        avg_speed = self._speed_average.get_average()
        trend = self._speed_average.get_trend()
        slow_chunks = [c.index for c in self.chunk_manager.get_slow_chunks(self.config.resplit_threshold)]
        return SchedulerStats(
            active_workers=self._current_workers,
            pending_chunks=len(self.chunk_manager.pending_chunks),
            slow_chunks=slow_chunks,
            resplit_count=self._resplit_count,
            current_speed=avg_speed,
            average_speed=avg_speed,
            speed_trend=trend,
            last_adjustment=self._last_adjustment_time,
            adjustments_today=self._adjustment_count,
        )

    def register_worker(self) -> None:
        self._current_workers += 1

    def unregister_worker(self) -> None:
        self._current_workers = max(0, self._current_workers - 1)

    def should_spawn_worker(self) -> bool:
        pending = len(self.chunk_manager.pending_chunks)
        active = self._current_workers
        return pending > 0 and active < self.max_workers

    def get_optimal_worker_count(self) -> int:
        if not self.monitor:
            return self.config.max_chunks
        stats = self.monitor.get_stats()
        if stats.total_size <= 0:
            return self.config.min_chunks
        pending = len(self.chunk_manager.pending_chunks)
        if pending <= 0:
            return self._current_workers
        optimal = min(self.config.max_chunks, pending)
        if self._speed_average.get_trend() < -0.2:
            optimal = max(self.config.min_chunks, optimal - 1)
        return optimal


class AdaptiveChunkSizer:
    def __init__(self, config: DownloadConfig) -> None:
        self.config = config
        self._speed_history: list[float] = []
        self._chunk_size_history: list[int] = []
        self._optimal_chunk_size: int = config.chunk_size

    @property
    def optimal_chunk_size(self) -> int:
        return self._optimal_chunk_size

    def record_sample(self, speed: float, chunk_size: int) -> None:
        self._speed_history.append(speed)
        self._chunk_size_history.append(chunk_size)
        if len(self._speed_history) > 20:
            self._speed_history.pop(0)
            self._chunk_size_history.pop(0)

    def calculate_optimal_chunk_size(self, current_speed: float) -> int:
        if current_speed <= 0:
            return self._optimal_chunk_size
        target_chunk_time = 2.0
        ideal_size = int(current_speed * target_chunk_time)
        ideal_size = max(self.config.min_chunk_size, ideal_size)
        ideal_size = min(self.config.max_chunk_size, ideal_size)
        if len(self._speed_history) >= 5:
            avg_speed = sum(self._speed_history[-5:]) / 5
            current_trend = (current_speed - avg_speed) / max(avg_speed, 1)
            if current_trend > 0.3:
                ideal_size = int(ideal_size * 1.1)
            elif current_trend < -0.3:
                ideal_size = int(ideal_size * 0.9)
        self._optimal_chunk_size = ideal_size
        return ideal_size

    def suggest_chunk_count(self, file_size: int, speed: float) -> int:
        optimal_size = self.calculate_optimal_chunk_size(speed)
        chunks = file_size // optimal_size
        chunks = max(self.config.min_chunks, chunks)
        chunks = min(self.config.max_chunks, chunks)
        return chunks


class ConnectionOptimizer:
    def __init__(self) -> None:
        self._connection_times: list[float] = []
        self._download_times: list[float] = []
        self._error_count: int = 0
        self._last_error_time: float = 0.0

    def record_connection_time(self, duration: float) -> None:
        self._connection_times.append(duration)
        if len(self._connection_times) > 20:
            self._connection_times.pop(0)

    def record_download_time(self, duration: float) -> None:
        self._download_times.append(duration)
        if len(self._download_times) > 20:
            self._download_times.pop(0)

    def record_error(self) -> None:
        self._error_count += 1
        self._last_error_time = time.time()

    def get_average_connection_time(self) -> float:
        if not self._connection_times:
            return 0.0
        return sum(self._connection_times) / len(self._connection_times)

    def get_average_download_time(self) -> float:
        if not self._download_times:
            return 0.0
        return sum(self._download_times) / len(self._download_times)

    def should_reduce_concurrency(self) -> bool:
        if self._error_count >= 3:
            if time.time() - self._last_error_time < 60:
                return True
            self._error_count = 0
        if len(self._connection_times) >= 5:
            avg_conn = self.get_average_connection_time()
            if avg_conn > 5.0:
                return True
        return False

    def can_increase_concurrency(self) -> bool:
        if self._error_count > 0:
            return False
        if len(self._connection_times) >= 5:
            avg_conn = self.get_average_connection_time()
            if avg_conn > 2.0:
                return False
        return True

    def reset_errors(self) -> None:
        self._error_count = 0
