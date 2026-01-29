"""配置加载器实现

支持 YAML 配置文件、环境变量覆盖、类型安全的配置访问。
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Any, Dict

import yaml


@dataclass
class ASRConfig:
    """ASR 引擎配置"""
    primary_engine: str = "funasr"
    fallback_engine: str = "nano-2512"
    # FunASR 配置
    funasr_model: str = "paraformer-zh"
    funasr_device: str = "cpu"
    enable_diarization: bool = False
    # Nano 配置
    nano_model: str = "nano-2512"
    nano_device: str = "cpu"
    # MOSS 配置
    moss_api_key: str = ""


@dataclass
class TTSConfig:
    """TTS 引擎配置"""
    primary_engine: str = "sherpa-vits"
    fallback_engine: str = "sherpa-kokoro"
    # Sherpa-VITS 配置
    vits_model: str = "vits-zh-hf-fanchen-C"
    vits_speaker_id: int = 77
    vits_volume_db: int = 25
    # Sherpa-Kokoro 配置
    kokoro_model: str = "kokoro-multi-lang-v1_1"
    kokoro_voice: str = "af_bella"
    kokoro_speed: float = 1.0


@dataclass
class GlobalConfig:
    """全局配置"""
    log_level: str = "INFO"
    log_file: str = "logs/voice-ime.log"
    temp_dir: str = "/tmp/voice-ime"
    debug: bool = False


@dataclass
class RecorderConfig:
    """录音配置"""
    sample_rate: int = 16000
    channels: int = 1
    dtype: str = "int16"
    threshold: float = 0.02
    silence_duration: float = 1.0


@dataclass
class HotkeyConfig:
    """快捷键配置"""
    record: str = "f2"
    toggle_mode: str = "hold"  # hold: 按住录音 | toggle: 切换录音


@dataclass
class Config:
    """主配置类"""
    asr: ASRConfig
    tts: TTSConfig
    global_settings: GlobalConfig
    recorder: RecorderConfig
    hotkey: HotkeyConfig
    version: str = "1.0.0"


class ConfigLoader:
    """配置加载器

    支持:
    - YAML 配置文件
    - 环境变量覆盖 ${VAR} 语法
    - 默认配置（配置文件不存在时）
    - 配置热重载
    """

    DEFAULT_PATH = "config.yaml"
    ENV_PREFIX = "VOICE_IME_"

    def __init__(self, path: Optional[str] = None):
        """初始化配置加载器

        Args:
            path: 配置文件路径，默认 config.yaml
        """
        self._path = path or self.DEFAULT_PATH
        self._config: Optional[Config] = None
        self._raw_config: Optional[Dict[str, Any]] = None

    def load(self, reload: bool = False) -> Config:
        """加载配置

        Args:
            reload: 是否重新加载（支持热重载）

        Returns:
            Config: 配置对象
        """
        if self._config is not None and not reload:
            return self._config

        config_path = Path(self._path)

        if config_path.exists():
            self._load_from_file(config_path)
        else:
            self._load_default()

        assert self._config is not None
        return self._config

    def _load_from_file(self, path: Path):
        """从文件加载配置"""
        with open(path, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f)

        if raw is None:
            raw = {}

        # 解析环境变量引用
        raw = self._resolve_env_vars(raw)

        # 解析配置
        self._config = self._parse_config(raw)

    def _load_default(self):
        """加载默认配置"""
        self._raw_config = {}
        self._config = self._default_config()

    def _resolve_env_vars(self, data: Any) -> Any:
        """解析环境变量引用 ${VAR}

        Args:
            data: 配置数据

        Returns:
            解析后的配置数据
        """
        pattern = re.compile(r'\$\{(\w+)\}')

        def resolve(value):
            if isinstance(value, str):
                # 匹配 ${VAR} 格式
                matches = pattern.findall(value)
                for var_name in matches:
                    env_value = os.getenv(var_name, "")
                    # 无论是否存在，都进行替换
                    value = value.replace(f"${{{var_name}}}", env_value)
                # 如果没有匹配，保持原值
                if not matches:
                    return value
            return value

        def traverse(obj):
            if isinstance(obj, dict):
                return {k: traverse(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [traverse(item) for item in obj]
            else:
                return resolve(obj)

        return traverse(data)

    def _parse_config(self, raw: Dict[str, Any]) -> Config:
        """解析配置字典

        Args:
            raw: 原始配置字典

        Returns:
            Config: 配置对象
        """
        # 解析各部分配置
        asr_cfg = raw.get('asr', {})
        tts_cfg = raw.get('tts', {})
        global_cfg = raw.get('global', {})
        recorder_cfg = raw.get('recorder', {})
        hotkey_cfg = raw.get('hotkey', {})

        # 解析 FunASR 配置
        funasr_cfg = asr_cfg.get('funasr', {})
        nano_cfg = asr_cfg.get('nano', {})
        moss_cfg = asr_cfg.get('moss', {})

        # 解析 Sherpa-VITS 配置
        sherpa_vits_cfg = tts_cfg.get('sherpa_vits', {})

        # 解析 Sherpa-Kokoro 配置
        sherpa_kokoro_cfg = tts_cfg.get('sherpa_kokoro', {})

        return Config(
            version=raw.get('version', '1.0.0'),
            asr=ASRConfig(
                primary_engine=asr_cfg.get('primary_engine', 'funasr'),
                fallback_engine=asr_cfg.get('fallback_engine', 'nano-2512'),
                funasr_model=funasr_cfg.get('model', 'paraformer-zh'),
                funasr_device=funasr_cfg.get('device', 'cpu'),
                enable_diarization=funasr_cfg.get('enable_diarization', False),
                nano_model=nano_cfg.get('model', 'nano-2512'),
                nano_device=nano_cfg.get('device', 'cpu'),
                moss_api_key=moss_cfg.get('api_key', ''),
            ),
            tts=TTSConfig(
                primary_engine=tts_cfg.get('primary_engine', 'sherpa-vits'),
                fallback_engine=tts_cfg.get('fallback_engine', 'sherpa-kokoro'),
                vits_model=sherpa_vits_cfg.get('model', 'vits-zh-hf-fanchen-C'),
                vits_speaker_id=sherpa_vits_cfg.get('speaker_id', 77),
                vits_volume_db=sherpa_vits_cfg.get('volume_db', 25),
                kokoro_model=sherpa_kokoro_cfg.get('model', 'kokoro-multi-lang-v1_1'),
                kokoro_voice=sherpa_kokoro_cfg.get('voice', 'af_bella'),
                kokoro_speed=sherpa_kokoro_cfg.get('speed', 1.0),
            ),
            global_settings=GlobalConfig(
                log_level=global_cfg.get('log_level', 'INFO'),
                log_file=global_cfg.get('log_file', 'logs/voice-ime.log'),
                temp_dir=global_cfg.get('temp_dir', '/tmp/voice-ime'),
                debug=global_cfg.get('debug', False),
            ),
            recorder=RecorderConfig(
                sample_rate=recorder_cfg.get('sample_rate', 16000),
                channels=recorder_cfg.get('channels', 1),
                dtype=recorder_cfg.get('dtype', 'int16'),
                threshold=recorder_cfg.get('threshold', 0.02),
                silence_duration=recorder_cfg.get('silence_duration', 1.0),
            ),
            hotkey=HotkeyConfig(
                record=hotkey_cfg.get('record', 'f2'),
                toggle_mode=hotkey_cfg.get('toggle_mode', 'hold'),
            ),
        )

    def _default_config(self) -> Config:
        """返回默认配置"""
        return Config(
            version="1.0.0",
            asr=ASRConfig(),
            tts=TTSConfig(),
            global_settings=GlobalConfig(),
            recorder=RecorderConfig(),
            hotkey=HotkeyConfig(),
        )

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键，支持点号分隔的路径，如 'asr.primary_engine'
            default: 默认值

        Returns:
            配置值
        """
        if self._config is None:
            self.load()

        # 解析路径
        parts = key.split('.')
        obj = self._config

        for part in parts:
            if hasattr(obj, part):
                obj = getattr(obj, part)
            else:
                return default

        return obj

    def reload(self) -> Config:
        """重新加载配置（支持热重载）"""
        self._config = None
        return self.load(reload=True)

    @property
    def path(self) -> str:
        """返回配置文件路径"""
        return str(self._path)


# 全局配置实例
_config_instance: Optional[ConfigLoader] = None


def get_config(path: Optional[str] = None) -> Config:
    """获取全局配置实例

    Args:
        path: 配置文件路径

    Returns:
        Config: 配置对象
    """
    global _config_instance

    if _config_instance is None:
        _config_instance = ConfigLoader(path)

    return _config_instance.load()


def reset_config():
    """重置全局配置实例"""
    global _config_instance
    _config_instance = None
