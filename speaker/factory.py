"""Speaker 工厂模块

提供 SpeakerClient 的工厂类，支持 CAM++ 等声纹引擎。
"""

from typing import Dict, Optional, Type, List, Any
import os

import numpy as np

from speaker.base import (
    SpeakerClient,
    SpeakerEmbedding,
    SpeakerVerificationResult,
    SpeakerSegment,
)


# 引擎注册表
_engines: Dict[str, Type[SpeakerClient]] = {}


def register(engine_name: str, client_class: Type[SpeakerClient]) -> None:
    """注册声纹引擎

    Args:
        engine_name: 引擎名称
        client_class: 引擎客户端类
    """
    _engines[engine_name.lower()] = client_class


def register_alias(alias: str, engine_name: str) -> None:
    """注册引擎别名

    Args:
        alias: 别名
        engine_name: 原始引擎名称
    """
    if engine_name.lower() not in _engines:
        raise ValueError(f"Engine {engine_name} not registered")
    _engines[alias.lower()] = _engines[engine_name.lower()]


def available_engines() -> List[str]:
    """列出可用引擎"""
    return list(_engines.keys())


def is_available(engine_name: str) -> bool:
    """检查引擎是否可用

    Args:
        engine_name: 引擎名称

    Returns:
        是否可用
    """
    if engine_name.lower() not in _engines:
        return False
    try:
        client_class = _engines[engine_name.lower()]
        # 检查依赖
        return client_class.check_dependencies()
    except Exception:
        return False


def get_engine_info(engine_name: str) -> Dict[str, Any]:
    """获取引擎信息

    Args:
        engine_name: 引擎名称

    Returns:
        引擎信息字典
    """
    if engine_name.lower() not in _engines:
        raise ValueError(f"Unknown engine: {engine_name}")

    client_class = _engines[engine_name.lower()]
    return {
        "name": engine_name,
        "class": client_class.__name__,
        "available": client_class.check_dependencies(),
    }


class SpeakerClientFactory:
    """Speaker 客户端工厂"""

    @staticmethod
    def create(
        engine: str = "cam++",
        embedding_dir: Optional[str] = None,
        **kwargs,
    ) -> SpeakerClient:
        """创建 Speaker 客户端

        Args:
            engine: 引擎名称
            embedding_dir: 声纹存储目录
            **kwargs: 其他引擎参数

        Returns:
            SpeakerClient 实例
        """
        engine_lower = engine.lower()

        if engine_lower not in _engines:
            available = available_engines()
            raise ValueError(
                f"Unsupported speaker engine: {engine}. "
                f"Available: {available}"
            )

        client_class = _engines[engine_lower]
        return client_class(embedding_dir=embedding_dir, **kwargs)

    @staticmethod
    def available_engines() -> List[str]:
        """列出可用引擎"""
        return available_engines()

    @staticmethod
    def is_available(engine_name: str) -> bool:
        """检查引擎是否可用"""
        return is_available(engine_name)

    @staticmethod
    def get_engine_info(engine_name: str) -> Dict[str, Any]:
        """获取引擎信息"""
        return get_engine_info(engine_name)


def create_speaker_client(
    engine: str = "cam++",
    embedding_dir: Optional[str] = None,
    **kwargs,
) -> SpeakerClient:
    """便捷函数：创建 Speaker 客户端

    Args:
        engine: 引擎名称
        embedding_dir: 声纹存储目录
        **kwargs: 其他引擎参数

    Returns:
        SpeakerClient 实例
    """
    return SpeakerClientFactory.create(
        engine=engine,
        embedding_dir=embedding_dir,
        **kwargs,
    )


# 注册默认引擎
try:
    from speaker.camplus_client import CAMPlusClient

    register("cam++", CAMPlusClient)
    register_alias("camplus", "cam++")
except ImportError:
    pass

# 模拟引擎（用于测试）
class MockSpeakerClient(SpeakerClient):
    """模拟声纹客户端（用于测试）"""

    def __init__(
        self,
        embedding_dir: Optional[str] = None,
        device: str = "cpu",
    ):
        """初始化模拟客户端"""
        self._embedding_dir = embedding_dir
        self._device = device

    @property
    def name(self) -> str:
        return "mock-speaker"

    @property
    def embedding_dim(self) -> int:
        return 192

    def extract_embedding(self, audio_path: str) -> np.ndarray:
        import numpy as np
        return np.random.randn(192).astype(np.float32)

    def verify(
        self,
        audio_path: str,
        embedding: np.ndarray,
        threshold: float = 0.5,
    ) -> SpeakerVerificationResult:
        import numpy as np
        confidence = float(np.random.random())
        return SpeakerVerificationResult(
            is_verified=confidence >= threshold,
            confidence=confidence,
            threshold=threshold,
            embedding=embedding,
        )

    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
    ) -> List[SpeakerSegment]:
        if num_speakers is None:
            num_speakers = 2
        return [
            SpeakerSegment(
                speaker_id=f"S0{i}",
                start_time=i * 3.0,
                end_time=(i + 1) * 3.0,
                confidence=0.9,
            )
            for i in range(num_speakers)
        ]

    def is_available(self) -> bool:
        return True

    @staticmethod
    def check_dependencies() -> bool:
        return True


register("mock", MockSpeakerClient)
