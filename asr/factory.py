"""
ASR Client Factory
==================

ASR 客户端工厂类。

负责创建和管理 ASR 引擎实例，
支持引擎热切换、自动回退和智能选择。
"""

from typing import Optional, Tuple
from .base import ASRClient
from .moss_client import MossClient
from .funasr_client import FunASRClient
from .nano_client import FunASRNanoClient
from .selector import EngineSelector, AudioContext, SelectionResult


class ASRClientFactory:
    """ASR 客户端工厂"""

    # 注册的引擎
    _engines = {
        'moss': MossClient,
        'funasr': FunASRClient,
        'nano-2512': FunASRNanoClient,
        'nano-mlt': FunASRNanoClient,
    }
    
    @classmethod
    def create(cls, engine: str, **kwargs) -> ASRClient:
        """
        创建 ASR 客户端
        
        Args:
            engine: 引擎名称 ('moss' | 'funasr')
            **kwargs: 引擎特定配置
            
        Returns:
            ASRClient 实例
        """
        if engine not in cls._engines:
            raise ValueError(f"Unknown ASR engine: {engine}")
        
        return cls._engines[engine](**kwargs)
    
    @classmethod
    def register(cls, name: str, client_class: type):
        """
        注册新的 ASR 引擎
        
        Args:
            name: 引擎名称
            client_class: 引擎类（必须是 ASRClient 子类）
        """
        if not issubclass(client_class, ASRClient):
            raise TypeError(f"{client_class} must be a subclass of ASRClient")
        cls._engines[name] = client_class
    
    @classmethod
    def get_available_engines(cls) -> list[str]:
        """获取可用的引擎列表"""
        return list(cls._engines.keys())
    
    @classmethod
    def create_with_fallback(cls, primary_engine: str, fallback_engine: str = 'moss', **kwargs) -> ASRClient:
        """
        创建 ASR 客户端，失败自动回退

        Args:
            primary_engine: 首选引擎
            fallback_engine: 回退引擎 (默认: 'moss')
            **kwargs: 引擎特定配置

        Returns:
            ASRClient 实例（首选或回退引擎）
        """
        # 获取回退引擎需要的参数
        fallback_kwargs = kwargs.copy()
        if fallback_engine == 'moss':
            # MOSS 需要 api_key
            fallback_kwargs = {'api_key': kwargs.get('api_key', '')}
        elif fallback_engine == 'funasr':
            # FunASR 需要 model 和 device
            # 兼容 'model' 和 'funasr_model' 两种参数名
            fallback_kwargs = {
                'model': kwargs.get('model') or kwargs.get('funasr_model', 'paraformer-zh'),
                'device': kwargs.get('device') or kwargs.get('funasr_device', 'cpu')
            }

        # 首选引擎
        try:
            if primary_engine == 'funasr':
                # FunASR (paraformer-zh, sensevoice)
                primary_kwargs = {
                    'model': kwargs.get('model') or kwargs.get('funasr_model', 'paraformer-zh'),
                    'device': kwargs.get('device') or kwargs.get('funasr_device', 'cpu'),
                    'enable_diarization': kwargs.get('enable_diarization', False),
                }
            elif primary_engine in ('nano-2512', 'nano-mlt'):
                # Fun-ASR-Nano-2512
                primary_kwargs = {
                    'model': kwargs.get('model') or primary_engine,
                    'device': kwargs.get('device') or kwargs.get('nano_device', 'cpu'),
                }
            elif primary_engine == 'moss':
                primary_kwargs = {'api_key': kwargs.get('api_key', '')}
            else:
                primary_kwargs = kwargs

            client = cls.create(primary_engine, **primary_kwargs)
            if client.is_available:
                return client
        except Exception as e:
            print(f"⚠️  {primary_engine} 初始化失败: {e}")

        # 自动回退
        if primary_engine in ('funasr', 'nano-2512', 'nano-mlt'):
            print(f"🔄 自动回退到 {fallback_engine}...")
            if fallback_engine == 'moss':
                if not fallback_kwargs.get('api_key'):
                    raise RuntimeError("无法回退到 MOSS：缺少 API Key")
                return cls.create('moss', **fallback_kwargs)
            elif fallback_engine == 'funasr':
                return cls.create('funasr', **fallback_kwargs)

        # 无可回退
        raise RuntimeError(f"无法初始化 {primary_engine}，且无回退选项")

    @classmethod
    def create_smart(
        cls,
        context: AudioContext,
        explain: bool = False,
        **kwargs
    ) -> Tuple[ASRClient, SelectionResult]:
        """
        智能创建 ASR 客户端

        根据音频上下文自动选择最佳引擎。

        Args:
            context: 音频上下文（时长、语言、说话人等）
            explain: 是否显示选择解释
            **kwargs: 引擎特定配置

        Returns:
            tuple[ASRClient, SelectionResult]: (客户端实例, 选择结果)

        Example:
            >>> context = AudioContext(
            ...     duration_seconds=30.0,
            ...     language_hint="zh",
            ...     is_streaming=True,
            ... )
            >>> client, result = ASRClientFactory.create_smart(context, explain=True)
            >>> print(f"推荐引擎: {result.recommended_engine}")
        """
        # 创建选择器并选择引擎
        selector = EngineSelector(available_engines=cls.get_available_engines())
        result = selector.select(context)

        if explain:
            print(f"🎯 智能选择: {result.recommended_engine}")
            print(f"📊 置信度: {result.confidence:.1%}")
            print(f"📋 场景: {result.scenario.name}")
            for reason in result.score.reasons:
                print(f"   • {reason}")
            if result.alternatives:
                print(f"🔄 备选: {', '.join(result.alternatives)}")

        # 创建客户端（带回退）
        client = cls.create_with_fallback(
            primary_engine=result.recommended_engine,
            fallback_engine=result.fallback_engine,
            **kwargs
        )

        return client, result
