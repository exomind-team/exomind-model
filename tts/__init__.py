"""Voice-IME TTS 模块

提供统一的 TTS 客户端接口，支持多种 TTS 引擎。
"""

from .base import TTSClient, TTSResult
from .factory import TTSClientFactory
from .sherpa_client import SherpaTTSClient

__all__ = [
    "TTSClient",
    "TTSResult",
    "TTSClientFactory",
    "SherpaTTSClient",
]

# 便捷的创建函数
def create_tts_client(engine: str = "sherpa-vits", **kwargs) -> TTSClient:
    """创建 TTS 客户端实例

    Args:
        engine: 引擎名称 (sherpa-vits | sherpa-kokoro)
        **kwargs: 引擎特定参数

    Returns:
        TTSClient 实例
    """
    return TTSClientFactory.create(engine, **kwargs)
