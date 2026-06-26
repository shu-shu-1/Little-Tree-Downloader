import asyncio
import contextlib
import statistics
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

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
        self._speed_ewma = MovingAverage(window_size=20)
        self._last_adjustment_time: float = 0.0
        self._adjustment_count: int = 0
        self._lock = asyncio.Lock()
        self._current_workers: int = 0
        self._target_workers: int = 0
        self._last_speed: float = 0.0
        self._chunk_resplit_count: dict[int, int] = {}

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
        avg_speed = self._speed_average.get_average()
        trend = self._speed_average.get_trend()
        previous_speed = self._last_speed
        self._last_speed = current_speed
        now = time.time()
        cooldown = max(2.0, self.config.adaptive_interval)
        if now - self._last_adjustment_time < cooldown:
            return

        self._speed_ewma.add(current_speed)
        ewma_avg = self._speed_ewma.get_average()
        if ewma_avg <= 0:
            ewma_avg = current_speed
        if previous_speed <= 0:
            speed_gain = 0.0
        else:
            speed_gain = (current_speed - previous_speed) / max(previous_speed, 1.0)
            ewma_speed_diff = (current_speed - ewma_avg) / max(ewma_avg, 1.0)
            speed_gain = speed_gain * 0.6 + ewma_speed_diff * 0.4

        if self._target_workers <= 0:
            self._target_workers = max(self.min_workers, self._current_workers)

        changed = False
        if self.config.enable_hybrid_turbo:
            if (
                trend > 0.1
                and speed_gain >= self.config.hybrid_speedup_threshold
                and self._target_workers < self.max_workers
            ):
                self._target_workers = min(
                    self.max_workers,
                    self._target_workers + self.config.hybrid_aimd_increase_step,
                )
                changed = True
            elif (
                trend < -0.12 or speed_gain < -self.config.hybrid_speedup_threshold
            ) and self._target_workers > self.min_workers:
                self._target_workers = max(
                    self.min_workers,
                    int(self._target_workers * self.config.hybrid_aimd_decrease_factor),
                )
                changed = True
        else:
            if trend > 0.2 and self._target_workers < self.max_workers:
                self._target_workers += 1
                changed = True
            elif trend < -0.3 and self._target_workers > self.min_workers:
                self._target_workers -= 1
                changed = True

        # 速度非常低时触发保护，避免盲目维持高并发。
        if avg_speed > 0 and current_speed < avg_speed * 0.4 and self._target_workers > self.min_workers:
            self._target_workers = max(self.min_workers, self._target_workers - 1)
            changed = True

        if changed:
            self._adjustment_count += 1
            self._last_adjustment_time = now

    async def _check_slow_chunks(self) -> None:
        if not self.config.enable_smart_resplit:
            return
        threshold = self.config.resplit_threshold
        if self.config.enable_hybrid_turbo:
            threshold = self.config.hybrid_slow_chunk_ratio
        slow_chunks = self.chunk_manager.get_slow_chunks(threshold)
        if not slow_chunks:
            return
        now = time.time()
        if now - self._last_resplit_time < self.config.resplit_cooldown:
            return
        active_chunks = self.chunk_manager.active_chunks
        max_slow_to_process = max(1, int(len(active_chunks) ** 0.5))
        global_avg_speed = self._speed_ewma.get_average() if self.monitor else 0.0
        processed = 0
        for chunk in slow_chunks:
            if processed >= max_slow_to_process:
                break
            if chunk.remaining < self.config.hybrid_min_remaining_bytes:
                continue
            resplit_times = self._chunk_resplit_count.get(chunk.index, 0)
            if resplit_times >= self.config.hybrid_max_resplit_per_chunk:
                continue
            if chunk.can_resplit(self.config.resplit_cooldown, global_avg_speed) and await self._resplit_chunk(
                chunk, resplit_times
            ):
                self._resplit_count += 1
                self._chunk_resplit_count[chunk.index] = resplit_times + 1
                self._last_resplit_time = now
                processed += 1

    async def _resplit_chunk(self, chunk: Chunk, resplit_times: int = 0) -> bool:
        async with self._lock:
            if chunk.remaining < self.config.min_chunk_size:
                return False
            if chunk.progress > 75:
                return False
            num_splits = min(2 + resplit_times, 4)
            new_chunks = self.chunk_manager.resplit_chunk(
                chunk.index,
                num_splits,
                bypass_can_resplit=True,
            )
            return new_chunks is not None and len(new_chunks) > 0

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
        limit = self.max_workers if self._target_workers <= 0 else min(self._target_workers, self.max_workers)
        return pending > 0 and active < limit

    def get_optimal_worker_count(self) -> int:
        if not self.monitor:
            return self.config.max_chunks
        stats = self.monitor.get_stats()
        if stats.total_size <= 0:
            return self.config.min_chunks
        pending = len(self.chunk_manager.pending_chunks)
        if pending <= 0:
            return self._current_workers
        target = self._target_workers if self._target_workers > 0 else self.config.max_chunks
        optimal = min(target, pending, self.config.max_chunks)
        if self._speed_average.get_trend() < -0.2:
            optimal = max(self.config.min_chunks, optimal - 1)
        return optimal


# ---------------------------------------------------------------------------
# FUSION Algorithm – 4-phase adaptive scheduler
# ---------------------------------------------------------------------------


class FusionPhase(Enum):
    """FUSION 算法的四个阶段"""

    PROBE = "probe"  # 探测期：快速测量带宽天花板
    RAMP = "ramp"  # 爬升期：指数增长找到最优并发
    CRUISE = "cruise"  # 巡航期：AIMD++ 稳定高速下载
    TAIL = "tail"  # 收尾期：激进抢占，微分片冲刺


@dataclass
class BandwidthEstimate:
    """带宽天花板估算"""

    ceiling: float = 0.0  # 观测到的最大总吞吐 (bytes/s)
    per_conn_avg: float = 0.0  # 每连接平均速度
    server_throttled: bool = False  # 服务器是否限速单连接
    samples: int = 0

    @property
    def at_ceiling(self) -> bool:
        """当前速度是否接近天花板"""
        return self.ceiling > 0 and self.samples >= 3


@dataclass
class FusionStats:
    """FUSION 调度统计"""

    phase: str = "probe"
    active_workers: int = 0
    target_workers: int = 0
    pending_chunks: int = 0
    bandwidth_ceiling: float = 0.0
    per_conn_speed: float = 0.0
    server_throttled: bool = False
    plateau_reached: bool = False
    ramp_rounds: int = 0
    resplit_count: int = 0
    phase_transitions: int = 0
    current_speed: float = 0.0
    p50_speed: float = 0.0
    speed_trend: float = 0.0


class BandwidthEstimator:
    """
    带宽天花板估算器

    通过追踪聚合吞吐和每连接速度来推断：
    - 总带宽上限（ceiling）
    - 服务器是否对单连接限速
    - 增加连接是否还有边际收益
    """

    def __init__(self, ewma_alpha: float = 0.2) -> None:
        self._alpha = ewma_alpha
        self._ceiling_ewma: float = 0.0
        self._speed_history: list[float] = []
        self._per_conn_history: list[float] = []
        self._samples: int = 0
        self._last_chunk_count: int = 0
        self._speed_at_count: dict[int, list[float]] = {}

    def record(self, aggregate_speed: float, active_chunks: int) -> BandwidthEstimate:
        """记录一次速度采样"""
        self._samples += 1
        self._speed_history.append(aggregate_speed)
        if len(self._speed_history) > 60:
            self._speed_history.pop(0)

        # 更新天花板 EWMA
        if aggregate_speed > self._ceiling_ewma:
            self._ceiling_ewma = (
                self._alpha * aggregate_speed + (1 - self._alpha) * self._ceiling_ewma
                if self._ceiling_ewma > 0
                else aggregate_speed
            )
        else:
            # 慢衰减：只用很小的权重向下修正天花板
            self._ceiling_ewma = 0.98 * self._ceiling_ewma + 0.02 * aggregate_speed

        # 记录每连接速度
        per_conn = aggregate_speed / max(active_chunks, 1)
        self._per_conn_history.append(per_conn)
        if len(self._per_conn_history) > 30:
            self._per_conn_history.pop(0)

        # 记录指定并发数下的速度
        self._speed_at_count.setdefault(active_chunks, [])
        self._speed_at_count[active_chunks].append(aggregate_speed)
        if len(self._speed_at_count[active_chunks]) > 10:
            self._speed_at_count[active_chunks].pop(0)
        self._last_chunk_count = active_chunks

        # 检测服务器限速
        server_throttled = self._detect_throttle()

        return BandwidthEstimate(
            ceiling=self._ceiling_ewma,
            per_conn_avg=sum(self._per_conn_history[-5:]) / min(5, len(self._per_conn_history)),
            server_throttled=server_throttled,
            samples=self._samples,
        )

    def _detect_throttle(self) -> bool:
        """检测服务器是否对单连接限速

        原理：如果增加并发数后，每连接速度几乎不变（即总速度近似线性增长），
        说明服务器不限速。如果每连接速度随并发增加而等比下降，说明带宽被均分。
        """
        if len(self._per_conn_history) < 6:
            return False
        recent_per_conn = self._per_conn_history[-5:]
        mean = sum(recent_per_conn) / len(recent_per_conn)
        if mean <= 0:
            return False
        # 变异系数 < 0.15 说明每连接速度非常稳定，服务器可能有限速
        cv = (sum((s - mean) ** 2 for s in recent_per_conn) / len(recent_per_conn)) ** 0.5 / mean
        return bool(cv < 0.15)

    def marginal_gain(self, from_count: int, to_count: int) -> float:
        """计算从 from_count 增加到 to_count 的边际收益"""
        speeds_from = self._speed_at_count.get(from_count, [])
        speeds_to = self._speed_at_count.get(to_count, [])
        if not speeds_from or not speeds_to:
            return 1.0  # 未知时假设有收益
        avg_from = sum(speeds_from[-3:]) / min(3, len(speeds_from))
        avg_to = sum(speeds_to[-3:]) / min(3, len(speeds_to))
        if avg_from <= 0:
            return 1.0
        return (avg_to - avg_from) / avg_from

    def near_ceiling(self, current_speed: float) -> bool:
        """当前速度是否接近天花板"""
        if self._ceiling_ewma <= 0 or self._samples < 3:
            return False
        return current_speed >= self._ceiling_ewma * 0.90

    @property
    def ceiling(self) -> float:
        return self._ceiling_ewma

    @property
    def p50_speed(self) -> float:
        """中位数速度，比均值更抗抖动"""
        if not self._speed_history:
            return 0.0
        return statistics.median(self._speed_history[-20:])


class FusionScheduler:
    """
    FUSION 调度器 — 又快又稳的核心算法

    四阶段自适应:
      1. PROBE  — 少量连接探测带宽天花板和服务器特征
      2. RAMP   — 指数增长并发，每轮检测边际收益，收益 < 阈值即停
      3. CRUISE — AIMD++ 巡航：带天花板感知的加性增/乘性减
      4. TAIL   — 剩余 < 20% 时激进抢占：微分片 + 临时超限并发

    关键创新:
      - 带宽天花板追踪 (BandwidthEstimator): 不做无用的并发增长
      - P50 速度: 用中位数代替均值，天然抗抖动
      - 边际收益检测: 只在确认有效时才增加并发
      - 收尾冲刺: 最后 20% 主动拆分慢块 + 临时扩容
    """

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
        self._lock = asyncio.Lock()

        # Phase state
        self._phase = FusionPhase.PROBE
        self._phase_start_time: float = 0.0
        self._phase_transitions: int = 0

        # Worker tracking
        self._current_workers: int = 0
        self._target_workers: int = config.fusion_probe_chunks

        # Bandwidth estimation
        self._bw = BandwidthEstimator(ewma_alpha=config.fusion_ceiling_ewma_alpha)

        # Speed tracking
        self._speed_avg = MovingAverage(window_size=20)
        self._speed_history: list[float] = []
        self._last_speed: float = 0.0

        # Ramp state
        self._ramp_rounds: int = 0
        self._ramp_prev_speed: float = 0.0
        self._plateau_reached: bool = False

        # Cruise state
        self._last_adjustment_time: float = 0.0
        self._adjustment_count: int = 0
        # 天花板锁定：接近带宽上限时锁定并发 hold 一段时间，消除天花板处的锯齿。
        self._ceiling_lock_until: float = 0.0

        # Resplit state
        self._last_resplit_time: float = 0.0
        self._resplit_count: int = 0
        self._chunk_resplit_count: dict[int, int] = {}

        # Tail state
        self._tail_entered: bool = False

    @property
    def max_workers(self) -> int:
        if self._phase == FusionPhase.TAIL:
            return self.config.max_chunks + self.config.fusion_tail_boost
        return self.config.max_chunks

    @property
    def min_workers(self) -> int:
        return self.config.min_chunks

    # -- Lifecycle --

    async def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._phase_start_time = time.time()
        self._task = asyncio.create_task(self._scheduler_loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

    # -- Main loop --

    async def _scheduler_loop(self) -> None:
        while self._running:
            try:
                await self._tick()
                await asyncio.sleep(self.config.adaptive_interval)
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1.0)

    async def _tick(self) -> None:
        """每个调度周期执行一次"""
        if not self.monitor:
            return

        stats = self.monitor.get_stats()
        current_speed = stats.speed
        self._speed_avg.add(current_speed)
        self._speed_history.append(current_speed)
        if len(self._speed_history) > 60:
            self._speed_history.pop(0)

        # 更新带宽估算
        bw_est = self._bw.record(current_speed, self._current_workers)

        # 检查阶段转换
        self._check_phase_transition(stats, bw_est)

        # 执行当前阶段逻辑
        if self._phase == FusionPhase.PROBE:
            await self._do_probe(current_speed, bw_est)
        elif self._phase == FusionPhase.RAMP:
            await self._do_ramp(current_speed, bw_est)
        elif self._phase == FusionPhase.CRUISE:
            await self._do_cruise(current_speed, bw_est)
        elif self._phase == FusionPhase.TAIL:
            await self._do_tail(current_speed, bw_est)

        # 慢块检测（所有阶段都做）
        if self.config.enable_smart_resplit:
            await self._check_slow_chunks(bw_est)

        self._last_speed = current_speed

    def _check_phase_transition(self, stats: Any, bw_est: BandwidthEstimate) -> None:
        """检查是否应该切换阶段"""
        now = time.time()
        elapsed = now - self._phase_start_time

        if self._phase == FusionPhase.PROBE:
            # 只需 1 个有效采样即可得到带宽基线：RAMP 会逐轮精修，无需等待
            # 完整 probe_duration 与两次采样，避免“前几秒很慢”的启动观感。
            min_elapsed = min(self.config.fusion_probe_duration, self.config.adaptive_interval)
            if elapsed >= min_elapsed and bw_est.samples >= 1:
                self._transition_to(FusionPhase.RAMP)

        elif self._phase == FusionPhase.RAMP and (
            self._plateau_reached
            or self._target_workers >= self.config.max_chunks
            or self._ramp_rounds >= self.config.fusion_ramp_max_rounds
        ):
            # 爬升期结束条件：达到平台 / 达到最大并发 / 超过最大轮数
            self._transition_to(FusionPhase.CRUISE)

        # 任何阶段都可以进入 TAIL（除了已经在 TAIL）
        if self._phase != FusionPhase.TAIL and self._should_enter_tail(stats):
            self._transition_to(FusionPhase.TAIL)

    def _should_enter_tail(self, stats: Any) -> bool:
        total_size = stats.total_size if stats.total_size > 0 else self.chunk_manager.file_size
        if total_size <= 0:
            return False

        remaining_ratio = (total_size - stats.downloaded) / total_size
        if remaining_ratio <= self.config.fusion_tail_ratio:
            return True

        incomplete_chunks = sum(1 for c in self.chunk_manager.chunks if not c.is_completed)
        soft_tail_ratio = max(self.config.fusion_tail_ratio * 2, 0.35)
        return incomplete_chunks <= 3 and remaining_ratio <= soft_tail_ratio

    def _transition_to(self, new_phase: FusionPhase) -> None:
        """切换阶段"""
        if new_phase == self._phase:
            return
        self._phase = new_phase
        self._phase_start_time = time.time()
        self._phase_transitions += 1

        if new_phase == FusionPhase.RAMP:
            self._plateau_reached = False
            self._ramp_prev_speed = self._speed_avg.get_average()
            self._ramp_rounds = 0
        elif new_phase == FusionPhase.CRUISE:
            self._last_adjustment_time = time.time()
        elif new_phase == FusionPhase.TAIL:
            self._tail_entered = True

    # -- Phase: PROBE --

    async def _do_probe(self, current_speed: float, bw_est: BandwidthEstimate) -> None:
        """探测期：用少量连接快速评估带宽"""
        # 保持 probe_chunks 个并发，只收集数据
        self._target_workers = self.config.fusion_probe_chunks

    # -- Phase: RAMP --

    async def _do_ramp(self, current_speed: float, bw_est: BandwidthEstimate) -> None:
        """
        爬升期：指数增长并发，每轮检查边际收益

        策略：每轮翻倍并发数，等 1-2 个采样周期后测量速度提升。
        如果增速 < plateau_threshold，判定达到平台，停止爬升。
        """
        now = time.time()
        # 每轮等一个调度周期即可测量速度提升（旧值为 1.5 个周期，爬升过慢）。
        if now - self._phase_start_time < self.config.adaptive_interval:
            return

        avg_speed = self._speed_avg.get_average()
        gain = (avg_speed - self._ramp_prev_speed) / self._ramp_prev_speed if self._ramp_prev_speed > 0 else 1.0

        if gain < self.config.fusion_plateau_threshold and self._ramp_rounds > 0:
            # 边际收益不足，达到平台
            self._plateau_reached = True
            return

        # 还有收益，继续增长（乘性），但限制单轮增幅，避免突发并发冲击
        # 网络/服务器后造成速度回落——这是“前快后回落”抖动的主因之一。
        self._ramp_prev_speed = avg_speed
        new_target = min(
            self.config.max_chunks,
            int(self._target_workers * self.config.fusion_ramp_multiplier),
        )
        # 至少 +1
        new_target = max(new_target, self._target_workers + 1)
        # 单轮新增并发不超过 fusion_ramp_max_step，把指数爬升变成更平滑的阶梯
        new_target = min(new_target, self._target_workers + self.config.fusion_ramp_max_step)
        self._target_workers = min(new_target, self.config.max_chunks)
        self._ramp_rounds += 1
        self._phase_start_time = time.time()  # 重置计时器等下一轮

    # -- Phase: CRUISE --

    async def _do_cruise(self, current_speed: float, bw_est: BandwidthEstimate) -> None:
        """
        巡航期：AIMD++ 带天花板感知 + 天花板锁定

        核心改进（让巡航更像 IDM 的平稳）：
          - 所有判断统一使用平滑后的均值速度（decision_speed），不再用单次瞬时
            速度触发增减，消除单点抖动导致的误判。
          - 天花板锁定：接近带宽上限时锁定并发 hold 一段时长，期间只减不增，
            消除天花板处的“加-减-加”锯齿。
        """
        now = time.time()
        cooldown = max(2.0, self.config.adaptive_interval)
        if now - self._last_adjustment_time < cooldown:
            return

        avg_speed = self._speed_avg.get_average()
        trend = self._speed_avg.get_trend()

        # 用 P50（抗抖动）作为速度变化基线
        p50 = self._bw.p50_speed

        # 判断基线统一采用平滑后的均值，避免瞬时抖动触发误判
        decision_speed = avg_speed if avg_speed > 0 else current_speed
        baseline = p50 if p50 > 0 else decision_speed
        speed_change = (decision_speed - baseline) / max(baseline, 1.0) if baseline > 0 else 0.0

        # 天花板锁定：命中或刚减并发都刷新锁定，锁定期内不再加性增
        near_top = self._bw.near_ceiling(decision_speed)
        if near_top:
            self._ceiling_lock_until = max(self._ceiling_lock_until, now + self.config.fusion_ceiling_lock_duration)
        ceiling_locked = now < self._ceiling_lock_until

        changed = False

        # 稳定性检查：方差过大先降（用更长窗口，避免一次抖动即降）
        if len(self._speed_history) >= 7:
            recent = self._speed_history[-7:]
            mean_recent = sum(recent) / len(recent)
            if mean_recent > 0:
                cv = (sum((s - mean_recent) ** 2 for s in recent) / len(recent)) ** 0.5 / mean_recent
                if cv > (1 - self.config.fusion_stability_floor) and self._target_workers > self.min_workers:
                    self._target_workers = max(self.min_workers, self._target_workers - 1)
                    # 不稳定 → 刷新锁定，避免刚降下去又被趋势加回
                    self._ceiling_lock_until = now + self.config.fusion_ceiling_lock_duration
                    changed = True

        if not changed:
            if ceiling_locked or near_top:
                # 锁定期 / 命中天花板：保持并发，hold
                pass
            # 拥塞信号：要求“平滑均值相对 P50 显著下降”且“趋势确认”，缺一不降
            elif speed_change < -self.config.fusion_congestion_drop and trend < -0.05:
                self._target_workers = max(
                    self.min_workers,
                    int(self._target_workers * self.config.fusion_cruise_decrease_factor),
                )
                self._ceiling_lock_until = now + self.config.fusion_ceiling_lock_duration
                changed = True
            # 正向趋势 + 未达天花板 → 加性增
            elif trend > 0.05 and speed_change >= 0 and self._target_workers < self.config.max_chunks:
                # 只在边际收益可能存在时增加
                mg = self._bw.marginal_gain(self._target_workers, self._target_workers + 1)
                if mg > self.config.fusion_plateau_threshold or mg >= 1.0:
                    self._target_workers = min(
                        self.config.max_chunks,
                        self._target_workers + self.config.fusion_cruise_increase_step,
                    )
                    changed = True

        # 速度极低保护：要求“持续下滑（trend 明显为负）”才减并发，单个抖动不再误降。
        if (
            p50 > 0
            and decision_speed < p50 * 0.35
            and avg_speed > 0
            and trend < -0.1
            and self._target_workers > self.min_workers
        ):
            self._target_workers = max(self.min_workers, self._target_workers - 1)
            self._ceiling_lock_until = now + self.config.fusion_ceiling_lock_duration
            changed = True

        if changed:
            self._adjustment_count += 1
            self._last_adjustment_time = now

    # -- Phase: TAIL --

    async def _do_tail(self, current_speed: float, bw_est: BandwidthEstimate) -> None:
        """
        收尾期：激进优化最后一段

        - 临时提高并发上限 (+fusion_tail_boost)
        - 主动拆分所有慢块
        - 微分片：小于阈值的块不再拆分
        """
        # 允许超过常规 max_chunks：直接把目标并发拉到能覆盖待处理块的上限，
        # 而非每轮 +2 缓慢爬升——收尾阶段应当尽快跑满，避免“最后一点卡很久”。
        tail_max = self.config.max_chunks + self.config.fusion_tail_boost
        pending = len(self.chunk_manager.pending_chunks)
        if pending > 0:
            self._target_workers = max(self._target_workers, min(tail_max, pending))
            self._target_workers = min(self._target_workers, tail_max)

        # 激进抢占慢块
        avg_speed = self._speed_avg.get_average()
        active = self.chunk_manager.active_chunks
        now = time.time()
        for chunk in active:
            if chunk.remaining < self.config.fusion_tail_micro_split_min:
                continue
            if chunk.average_speed > 0 and chunk.average_speed < avg_speed * self.config.fusion_tail_steal_ratio:
                resplit_times = self._chunk_resplit_count.get(chunk.index, 0)
                if resplit_times >= 3:
                    continue
                if await self._resplit_chunk(chunk, resplit_times, is_tail=True):
                    self._resplit_count += 1
                    self._chunk_resplit_count[chunk.index] = resplit_times + 1
                    self._last_resplit_time = now

    # -- Slow chunks & resplit --

    async def _check_slow_chunks(self, bw_est: BandwidthEstimate) -> None:
        """检测并处理慢块

        分阶段差异化，让巡航期更像 IDM 的平稳：
          - PROBE / RAMP：不做重切。这两个阶段在探测带宽/爬升并发，重切会
            污染带宽测量并制造抖动。
          - CRUISE：只切“严重慢块”（< 均速的 cruise_resplit_threshold），且
            使用更长的冷却；轻微速度波动不再触发取消重切，避免巡航期的停顿。
          - TAIL：保持激进抢占（这是提速收尾的关键）。
        """
        if self._phase in (FusionPhase.PROBE, FusionPhase.RAMP):
            return

        if self._phase == FusionPhase.TAIL:
            threshold = self.config.fusion_tail_steal_ratio
            min_remaining = self.config.fusion_tail_micro_split_min
            cooldown = self.config.resplit_cooldown
            max_resplits = 3
        else:  # CRUISE
            threshold = self.config.fusion_cruise_resplit_threshold
            min_remaining = self.config.hybrid_min_remaining_bytes
            # 巡航期双倍冷却，减少中途重切带来的停顿
            cooldown = self.config.resplit_cooldown * 2
            max_resplits = self.config.hybrid_max_resplit_per_chunk

        slow_chunks = self.chunk_manager.get_slow_chunks(threshold)
        if not slow_chunks:
            return

        now = time.time()
        if now - self._last_resplit_time < cooldown:
            return

        active_count = len(self.chunk_manager.active_chunks)
        max_process = max(1, int(active_count**0.5))
        global_avg_speed = self._bw.p50_speed

        processed = 0
        for chunk in slow_chunks:
            if processed >= max_process:
                break
            if chunk.remaining < min_remaining:
                continue
            resplit_times = self._chunk_resplit_count.get(chunk.index, 0)
            if resplit_times >= max_resplits:
                continue
            if chunk.can_resplit(self.config.resplit_cooldown, global_avg_speed) and await self._resplit_chunk(
                chunk, resplit_times
            ):
                self._resplit_count += 1
                self._chunk_resplit_count[chunk.index] = resplit_times + 1
                self._last_resplit_time = now
                processed += 1

    async def _resplit_chunk(self, chunk: Chunk, resplit_times: int = 0, is_tail: bool = False) -> bool:
        async with self._lock:
            min_size = self.config.fusion_tail_micro_split_min if is_tail else self.config.min_chunk_size
            if chunk.remaining < min_size:
                return False
            if not is_tail and chunk.progress > 75:
                return False
            num_splits = min(2 + resplit_times, 4)
            if is_tail:
                num_splits = min(4, max(2, chunk.remaining // max(min_size, 1)))
            new_chunks = self.chunk_manager.resplit_chunk(
                chunk.index,
                num_splits,
                bypass_can_resplit=True,
            )
            return new_chunks is not None and len(new_chunks) > 0

    # -- Worker management --

    def register_worker(self) -> None:
        self._current_workers += 1

    def unregister_worker(self) -> None:
        self._current_workers = max(0, self._current_workers - 1)

    def should_spawn_worker(self) -> bool:
        pending = len(self.chunk_manager.pending_chunks)
        active = self._current_workers
        limit = min(self._target_workers, self.max_workers)
        return pending > 0 and active < limit

    def get_optimal_worker_count(self) -> int:
        if not self.monitor:
            return self._target_workers
        pending = len(self.chunk_manager.pending_chunks)
        if pending <= 0:
            return self._current_workers
        return min(self._target_workers, pending, self.max_workers)

    # -- Stats --

    def get_stats(self) -> FusionStats:
        return FusionStats(
            phase=self._phase.value,
            active_workers=self._current_workers,
            target_workers=self._target_workers,
            pending_chunks=len(self.chunk_manager.pending_chunks),
            bandwidth_ceiling=self._bw.ceiling,
            per_conn_speed=self._bw._per_conn_history[-1] if self._bw._per_conn_history else 0.0,
            server_throttled=self._bw._detect_throttle(),
            plateau_reached=self._plateau_reached,
            ramp_rounds=self._ramp_rounds,
            resplit_count=self._resplit_count,
            phase_transitions=self._phase_transitions,
            current_speed=self._speed_avg.get_average(),
            p50_speed=self._bw.p50_speed,
            speed_trend=self._speed_avg.get_trend(),
        )
