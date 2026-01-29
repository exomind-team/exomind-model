"""Voice-IME 配置模块

提供统一的配置管理，支持 YAML 配置文件和环境变量覆盖。
"""

from .config import (
    Config,
    ASRConfig,
    TTSConfig,
    GlobalConfig,
    RecorderConfig,
    HotkeyConfig,
    ConfigLoader,
    get_config,
)

__all__ = [
    "Config",
    "ASRConfig",
    "TTSConfig",
    "GlobalConfig",
    "RecorderConfig",
    "HotkeyConfig",
    "ConfigLoader",
    "get_config",
]


def create_default_config(path: str = "config.yaml") -> str:
    """生成默认配置文件

    Args:
        path: 配置文件路径

    Returns:
        生成的配置内容
    """
    import yaml

    default_config = {
        "version": "1.0.0",
        "asr": {
            "primary_engine": "funasr",
            "fallback_engine": "nano-2512",
            "funasr": {
                "model": "paraformer-zh",
                "device": "cpu",
                "enable_diarization": False,
            },
            "nano": {
                "model": "nano-2512",
                "device": "cpu",
            },
            "moss": {
                "api_key": "${MOSS_API_KEY}",
            },
        },
        "tts": {
            "primary_engine": "sherpa-vits",
            "fallback_engine": "sherpa-kokoro",
            "sherpa_vits": {
                "model": "vits-zh-hf-fanchen-C",
                "speaker_id": 77,
                "volume_db": 25,
            },
            "sherpa_kokoro": {
                "model": "kokoro-multi-lang-v1_1",
                "voice": "af_bella",
                "speed": 1.0,
            },
        },
        "global": {
            "log_level": "INFO",
            "log_file": "logs/voice-ime.log",
            "temp_dir": "/tmp/voice-ime",
            "debug": False,
        },
        "recorder": {
            "sample_rate": 16000,
            "channels": 1,
            "dtype": "int16",
            "threshold": 0.02,
            " silence_duration": 1.0,
        },
        "hotkey": {
            "record": "f2",
            "toggle_mode": "hold",  # hold | toggle
        },
    }

    content = yaml.dump(default_config, default_flow_style=False, allow_unicode=True)

    # 写入文件
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

    return content
