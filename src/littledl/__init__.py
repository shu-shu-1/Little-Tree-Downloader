from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _pkg_version

from .auth import AuthManager, TokenInfo
from .batch import (
    AdaptiveConcurrencyController,
    BatchDownloader,
    BatchProgress,
    EnhancedBatchDownloader,
    FileScheduler,
    FileTask,
    FileTaskStatus,
    SharedConnectionBatchDownloader,
    batch_download,
    batch_download_sync,
)
from .callback import (
    BaseProgressEvent,
    BatchProgressEvent,
    CallbackChain,
    ChunkProgressEvent,
    EventType,
    FileCompleteEvent,
    FileProgressEvent,
    ProgressAggregator,
    ThrottledCallback,
    UnifiedCallbackAdapter,
    detect_callback_mode,
)
from .chunk import Chunk, ChunkManager, ChunkStatus
from .config import (
    AuthConfig,
    AuthType,
    DownloadConfig,
    ProxyConfig,
    ProxyMode,
    RetryConfig,
    RetryStrategy,
    SpeedLimitConfig,
    SpeedLimitMode,
)
from .detector import ServerCapabilities, ServerDetector
from .downloader import ChunkEvent, Downloader, ProgressEvent, download_file, download_file_sync
from .exceptions import (
    CancelledError,
    ChunkDownloadError,
    ChunkError,
    ChunkResplitError,
    ConfigurationError,
    DownloadError,
    DownloadTimeoutError,
    ForbiddenError,
    HTTPError,
    NetworkConnectionError,
    NetworkError,
    RangeNotSupportedError,
    ResourceNotFoundError,
    ResumeDataCorruptedError,
    ResumeDataNotFoundError,
    ResumeError,
    SpeedLimitExceededError,
    ValidationError,
)
from .global_pool import GlobalThreadPool
from .i18n import (
    LANGUAGE_ENV_VAR,
    get_available_languages,
    gettext,
    init_language,
    ngettext,
    pgettext,
    set_language,
)
from .limiter import AdaptiveLimiter, SpeedLimiter, TokenBucketLimiter
from .monitor import DownloadMonitor, DownloadStats
from .proxy import ProxyDetector, ProxyInfo, ProxyManager
from .resume import DownloadMetadata, ResumeManager
from .reuse import FileReuseChecker, MultiSourceManager, SharedFileRegistry
from .scheduler import FusionScheduler, SmartScheduler
from .strategy import (
    DownloadStyle,
    DynamicStyleAllocator,
    FileProfile,
    NetworkProfile,
    StrategySelector,
    StyleDecision,
)

__all__ = [
    # Core entry points
    "Downloader",
    "download_file",
    "download_file_sync",
    "BatchDownloader",
    "EnhancedBatchDownloader",
    "SharedConnectionBatchDownloader",
    "AdaptiveConcurrencyController",
    "BatchProgress",
    "FileScheduler",
    "FileTask",
    "FileTaskStatus",
    "batch_download",
    "batch_download_sync",
    # Progress / callbacks
    "ProgressEvent",
    "ChunkEvent",
    "EventType",
    "BaseProgressEvent",
    "FileProgressEvent",
    "FileCompleteEvent",
    "ChunkProgressEvent",
    "BatchProgressEvent",
    "UnifiedCallbackAdapter",
    "ThrottledCallback",
    "ProgressAggregator",
    "CallbackChain",
    "detect_callback_mode",
    # Configuration
    "DownloadConfig",
    "AuthConfig",
    "AuthType",
    "TokenInfo",
    "AuthManager",
    "ProxyConfig",
    "ProxyMode",
    "ProxyDetector",
    "ProxyManager",
    "ProxyInfo",
    "SpeedLimitConfig",
    "SpeedLimitMode",
    "SpeedLimiter",
    "TokenBucketLimiter",
    "AdaptiveLimiter",
    "RetryConfig",
    "RetryStrategy",
    # Introspection / building blocks
    "ServerCapabilities",
    "ServerDetector",
    "Chunk",
    "ChunkManager",
    "ChunkStatus",
    "DownloadMonitor",
    "DownloadStats",
    "DownloadMetadata",
    "ResumeManager",
    "SmartScheduler",
    "FusionScheduler",
    "DownloadStyle",
    "StrategySelector",
    "DynamicStyleAllocator",
    "FileProfile",
    "NetworkProfile",
    "StyleDecision",
    "GlobalThreadPool",
    "FileReuseChecker",
    "MultiSourceManager",
    "SharedFileRegistry",
    # i18n
    "gettext",
    "ngettext",
    "pgettext",
    "set_language",
    "get_available_languages",
    "init_language",
    "LANGUAGE_ENV_VAR",
    # Errors
    "DownloadError",
    "NetworkError",
    "NetworkConnectionError",
    "DownloadTimeoutError",
    "HTTPError",
    "ResourceNotFoundError",
    "ForbiddenError",
    "RangeNotSupportedError",
    "ChunkError",
    "ChunkDownloadError",
    "ChunkResplitError",
    "ResumeError",
    "ResumeDataCorruptedError",
    "ResumeDataNotFoundError",
    "SpeedLimitExceededError",
    "ConfigurationError",
    "ValidationError",
    "CancelledError",
]

try:
    __version__ = _pkg_version("littledl")
except PackageNotFoundError:  # pragma: no cover - running from source without install metadata
    __version__ = "0.0.0"

init_language()
