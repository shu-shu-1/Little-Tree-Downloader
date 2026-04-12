import argparse
import hashlib
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from littledl import (
    Chunk,
    ChunkEvent,
    ChunkManager,
    ChunkStatus,
    DownloadConfig,
    DownloadMonitor,
    Downloader,
    DownloadStyle,
    ProgressEvent,
    ResumeManager,
    StyleDecision,
    StrategySelector,
)
import littledl.__main__ as cli_main
from littledl.batch import BatchDownloader, EnhancedBatchDownloader, FileScheduler, FileTask
from littledl.connection import ConnectionPool
from littledl.downloader import ChunkCallbackAdapter, ProgressCallbackAdapter
from littledl.exceptions import ConfigurationError, HTTPError
from littledl.monitor import DownloadStats
from littledl.scheduler import BandwidthEstimate, FusionPhase, FusionScheduler, SmartScheduler
from littledl.writer import BufferedFileWriter
from littledl.__main__ import OutputMode, resolve_single_download_path, run_download, select_batch_concurrency, style_to_enum


class TestDownloadConfig:
    def test_default_config(self) -> None:
        config = DownloadConfig()
        assert config.enable_chunking is True
        assert config.max_chunks == 16
        assert config.resume is True
        assert config.retry.max_retries == 3
        assert config.enable_hybrid_turbo is True

    def test_config_validation(self) -> None:
        config = DownloadConfig(max_chunks=4, min_chunks=8)
        assert config.max_chunks == 8

        config = DownloadConfig(chunk_size=1024)
        assert config.chunk_size == config.min_chunk_size

    def test_calculate_optimal_chunks(self) -> None:
        config = DownloadConfig(max_chunks=8, min_chunk_size=1024 * 1024)

        chunks = config.calculate_optimal_chunks(10 * 1024 * 1024)
        assert 1 <= chunks <= 8

        chunks = config.calculate_optimal_chunks(100 * 1024 * 1024)
        assert chunks == 8

        chunks = config.calculate_optimal_chunks(0)
        assert chunks == 1

    def test_get_headers(self) -> None:
        config = DownloadConfig(
            user_agent="TestAgent/1.0",
            headers={"X-Custom": "value"},
        )
        headers = config.get_headers()
        assert headers["User-Agent"] == "TestAgent/1.0"
        assert headers["X-Custom"] == "value"
        assert "Accept" in headers


class TestChunk:
    def test_chunk_creation(self) -> None:
        chunk = Chunk(
            index=0,
            start_byte=0,
            end_byte=1024,
            total_size=2048,
        )
        assert chunk.size == 1024
        assert chunk.downloaded == 0
        assert chunk.progress == 0.0
        assert chunk.status == ChunkStatus.PENDING

    def test_chunk_progress(self) -> None:
        chunk = Chunk(
            index=0,
            start_byte=0,
            end_byte=1000,
            total_size=1000,
        )
        chunk.update_progress(500)
        assert chunk.downloaded == 500
        assert chunk.progress == 50.0

    def test_chunk_completion(self) -> None:
        chunk = Chunk(
            index=0,
            start_byte=0,
            end_byte=100,
            total_size=100,
        )
        chunk.start_download("worker_1")
        chunk.update_progress(100)
        assert chunk.is_completed
        assert chunk.status == ChunkStatus.COMPLETED

    def test_chunk_failure(self) -> None:
        chunk = Chunk(
            index=0,
            start_byte=0,
            end_byte=100,
            total_size=100,
        )
        chunk.fail("Test error")
        assert chunk.is_failed
        assert chunk.error_count == 1
        assert chunk.last_error == "Test error"

    def test_chunk_resplit(self) -> None:
        chunk = Chunk(
            index=0,
            start_byte=0,
            end_byte=10 * 1024 * 1024,
            total_size=10 * 1024 * 1024,
        )
        chunk.start_download("worker_1")
        chunk.update_progress(1024)
        assert chunk.can_resplit()

        chunk.update_progress(9 * 1024 * 1024)
        assert not chunk.can_resplit()

    def test_chunk_serialization(self) -> None:
        chunk = Chunk(
            index=1,
            start_byte=1024,
            end_byte=2048,
            total_size=4096,
            downloaded=512,
        )
        data = chunk.to_dict()
        restored = Chunk.from_dict(data)
        assert restored.index == chunk.index
        assert restored.start_byte == chunk.start_byte
        assert restored.downloaded == chunk.downloaded


class TestChunkManager:
    def test_initialization(self) -> None:
        manager = ChunkManager(file_size=10 * 1024 * 1024, max_chunks=4)
        manager.initialize_chunks()
        assert len(manager.chunks) >= 1
        assert manager.total_remaining == 10 * 1024 * 1024

    def test_progress_tracking(self) -> None:
        manager = ChunkManager(file_size=10 * 1024 * 1024, max_chunks=2, min_chunk_size=1024)
        manager.initialize_chunks()

        manager.chunks[0].update_progress(250)
        if len(manager.chunks) > 1:
            manager.chunks[1].update_progress(250)
            assert manager.total_downloaded == 500
        else:
            assert manager.total_downloaded == 250

    def test_chunk_retrieval(self) -> None:
        manager = ChunkManager(file_size=10 * 1024 * 1024, max_chunks=3, min_chunk_size=1024)
        manager.initialize_chunks()

        pending = manager.pending_chunks
        assert len(pending) >= 1

    @pytest.mark.asyncio
    async def test_async_operations(self) -> None:
        manager = ChunkManager(file_size=1000, max_chunks=2)
        manager.initialize_chunks()

        chunk = await manager.get_next_chunk()
        assert chunk is not None
        assert chunk.status == ChunkStatus.PENDING

        await manager.update_chunk_progress(0, 100)
        assert manager.chunks[0].downloaded == 100


class TestDownloadMonitor:
    def test_initialization(self) -> None:
        monitor = DownloadMonitor(total_size=1000)
        assert monitor.total_size == 1000
        assert monitor.downloaded == 0

    def test_progress_update(self) -> None:
        monitor = DownloadMonitor(total_size=1000)
        monitor.start()
        monitor.update_downloaded(500)
        assert monitor.progress == 50.0

    def test_speed_calculation(self) -> None:
        monitor = DownloadMonitor(total_size=1000)
        monitor.start()
        monitor.update_downloaded(100)
        assert monitor._speed_monitor.current_speed >= 0

    def test_eta_calculation(self) -> None:
        monitor = DownloadMonitor(total_size=10000)
        monitor.start()
        monitor.update_downloaded(1000)
        monitor._speed_monitor._current_speed = 100.0
        eta = monitor.eta
        assert eta >= -1

    def test_stats(self) -> None:
        monitor = DownloadMonitor(total_size=1000)
        monitor.start()
        monitor.update_downloaded(100)
        stats = monitor.get_stats()
        assert stats.total_size == 1000
        assert stats.downloaded == 100
        assert stats.is_active


class TestResumeManager:
    @pytest.mark.asyncio
    async def test_initialization(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResumeManager(Path(tmpdir), "test_id")
            manager.initialize(
                url="https://example.com/file.zip",
                file_size=10000,
                filename="file.zip",
            )
            assert manager.metadata is not None
            assert manager.metadata.file_size == 10000

    @pytest.mark.asyncio
    async def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ResumeManager(Path(tmpdir), "test_id")
            manager.initialize(
                url="https://example.com/file.zip",
                file_size=10000,
                filename="file.zip",
            )
            await manager.save(force=True)

            new_manager = ResumeManager(Path(tmpdir), "test_id")
            loaded = await new_manager.load()
            assert loaded is not None
            assert loaded.file_size == 10000


class TestDownloader:
    def test_config_initialization(self) -> None:
        config = DownloadConfig(max_chunks=8)
        downloader = Downloader(config)
        assert downloader.config.max_chunks == 8

    @pytest.mark.asyncio
    async def test_probe_file_info(self) -> None:
        config = DownloadConfig()
        downloader = Downloader(config)

        mock_response = MagicMock()
        mock_response.headers = {
            "Content-Length": "10000",
            "Accept-Ranges": "bytes",
            "Content-Disposition": 'attachment; filename="test.zip"',
            "Content-Type": "application/zip",
        }
        mock_response.status_code = 200

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head.return_value = mock_response

        info = await downloader._probe_file_info(mock_client, "https://example.com/test.zip")

        assert info["size"] == 10000
        assert info["supports_range"] is True
        assert info["filename"] == "test.zip"

    @pytest.mark.asyncio
    async def test_probe_file_info_http_error(self) -> None:
        config = DownloadConfig()
        downloader = Downloader(config)

        mock_response = MagicMock()
        mock_response.headers = {}
        mock_response.status_code = 500

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.head.return_value = mock_response

        with pytest.raises(HTTPError):
            await downloader._probe_file_info(mock_client, "https://example.com/fail.bin")

    @pytest.mark.asyncio
    async def test_verify_downloaded_file_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.bin"
            content = b"littledl-hash-test"
            file_path.write_bytes(content)

            expected = hashlib.sha256(content).hexdigest()
            config = DownloadConfig(verify_hash=True, expected_hash=expected, hash_algorithm="sha256")
            downloader = Downloader(config)

            await downloader._verify_downloaded_file(file_path)

    @pytest.mark.asyncio
    async def test_verify_hash_requires_expected_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "sample.bin"
            file_path.write_bytes(b"abc")

            config = DownloadConfig(verify_hash=True, expected_hash=None)
            downloader = Downloader(config)

            with pytest.raises(ConfigurationError):
                await downloader._verify_downloaded_file(file_path)

    def test_stats(self) -> None:
        downloader = Downloader()
        stats = downloader.get_stats()
        assert stats is None

    @pytest.mark.asyncio
    async def test_progress_callback_legacy_format(self) -> None:
        captured: list[tuple[int, int, float, int]] = []

        def callback(downloaded: int, total: int, speed: float, eta: int) -> None:
            captured.append((downloaded, total, speed, eta))

        adapter = ProgressCallbackAdapter(callback)
        await adapter.emit(100, 200, 50.0, 2)

        assert captured == [(100, 200, 50.0, 2)]

    @pytest.mark.asyncio
    async def test_progress_callback_event_format(self) -> None:
        captured: list[ProgressEvent] = []

        def callback(event: ProgressEvent) -> None:
            captured.append(event)

        adapter = ProgressCallbackAdapter(callback)
        await adapter.emit(200, 400, 80.0, 2)

        assert len(captured) == 1
        assert captured[0].downloaded == 200
        assert captured[0].total == 400

    @pytest.mark.asyncio
    async def test_progress_callback_dict_format(self) -> None:
        captured: list[dict[str, float | int]] = []

        def callback(payload: dict[str, float | int]) -> None:
            captured.append(payload)

        adapter = ProgressCallbackAdapter(callback)
        await adapter.emit(300, 600, 120.0, 2)

        assert len(captured) == 1
        assert captured[0]["downloaded"] == 300
        assert captured[0]["total"] == 600

    @pytest.mark.asyncio
    async def test_progress_callback_kwargs_format(self) -> None:
        captured: dict[str, float | int] = {}

        def callback(**kwargs: float | int) -> None:
            captured.update(kwargs)

        adapter = ProgressCallbackAdapter(callback)
        await adapter.emit(400, 800, 160.0, 2)

        assert captured["downloaded"] == 400
        assert captured["total"] == 800
        assert "progress" in captured

    @pytest.mark.asyncio
    async def test_progress_callback_async_supported(self) -> None:
        captured: list[int] = []

        async def callback(event: ProgressEvent) -> None:
            captured.append(event.downloaded)

        adapter = ProgressCallbackAdapter(callback)
        await adapter.emit(500, 1000, 200.0, 2)

        assert captured == [500]

    @pytest.mark.asyncio
    async def test_chunk_callback_legacy_format(self) -> None:
        captured: list[tuple[int, str, int, int, float, float, str | None]] = []
        chunk = Chunk(index=1, start_byte=0, end_byte=1000, total_size=1000, downloaded=300)

        def callback(
            chunk_index: int,
            status: str,
            downloaded: int,
            total: int,
            progress: float,
            speed: float,
            error: str | None,
        ) -> None:
            captured.append((chunk_index, status, downloaded, total, progress, speed, error))

        adapter = ChunkCallbackAdapter(callback)
        await adapter.emit(chunk, "downloading", speed=123.0)

        assert len(captured) == 1
        assert captured[0][0] == 1
        assert captured[0][1] == "downloading"

    @pytest.mark.asyncio
    async def test_chunk_callback_event_format(self) -> None:
        captured: list[ChunkEvent] = []
        chunk = Chunk(index=2, start_byte=0, end_byte=2000, total_size=2000, downloaded=1000)

        def callback(event: ChunkEvent) -> None:
            captured.append(event)

        adapter = ChunkCallbackAdapter(callback)
        await adapter.emit(chunk, "completed", speed=256.0)

        assert len(captured) == 1
        assert captured[0].chunk_index == 2
        assert captured[0].status == "completed"

    @pytest.mark.asyncio
    async def test_chunk_callback_dict_and_kwargs_formats(self) -> None:
        dict_payloads: list[dict[str, float | int | str | None]] = []
        kwargs_payloads: list[dict[str, float | int | str | None]] = []
        chunk = Chunk(index=3, start_byte=0, end_byte=1000, total_size=1000, downloaded=600)

        def dict_callback(payload: dict[str, float | int | str | None]) -> None:
            dict_payloads.append(payload)

        def kwargs_callback(**payload: float | int | str | None) -> None:
            kwargs_payloads.append(payload)

        dict_adapter = ChunkCallbackAdapter(dict_callback)
        kwargs_adapter = ChunkCallbackAdapter(kwargs_callback)

        await dict_adapter.emit(chunk, "downloading", speed=88.0)
        await kwargs_adapter.emit(chunk, "failed", speed=0.0, error="network")

        assert dict_payloads[0]["chunk_index"] == 3
        assert kwargs_payloads[0]["status"] == "failed"
        assert kwargs_payloads[0]["error"] == "network"

    @pytest.mark.asyncio
    async def test_chunk_callback_async_supported(self) -> None:
        captured: list[str] = []
        chunk = Chunk(index=4, start_byte=0, end_byte=1000, total_size=1000, downloaded=100)

        async def callback(event: ChunkEvent) -> None:
            captured.append(event.status)

        adapter = ChunkCallbackAdapter(callback)
        await adapter.emit(chunk, "started", speed=0.0)

        assert captured == ["started"]


class TestStrategyAndHybridStyle:
    def test_strategy_prefers_fusion_for_large_range_file(self) -> None:
        selector = StrategySelector()
        profile = selector.analyze_file(
            url="https://example.com/large.iso",
            size=200 * 1024 * 1024,
            supports_range=True,
            content_type="application/octet-stream",
        )
        decision = selector.select_style(profile)

        assert decision.style == DownloadStyle.FUSION
        assert decision.recommended_chunks >= 4

    def test_style_to_enum_supports_hybrid_alias(self) -> None:
        assert style_to_enum("hybrid") == DownloadStyle.HYBRID_TURBO
        assert style_to_enum("hybrid_turbo") == DownloadStyle.HYBRID_TURBO
        assert style_to_enum("fusion") == DownloadStyle.FUSION
        assert style_to_enum("auto") == DownloadStyle.FUSION

    def test_apply_style_to_config_single_and_hybrid(self) -> None:
        single_config = DownloadConfig()
        single_config.apply_style(DownloadStyle.SINGLE)
        assert single_config.max_chunks == 1
        assert single_config.enable_chunking is False
        assert single_config.enable_hybrid_turbo is False

        hybrid_config = DownloadConfig(enable_hybrid_turbo=False, adaptive_interval=3.0)
        hybrid_config.apply_style(DownloadStyle.HYBRID_TURBO)
        assert hybrid_config.enable_hybrid_turbo is True
        assert hybrid_config.enable_adaptive is True
        assert hybrid_config.adaptive_interval <= 2.0


class TestSmartSchedulerHybrid:
    class _FakeMonitor:
        def __init__(self, speed: float) -> None:
            self.speed = speed

        def get_stats(self) -> DownloadStats:
            return DownloadStats(total_size=1, downloaded=1, speed=self.speed, is_active=True)

    @pytest.mark.asyncio
    async def test_aimd_increases_target_workers_on_speedup(self) -> None:
        config = DownloadConfig(min_chunks=1, max_chunks=8, enable_hybrid_turbo=True)
        manager = ChunkManager(file_size=8 * 1024 * 1024, max_chunks=8, min_chunk_size=1024 * 1024)
        manager.initialize_chunks()
        scheduler = SmartScheduler(manager, config=config, monitor=self._FakeMonitor(speed=1500.0))
        scheduler._current_workers = 2
        scheduler._target_workers = 2
        scheduler._last_speed = 1000.0
        scheduler._speed_average.add(1000.0)
        scheduler._speed_average.add(1200.0)
        scheduler._last_adjustment_time = 0.0

        await scheduler._run_adaptive_adjustments()

        assert scheduler.get_optimal_worker_count() >= 3

    @pytest.mark.asyncio
    async def test_aimd_decreases_target_workers_on_decline(self) -> None:
        config = DownloadConfig(min_chunks=1, max_chunks=8, enable_hybrid_turbo=True)
        manager = ChunkManager(file_size=8 * 1024 * 1024, max_chunks=8, min_chunk_size=1024 * 1024)
        manager.initialize_chunks()
        scheduler = SmartScheduler(manager, config=config, monitor=self._FakeMonitor(speed=700.0))
        scheduler._current_workers = 5
        scheduler._target_workers = 5
        scheduler._last_speed = 1200.0
        scheduler._speed_average.add(1200.0)
        scheduler._speed_average.add(1000.0)
        scheduler._last_adjustment_time = 0.0

        await scheduler._run_adaptive_adjustments()

        assert scheduler.get_optimal_worker_count() <= 4


class TestFusionScheduler:
    class _FakeMonitor:
        def __init__(self, speed: float, total_size: int, downloaded: int) -> None:
            self.speed = speed
            self.total_size = total_size
            self.downloaded = downloaded

        def get_stats(self) -> DownloadStats:
            return DownloadStats(
                total_size=self.total_size,
                downloaded=self.downloaded,
                speed=self.speed,
                is_active=True,
            )

    @pytest.mark.asyncio
    async def test_cruise_can_probe_after_ramp_plateau(self) -> None:
        file_size = 8 * 1024 * 1024
        config = DownloadConfig(min_chunks=1, max_chunks=8, enable_fusion=True)
        manager = ChunkManager(file_size=file_size, max_chunks=8, min_chunk_size=1024 * 1024)
        manager.initialize_chunks()
        scheduler = FusionScheduler(
            manager,
            config=config,
            monitor=self._FakeMonitor(speed=1500.0, total_size=file_size, downloaded=file_size // 2),
        )
        scheduler._phase = FusionPhase.CRUISE
        scheduler._target_workers = 3
        scheduler._last_speed = 1200.0
        scheduler._plateau_reached = True
        scheduler._last_adjustment_time = 0.0
        scheduler._speed_avg.add(1000.0)
        scheduler._speed_avg.add(1250.0)
        scheduler._speed_avg.add(1500.0)

        await scheduler._do_cruise(1500.0, BandwidthEstimate())

        assert scheduler._target_workers == 4

    def test_tail_waits_for_real_tail_progress(self) -> None:
        file_size = 4 * 1024 * 1024
        config = DownloadConfig(min_chunks=1, max_chunks=4, enable_fusion=True)
        manager = ChunkManager(file_size=file_size, max_chunks=4, min_chunk_size=1024 * 1024)
        manager.initialize_chunks()
        manager.chunks[0].complete()
        scheduler = FusionScheduler(manager, config=config)
        scheduler._phase = FusionPhase.CRUISE

        scheduler._check_phase_transition(
            DownloadStats(total_size=file_size, downloaded=file_size // 4, speed=1000.0, is_active=True),
            BandwidthEstimate(),
        )

        assert scheduler._phase == FusionPhase.CRUISE

    def test_tail_enters_when_remaining_ratio_is_low(self) -> None:
        file_size = 4 * 1024 * 1024
        config = DownloadConfig(min_chunks=1, max_chunks=4, enable_fusion=True)
        manager = ChunkManager(file_size=file_size, max_chunks=4, min_chunk_size=1024 * 1024)
        manager.initialize_chunks()
        scheduler = FusionScheduler(manager, config=config)
        scheduler._phase = FusionPhase.CRUISE

        scheduler._check_phase_transition(
            DownloadStats(total_size=file_size, downloaded=int(file_size * 0.85), speed=1000.0, is_active=True),
            BandwidthEstimate(),
        )

        assert scheduler._phase == FusionPhase.TAIL


class TestDownloaderScheduling:
    def test_collect_schedulable_chunks_respects_limit_and_state(self) -> None:
        downloader = Downloader(DownloadConfig(max_chunks=4))
        manager = ChunkManager(file_size=4 * 1024 * 1024, max_chunks=4, min_chunk_size=1024 * 1024)
        manager.initialize_chunks()
        manager.chunks[1].status = ChunkStatus.DOWNLOADING
        manager.chunks[2].complete()
        downloader._chunk_manager = manager

        selected = downloader._collect_schedulable_chunks({0}, limit=3)

        assert [chunk.index for chunk in selected] == [3]


class TestCliAutoSelection:
    @pytest.mark.asyncio
    async def test_run_download_auto_applies_recommended_chunks(
        self,
        monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path,
    ) -> None:
        captured: dict[str, int | bool] = {}

        async def fake_download_file(*, config: DownloadConfig, **_: object) -> Path:
            captured["max_chunks"] = config.max_chunks
            captured["enable_fusion"] = config.enable_fusion
            output_path = tmp_path / "download.bin"
            output_path.write_bytes(b"ok")
            return output_path

        class FakeSelector:
            def __init__(self, *args: object, **kwargs: object) -> None:
                pass

            def analyze_file(self, *args: object, **kwargs: object) -> object:
                return object()

            def select_style(self, profile: object) -> StyleDecision:
                return StyleDecision(
                    style=DownloadStyle.FUSION,
                    confidence=1.0,
                    reason="test",
                    recommended_chunks=6,
                )

        monkeypatch.setattr(cli_main, "download_file", fake_download_file)
        monkeypatch.setattr(cli_main, "StrategySelector", FakeSelector)

        config = DownloadConfig(max_chunks=16)
        args = argparse.Namespace(style="auto", verbose=False, resume=True)
        output = OutputMode(format_pref="json", quiet=False, is_tty=False)

        exit_code = await run_download(
            "https://example.com/file.bin",
            config,
            tmp_path / "download.bin",
            output,
            args,
            DownloadStyle.FUSION,
            probe_info={
                "size": 200 * 1024 * 1024,
                "supports_range": True,
                "content_type": "application/octet-stream",
            },
        )

        assert exit_code == 0
        assert captured["max_chunks"] == 6
        assert captured["enable_fusion"] is True


class TestIntegration:
    @pytest.mark.asyncio
    async def test_chunk_download_flow(self) -> None:
        manager = ChunkManager(file_size=10 * 1024 * 1024, max_chunks=2, min_chunk_size=1024)
        manager.initialize_chunks()

        chunk1 = await manager.get_next_chunk()
        assert chunk1 is not None
        chunk1.start_download("worker_1")
        chunk1.update_progress(5 * 1024 * 1024)
        await manager.complete_chunk(chunk1.index)

        chunk2 = await manager.get_next_chunk()
        if chunk2 is not None:
            chunk2.start_download("worker_2")
            chunk2.update_progress(5 * 1024 * 1024)
            await manager.complete_chunk(chunk2.index)

        assert manager.is_completed


class TestBufferedFileWriterDirectWrite:
    @pytest.mark.asyncio
    async def test_direct_write_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.bin"
            writer = BufferedFileWriter(
                file_path,
                "wb",
                buffer_size=1024 * 1024,
                direct_write_threshold=256 * 1024,
            )
            await writer.open()

            large_data = b"x" * 300 * 1024
            result = await writer.write_at(0, large_data)
            assert result == len(large_data)

            await writer.close()

            assert file_path.read_bytes() == large_data

    @pytest.mark.asyncio
    async def test_buffered_write_below_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.bin"
            writer = BufferedFileWriter(
                file_path,
                "wb",
                buffer_size=1024 * 1024,
                direct_write_threshold=256 * 1024,
            )
            await writer.open()

            small_data = b"y" * 100
            result = await writer.write_at(0, small_data)
            assert result == len(small_data)

            await writer.close()

            assert file_path.read_bytes() == small_data

    @pytest.mark.asyncio
    async def test_default_buffer_size(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test.bin"
            writer = BufferedFileWriter(file_path, "wb")
            assert writer.buffer_size == 1024 * 1024
            assert writer.direct_write_threshold == 256 * 1024
            await writer.open()
            await writer.close()


class TestConnectionPoolPreconnect:
    @pytest.mark.asyncio
    async def test_preconnect_urls(self) -> None:
        config = DownloadConfig()
        pool = ConnectionPool(config)

        mock_response = MagicMock()
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=None)

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_client.stream.return_value = mock_response

        pool._client = mock_client

        await pool.preconnect(
            [
                "https://example.com/file1.zip",
                "https://example.com/file2.zip",
            ]
        )

        assert mock_client.stream.call_count == 2

        await pool.close()


class TestMaxConcurrentFilesDefault:
    def test_file_scheduler_default(self) -> None:
        scheduler = FileScheduler()
        assert scheduler.max_concurrent_files == 8

    def test_batch_downloader_default(self) -> None:
        downloader = BatchDownloader()
        assert downloader.max_concurrent_files == 8

    @pytest.mark.asyncio
    async def test_enhanced_batch_downloader_default(self) -> None:
        downloader = EnhancedBatchDownloader()
        assert downloader.max_concurrent_files == 8

    def test_dynamic_style_allocator_default(self) -> None:
        from littledl.strategy import DynamicStyleAllocator

        selector = StrategySelector()
        allocator = DynamicStyleAllocator(selector)
        assert allocator.max_concurrent_files == 8


class TestBatchDomainAndSmallFileOptimization:
    @pytest.mark.asyncio
    async def test_scheduler_prefers_requested_domain(self) -> None:
        scheduler = FileScheduler(enable_domain_affinity=True)

        task_a1 = await self._create_task("https://a.example.com/f1.bin", "a.example.com")
        task_b1 = await self._create_task("https://b.example.com/f2.bin", "b.example.com")
        task_a2 = await self._create_task("https://a.example.com/f3.bin", "a.example.com")

        await scheduler.add_task(task_b1)
        await scheduler.add_task(task_a1)
        await scheduler.add_task(task_a2)

        picked = await scheduler.get_next_task(preferred_domain="a.example.com")
        assert picked is not None
        assert picked.domain == "a.example.com"

    def test_small_file_same_domain_boost_concurrency(self) -> None:
        downloader = BatchDownloader(
            max_concurrent_files=4,
            enable_adaptive_concurrency=False,
            enable_small_file_concurrency_boost=True,
            same_domain_boost_threshold=0.7,
        )

        for idx in range(20):
            task = FileTask(
                task_id=f"task-{idx}",
                url=f"https://cdn.example.com/file-{idx}.bin",
                save_path=Path("."),
                domain="cdn.example.com",
                file_size=64 * 1024,
            )
            downloader._scheduler._pending_tasks.append(task)

        boosted = downloader._estimate_concurrency_limit(base_limit=4)
        assert boosted > 4

    @staticmethod
    async def _create_task(url: str, domain: str) -> FileTask:
        task = FileTask(
            task_id=url,
            url=url,
            save_path=Path("."),
            domain=domain,
            file_size=128 * 1024,
        )
        return task


class TestCliPathAndConcurrencyOptimization:
    def test_resolve_single_download_path_treats_suffixless_output_as_directory(self) -> None:
        path = resolve_single_download_path("./downloads", None, "video.mp4")
        assert path.name == "video.mp4"
        assert path.parent.name == "downloads"

    def test_resolve_single_download_path_file_output_kept(self) -> None:
        path = resolve_single_download_path("./downloads/fixed_name.bin", None, "remote.bin")
        assert path.name == "fixed_name.bin"
        assert path.parent.name == "downloads"

    def test_select_batch_concurrency_for_thousand_files(self) -> None:
        config = DownloadConfig(connection_pool_size=100)
        chosen = select_batch_concurrency(1200, requested=0, config=config, auto_enabled=True)
        assert chosen >= 32
        assert chosen <= 64


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
