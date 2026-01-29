"""TTS 引擎工厂"""

from typing import Dict, Type, Optional
from .base import TTSClient, TTSResult
from .sherpa_client import SherpaTTSClient


class TTSClientFactory:
    """TTS 客户端工厂

    负责创建和管理 TTS 客户端实例。
    支持引擎注册、切换和回退机制。

    Usage:
        # 方式1: 直接创建
        tts = TTSClientFactory.create("sherpa-vits", model="vits-zh-hf-fanchen-C")

        # 方式2: 使用便捷函数
        from tts import create_tts_client
        tts = create_tts_client(engine="sherpa-vits")

        # 方式3: 上下文管理器
        with TTSClientFactory.create("sherpa-vits") as tts:
            result = tts.generate("你好")
    """

    # 注册的引擎实现
    _engines: Dict[str, Type[TTSClient]] = {
        "sherpa-vits": SherpaTTSClient,
        "sherpa-kokoro": SherpaTTSClient,
    }

    # 引擎别名映射（支持旧名称或其他标识）
    _aliases: Dict[str, str] = {
        "sherpa": "sherpa-vits",
        "vits": "sherpa-vits",
        "kokoro": "sherpa-kokoro",
    }

    @classmethod
    def register(cls, name: str, engine_class: Type[TTSClient]):
        """注册新的 TTS 引擎

        Args:
            name: 引擎名称（小写）
            engine_class: 实现 TTSClient 抽象基类的引擎类
        """
        cls._engines[name.lower()] = engine_class

    @classmethod
    def register_alias(cls, alias: str, engine_name: str):
        """注册引擎别名

        Args:
            alias: 别名
            engine_name: 实际引擎名称
        """
        cls._aliases[alias.lower()] = engine_name.lower()

    @classmethod
    def create(
        cls,
        engine: str = "sherpa-vits",
        **kwargs
    ) -> TTSClient:
        """创建 TTS 客户端实例

        Args:
            engine: 引擎名称或别名
            **kwargs: 引擎特定参数

        Returns:
            TTSClient 实例

        Raises:
            ValueError: 不支持的引擎
            RuntimeError: 引擎初始化失败
        """
        # 解析别名
        engine_key = engine.lower()
        if engine_key in cls._aliases:
            engine_key = cls._aliases[engine_key]

        if engine_key not in cls._engines:
            available = list(cls._engines.keys())
            raise ValueError(
                f"Unsupported TTS engine: {engine}. "
                f"Available engines: {available}"
            )

        engine_class = cls._engines[engine_key]
        return engine_class(**kwargs)

    @classmethod
    def available_engines(cls) -> list:
        """列出所有可用的引擎

        Returns:
            引擎名称列表
        """
        return list(cls._engines.keys())

    @classmethod
    def is_available(cls, engine: str) -> bool:
        """检查引擎是否可用

        Args:
            engine: 引擎名称

        Returns:
            True 表示引擎可用
        """
        try:
            client = cls.create(engine)
            available = client.is_available()
            client.close()
            return available
        except Exception:
            return False

    @classmethod
    def get_engine_info(cls, engine: str) -> dict:
        """获取引擎信息

        Args:
            engine: 引擎名称

        Returns:
            引擎信息字典，包含 name, sample_rate, num_speakers 等
        """
        try:
            with cls.create(engine) as client:
                return {
                    "name": client.name,
                    "sample_rate": client.sample_rate,
                    "num_speakers": client.num_speakers,
                    "available": client.is_available(),
                }
        except Exception as e:
            return {
                "name": engine,
                "available": False,
                "error": str(e),
            }
