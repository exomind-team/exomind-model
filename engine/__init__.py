"""
Unified Engine Framework
========================

统一引擎框架，支持 ASR/TTS 多引擎管理和热切换。

Architecture:
    EngineType: 引擎类型枚举 (ASR, TTS)
    EngineConfig: 引擎配置
    EngineInfo: 引擎信息
    EngineManager: 统一引擎管理器

Usage:
    from engine import EngineManager, EngineType

    # 获取所有可用引擎
    manager = EngineManager()
    engines = manager.list_engines(EngineType.ASR)

    # 创建引擎
    asr_client = manager.create_engine(EngineType.ASR, "funasr")
    tts_client = manager.create_engine(EngineType.TTS, "sherpa-vits")
"""

from enum import Enum
from typing import Dict, List, Optional, Type, Union, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

import sys
from pathlib import Path
FILE = Path(__file__).resolve()
ROOT = FILE.parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from asr.factory import ASRClientFactory
from tts.factory import TTSClientFactory


class EngineType(Enum):
    """引擎类型"""
    ASR = "asr"  # 语音识别
    TTS = "tts"  # 语音合成
    SPEAKER = "speaker"  # 说话人识别


@dataclass
class EngineConfig:
    """引擎配置"""
    name: str
    type: EngineType
    enabled: bool = True
    priority: int = 0  # 优先级，数字越大优先级越高
    fallback: Optional[str] = None  # 回退引擎
    display_name: str = ""  # 显示名称
    description: str = ""  # 引擎描述
    capabilities: List[str] = field(default_factory=list)  # 引擎能力列表
    params: Dict[str, Any] = field(default_factory=dict)  # 引擎特定参数


@dataclass
class EngineInfo:
    """引擎信息"""
    name: str
    type: EngineType
    display_name: str
    description: str
    capabilities: List[str]
    available: bool
    priority: int
    is_default: bool


class BaseEngine(ABC):
    """引擎基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        pass

    @property
    @abstractmethod
    def type(self) -> EngineType:
        """引擎类型"""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """引擎是否可用"""
        pass

    @abstractmethod
    def get_info(self) -> EngineInfo:
        """获取引擎信息"""
        pass


class EngineManager:
    """统一引擎管理器

    负责管理所有类型的引擎，提供统一的创建、查询、切换接口。
    """

    def __init__(self):
        self._configs: Dict[EngineType, Dict[str, EngineConfig]] = {
            EngineType.ASR: {},
            EngineType.TTS: {},
            EngineType.SPEAKER: {},
        }
        self._factories: Dict[EngineType, Any] = {
            EngineType.ASR: ASRClientFactory,
            EngineType.TTS: TTSClientFactory,
        }

        # 自动注册已知的引擎
        self._register_default_engines()

    def _register_default_engines(self):
        """注册默认引擎配置"""
        # ASR 引擎
        self.register_engine(EngineConfig(
            name="funasr",
            type=EngineType.ASR,
            display_name="FunASR",
            description="阿里达摩院 FunASR，本地语音识别",
            capabilities=["streaming", "diarization", "timestamps"],
            priority=100,
            fallback="nano-2512",
            params={"model": "paraformer-zh", "device": "cpu"}
        ))

        self.register_engine(EngineConfig(
            name="nano-2512",
            type=EngineType.ASR,
            display_name="Fun-ASR-Nano-2512",
            description="轻量级实时流式 ASR，<600ms 延迟",
            capabilities=["streaming", "realtime"],
            priority=90,
            fallback="funasr",
            params={"model": "nano-2512"}
        ))

        self.register_engine(EngineConfig(
            name="moss",
            type=EngineType.ASR,
            display_name="MOSS 云端",
            description="MOSS 云端语音识别 API",
            capabilities=["cloud", "high-accuracy"],
            priority=50,
            fallback="funasr",
            params={"api_key": ""}
        ))

        # TTS 引擎
        self.register_engine(EngineConfig(
            name="sherpa-vits",
            type=EngineType.TTS,
            display_name="Sherpa-ONNX VITS",
            description="VITS 中文语音合成，187 种音色",
            capabilities=["multi-voice", "emotions"],
            priority=100,
            params={"model": "vits-zh-fanchen-C"}
        ))

        self.register_engine(EngineConfig(
            name="sherpa-kokoro",
            type=EngineType.TTS,
            display_name="Sherpa-ONNX Kokoro",
            description="Kokoro 多语言语音合成，103 种音色",
            capabilities=["multi-lang", "multi-voice"],
            priority=80,
            params={"model": "kokoro"}
        ))

    def register_engine(self, config: EngineConfig):
        """注册引擎配置

        Args:
            config: 引擎配置
        """
        self._configs[config.type][config.name] = config

    def unregister_engine(self, engine_type: EngineType, name: str):
        """注销引擎"""
        if name in self._configs[engine_type]:
            del self._configs[engine_type][name]

    def get_engine_config(self, engine_type: EngineType, name: str) -> Optional[EngineConfig]:
        """获取引擎配置"""
        return self._configs[engine_type].get(name)

    def list_engines(self, engine_type: EngineType) -> List[EngineInfo]:
        """列出指定类型的所有引擎信息"""
        engines = []
        for name, config in self._configs[engine_type].items():
            factory = self._factories.get(engine_type)
            available = False

            if factory and engine_type in [EngineType.ASR, EngineType.TTS]:
                try:
                    available = factory.is_available(name) if hasattr(factory, 'is_available') else True
                except Exception:
                    available = False

            is_default = config.priority == max(
                (c.priority for c in self._configs[engine_type].values()),
                default=0
            )

            engines.append(EngineInfo(
                name=name,
                type=engine_type,
                display_name=getattr(config, 'display_name', name),
                description=getattr(config, 'description', ''),
                capabilities=getattr(config, 'capabilities', []),
                available=available,
                priority=config.priority,
                is_default=is_default
            ))

        # 按优先级排序
        engines.sort(key=lambda x: (-x.priority, x.name))
        return engines

    def list_available_engines(self, engine_type: EngineType) -> List[str]:
        """列出指定类型可用的引擎名称"""
        return [e.name for e in self.list_engines(engine_type) if e.available]

    def get_default_engine(self, engine_type: EngineType) -> Optional[str]:
        """获取指定类型的默认引擎"""
        engines = self.list_engines(engine_type)
        for engine in engines:
            if engine.is_default:
                return engine.name
        return engines[0].name if engines else None

    def create_engine(
        self,
        engine_type: EngineType,
        name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """创建引擎实例

        Args:
            engine_type: 引擎类型
            name: 引擎名称，不指定则使用默认引擎
            **kwargs: 引擎特定参数

        Returns:
            引擎实例
        """
        if name is None:
            name = self.get_default_engine(engine_type)
            if name is None:
                raise ValueError(f"No available engine for type: {engine_type}")

        config = self.get_engine_config(engine_type, name)
        if config and config.params:
            # 合并配置参数
            for key, value in config.params.items():
                if key not in kwargs:
                    kwargs[key] = value

        factory = self._factories.get(engine_type)
        if factory:
            return factory.create(name, **kwargs)

        raise ValueError(f"Unknown engine type: {engine_type}")

    def get_engine_info(self, engine_type: EngineType, name: str) -> Optional[EngineInfo]:
        """获取指定引擎的详细信息"""
        for engine in self.list_engines(engine_type):
            if engine.name == name:
                return engine
        return None

    def switch_engine(
        self,
        engine_type: EngineType,
        from_name: str,
        to_name: str,
        **kwargs
    ) -> Any:
        """切换引擎

        Args:
            engine_type: 引擎类型
            from_name: 当前引擎名称
            to_name: 目标引擎名称
            **kwargs: 新引擎参数

        Returns:
            新引擎实例
        """
        # 验证目标引擎是否存在
        if not self.get_engine_config(engine_type, to_name):
            raise ValueError(f"Engine not found: {to_name}")

        # 创建新引擎实例
        return self.create_engine(engine_type, to_name, **kwargs)


# 全局引擎管理器实例
_engine_manager: Optional[EngineManager] = None


def get_engine_manager() -> EngineManager:
    """获取全局引擎管理器实例"""
    global _engine_manager
    if _engine_manager is None:
        _engine_manager = EngineManager()
    return _engine_manager


def list_asr_engines() -> List[EngineInfo]:
    """列出所有 ASR 引擎"""
    return get_engine_manager().list_engines(EngineType.ASR)


def list_tts_engines() -> List[EngineInfo]:
    """列出所有 TTS 引擎"""
    return get_engine_manager().list_engines(EngineType.TTS)


def get_default_asr_engine() -> Optional[str]:
    """获取默认 ASR 引擎"""
    return get_engine_manager().get_default_engine(EngineType.ASR)


def get_default_tts_engine() -> Optional[str]:
    """获取默认 TTS 引擎"""
    return get_engine_manager().get_default_engine(EngineType.TTS)
