"""
Service Configuration
=====================

服务配置管理模块。

从环境变量和配置文件加载服务配置。
"""

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """服务配置"""

    # 服务配置
    host: str = "0.0.0.0"
    port: int = 1921
    debug: bool = False
    title: str = "Voice-ime API"
    description: str = "本地语音识别和合成服务"
    version: str = "2.0.0"

    # ASR 配置
    asr_default_engine: str = "funasr"
    asr_fallback_engine: str = "moss"

    # TTS 配置
    tts_default_model: str = "vits-zh-hf-fanchen-C"
    tts_default_voice_id: int = 77
    tts_default_volume_db: float = 25.0
    tts_default_speed: float = 1.0

    # 路径配置
    model_path: Optional[str] = None
    cache_path: Optional[str] = None

    class Config:
        env_prefix = "VOICEIME_"
        env_file = ".env"
        extra = "ignore"  # 忽略额外环境变量（兼容旧项目配置）


@lru_cache()
def get_settings() -> Settings:
    """获取全局配置实例（单例模式）"""
    return Settings()


# 全局配置实例
settings = get_settings()
