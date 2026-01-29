"""
Configuration for Privacy Gateway
"""

from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path


class PrivacyGatewaySettings(BaseSettings):
    """隐私网关配置"""

    # 启用控制
    enabled: bool = False  # 默认关闭，需手动启用

    # 存储配置
    token_store_path: Path = Path("~/.cache/voice-ime/pii_tokens.json")

    # 跳过模式（不进行隐私检测的文本模式）
    bypass_patterns: list = []

    # Token 前缀格式
    token_prefix: str = "[PII_{type}_{id}]"

    class Config:
        env_prefix = "PRIVACY_GATEWAY_"


# 全局设置实例
settings = PrivacyGatewaySettings()
