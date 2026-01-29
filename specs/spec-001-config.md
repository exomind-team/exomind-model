# Voice-IME 配置管理规范

> **Spec ID**: spec-001-config
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29

## 1. 概述

本文档定义了 Voice-IME 项目的配置管理规范，统一管理应用配置。

## 2. 配置格式

### 2.1 配置文件

**位置**: `config.yaml`

```yaml
# Voice-IME 配置文件
# ===================

# ASR 引擎配置
asr:
  # 首选引擎: funasr | moss | nano-2512
  primary_engine: "funasr"
  # 回退引擎
  fallback_engine: "moss"
  # FunASR 配置
  funasr:
    model: "paraformer-zh"  # paraformer-zh | sensevoice | paraformer-en
    device: "cpu"           # cpu | cuda
    enable_diarization: false
  # MOSS 配置
  moss:
    api_key: "${MOSS_API_KEY}"  # 环境变量引用
  # Nano 配置
  nano:
    model: "nano-2512"
    device: "cpu"

# TTS 引擎配置
tts:
  # 首选引擎: sherpa-vits | sherpa-kokoro
  primary_engine: "sherpa-vits"
  # 回退引擎
  fallback_engine: "sherpa-kokoro"
  # Sherpa-VITS 配置
  sherpa_vits:
    model: "vits-zh-hf-fanchen-C"
    speaker_id: 77
    volume_db: 25
  # Sherpa-Kokoro 配置
  sherpa_kokoro:
    model: "kokoro-multi-lang-v1_1"
    voice: "af_bella"
    speed: 1.0

# 全局设置
global:
  # 日志级别: DEBUG | INFO | WARNING | ERROR
  log_level: "INFO"
  # 日志文件路径
  log_file: "logs/voice-ime.log"
  # 临时文件目录
  temp_dir: "/tmp/voice-ime"

# 录音配置
recorder:
  sample_rate: 16000
  channels: 1
  dtype: "int16"

# 快捷键配置
hotkey:
  # 录音开关快捷键
  record: "f2"
```

### 2.2 环境变量覆盖

支持通过环境变量覆盖配置：

| 环境变量 | 对应配置 | 说明 |
|---------|---------|------|
| `MOSS_API_KEY` | asr.moss.api_key | MOSS API 密钥 |
| `VOICE_IME_LOG_LEVEL` | global.log_level | 日志级别 |
| `VOICE_IME_DEVICE` | asr.funasr.device | 计算设备 |

## 3. 配置加载器

### 3.1 ConfigLoader 类

```python
from dataclasses import dataclass
from typing import Optional
import os
import yaml
from pathlib import Path

@dataclass
class ASRConfig:
    primary_engine: str = "funasr"
    fallback_engine: str = "moss"
    funasr_model: str = "paraformer-zh"
    funasr_device: str = "cpu"
    enable_diarization: bool = False
    moss_api_key: str = ""

@dataclass
class TTSConfig:
    primary_engine: str = "sherpa-vits"
    fallback_engine: str = "sherpa-kokoro"
    vits_model: str = "vits-zh-hf-fanchen-C"
    vits_speaker_id: int = 77
    vits_volume_db: int = 25
    kokoro_voice: str = "af_bella"
    kokoro_speed: float = 1.0

@dataclass
class GlobalConfig:
    log_level: str = "INFO"
    log_file: str = "logs/voice-ime.log"
    temp_dir: str = "/tmp/voice-ime"

@dataclass
class RecorderConfig:
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "int16"

@dataclass
class Config:
    asr: ASRConfig
    tts: TTSConfig
    global_settings: GlobalConfig
    recorder: RecorderConfig

class ConfigLoader:
    """配置加载器"""

    DEFAULT_PATH = "config.yaml"

    @classmethod
    def load(cls, path: Optional[str] = None) -> Config:
        """加载配置文件"""
        config_path = Path(path or cls.DEFAULT_PATH)

        if not config_path.exists():
            # 返回默认配置
            return cls._default_config()

        with open(config_path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f)

        # 解析环境变量引用
        raw = cls._resolve_env_vars(raw)

        return cls._parse_config(raw)

    @classmethod
    def _resolve_env_vars(cls, data: dict) -> dict:
        """解析 ${VAR} 格式的环境变量引用"""
        import re
        pattern = re.compile(r'\$\{(\w+)\}')

        def resolve(value):
            if isinstance(value, str) and (match := pattern.match(value)):
                env_key = match.group(1)
                return os.getenv(env_key, value)
            return value

        def traverse(obj):
            if isinstance(obj, dict):
                return {k: traverse(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [traverse(item) for item in obj]
            else:
                return resolve(obj)

        return traverse(data)

    @classmethod
    def _parse_config(cls, raw: dict) -> Config:
        """解析配置字典"""
        asr_cfg = raw.get('asr', {})
        tts_cfg = raw.get('tts', {})
        global_cfg = raw.get('global', {})
        recorder_cfg = raw.get('recorder', {})

        return Config(
            asr=ASRConfig(
                primary_engine=asr_cfg.get('primary_engine', 'funasr'),
                fallback_engine=asr_cfg.get('fallback_engine', 'moss'),
                funasr_model=asr_cfg.get('funasr', {}).get('model', 'paraformer-zh'),
                funasr_device=asr_cfg.get('funasr', {}).get('device', 'cpu'),
                enable_diarization=asr_cfg.get('funasr', {}).get('enable_diarization', False),
                moss_api_key=asr_cfg.get('moss', {}).get('api_key', ''),
            ),
            tts=TTSConfig(
                primary_engine=tts_cfg.get('primary_engine', 'sherpa-vits'),
                fallback_engine=tts_cfg.get('fallback_engine', 'sherpa-kokoro'),
                vits_model=tts_cfg.get('sherpa_vits', {}).get('model', 'vits-zh-hf-fanchen-C'),
                vits_speaker_id=tts_cfg.get('sherpa_vits', {}).get('speaker_id', 77),
                vits_volume_db=tts_cfg.get('sherpa_vits', {}).get('volume_db', 25),
                kokoro_voice=tts_cfg.get('sherpa_kokoro', {}).get('voice', 'af_bella'),
                kokoro_speed=tts_cfg.get('sherpa_kokoro', {}).get('speed', 1.0),
            ),
            global_settings=GlobalConfig(
                log_level=global_cfg.get('log_level', 'INFO'),
                log_file=global_cfg.get('log_file', 'logs/voice-ime.log'),
                temp_dir=global_cfg.get('temp_dir', '/tmp/voice-ime'),
            ),
            recorder=RecorderConfig(
                sample_rate=recorder_cfg.get('sample_rate', 16000),
                channels=recorder_cfg.get('channels', 1),
                dtype=recorder_cfg.get('dtype', 'int16'),
            ),
        )

    @classmethod
    def _default_config(cls) -> Config:
        """返回默认配置"""
        return Config(
            asr=ASRConfig(),
            tts=TTSConfig(),
            global_settings=GlobalConfig(),
            recorder=RecorderConfig(),
        )
```

## 4. 使用示例

```python
from config import ConfigLoader

# 加载配置
config = ConfigLoader.load("config.yaml")

# 使用配置
print(f"ASR Engine: {config.asr.primary_engine}")
print(f"TTS Model: {config.tts.vits_model}")
print(f"Log Level: {config.global_settings.log_level}")
```

## 5. 验收标准

- [ ] 配置文件支持 YAML 格式
- [ ] 支持环境变量覆盖
- [ ] 支持配置文件不存在时的默认配置
- [ ] 提供类型安全的配置访问接口
- [ ] 支持配置热重载（可选）

---

*本文档遵循 Voice-IME Spec 规范*
