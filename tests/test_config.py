"""配置模块单元测试

测试 ConfigLoader 和配置解析功能。
"""

import pytest
import os
import tempfile
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.config import (
    Config,
    ASRConfig,
    TTSConfig,
    GlobalConfig,
    RecorderConfig,
    HotkeyConfig,
    ConfigLoader,
    get_config,
    reset_config,
)


class TestConfigClasses:
    """测试配置数据类"""

    def test_asr_config_defaults(self):
        """测试 ASR 默认配置"""
        config = ASRConfig()
        assert config.primary_engine == "funasr"
        assert config.fallback_engine == "nano-2512"
        assert config.funasr_model == "paraformer-zh"
        assert config.funasr_device == "cpu"
        assert config.enable_diarization is False

    def test_tts_config_defaults(self):
        """测试 TTS 默认配置"""
        config = TTSConfig()
        assert config.primary_engine == "sherpa-vits"
        assert config.vits_speaker_id == 77
        assert config.vits_volume_db == 25

    def test_global_config_defaults(self):
        """测试全局默认配置"""
        config = GlobalConfig()
        assert config.log_level == "INFO"
        assert config.temp_dir == "/tmp/voice-ime"
        assert config.debug is False

    def test_recorder_config_defaults(self):
        """测试录音默认配置"""
        config = RecorderConfig()
        assert config.sample_rate == 16000
        assert config.channels == 1
        assert config.dtype == "int16"

    def test_hotkey_config_defaults(self):
        """测试快捷键默认配置"""
        config = HotkeyConfig()
        assert config.record == "f2"
        assert config.toggle_mode == "hold"


class TestConfigLoader:
    """测试配置加载器"""

    def test_load_default_config(self):
        """测试加载默认配置（无配置文件）"""
        reset_config()
        loader = ConfigLoader("/nonexistent/config.yaml")
        config = loader.load()

        assert isinstance(config, Config)
        assert config.asr.primary_engine == "funasr"
        assert config.tts.vits_speaker_id == 77

    def test_load_from_yaml(self):
        """测试从 YAML 文件加载配置"""
        yaml_content = """
version: "1.0.0"

asr:
  primary_engine: "nano-2512"
  funasr:
    model: "sensevoice"
    device: "cuda"

tts:
  primary_engine: "sherpa-kokoro"
  sherpa_vits:
    speaker_id: 99
    volume_db: 30

global:
  log_level: "DEBUG"
  debug: true

recorder:
  sample_rate: 44100
  channels: 2

hotkey:
  record: "ctrl+space"
  toggle_mode: "toggle"
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                reset_config()
                loader = ConfigLoader(f.name)
                config = loader.load()

                assert config.version == "1.0.0"
                assert config.asr.primary_engine == "nano-2512"
                assert config.asr.funasr_model == "sensevoice"
                assert config.asr.funasr_device == "cuda"
                assert config.tts.vits_speaker_id == 99
                assert config.tts.vits_volume_db == 30
                assert config.global_settings.log_level == "DEBUG"
                assert config.global_settings.debug is True
                assert config.recorder.sample_rate == 44100
                assert config.recorder.channels == 2
                assert config.hotkey.record == "ctrl+space"
                assert config.hotkey.toggle_mode == "toggle"
            finally:
                os.unlink(f.name)

    def test_env_var_substitution(self):
        """测试环境变量替换"""
        os.environ["TEST_API_KEY"] = "secret-key-123"

        yaml_content = """
asr:
  moss:
    api_key: "${TEST_API_KEY}"
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                reset_config()
                loader = ConfigLoader(f.name)
                config = loader.load()

                assert config.asr.moss_api_key == "secret-key-123"
            finally:
                os.unlink(f.name)
                del os.environ["TEST_API_KEY"]

    def test_missing_env_var(self):
        """测试缺失的环境变量"""
        # 确保环境变量不存在
        env_var = "NONEXISTENT_VAR_12345"
        if env_var in os.environ:
            del os.environ[env_var]

        yaml_content = f"""
asr:
  moss:
    api_key: "${{{env_var}}}"
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                reset_config()
                loader = ConfigLoader(f.name)
                config = loader.load()

                # 缺失的环境变量应返回空字符串
                assert config.asr.moss_api_key == ""
            finally:
                os.unlink(f.name)

    def test_get_method(self):
        """测试 get 方法"""
        yaml_content = """
asr:
  primary_engine: "test-engine"
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                reset_config()
                loader = ConfigLoader(f.name)
                config = loader.load()

                assert loader.get("asr.primary_engine") == "test-engine"
                assert loader.get("nonexistent.key", "default") == "default"
            finally:
                os.unlink(f.name)

    def test_reload(self):
        """测试配置热重载"""
        yaml_content_1 = """
asr:
  primary_engine: "engine-1"
"""
        yaml_content_2 = """
asr:
  primary_engine: "engine-2"
"""

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(yaml_content_1)
            f.flush()

            try:
                reset_config()
                loader = ConfigLoader(f.name)
                config1 = loader.load()
                assert config1.asr.primary_engine == "engine-1"

                # 修改文件
                with open(f.name, 'w') as f2:
                    f2.write(yaml_content_2)

                # 重新加载
                config2 = loader.reload()
                assert config2.asr.primary_engine == "engine-2"
            finally:
                os.unlink(f.name)


class TestGlobalConfig:
    """测试全局配置函数"""

    def test_get_config_singleton(self):
        """测试全局配置单例"""
        reset_config()
        config1 = get_config()
        config2 = get_config()

        assert config1 is config2

    def test_reset_config(self):
        """测试重置全局配置"""
        reset_config()
        config1 = get_config()

        reset_config()
        config2 = get_config()

        # 重置后应该是不同的加载器实例
        assert config1 is not config2


class TestModuleExports:
    """测试模块导出"""

    def test_import_all(self):
        """测试导入所有公共 API"""
        from config import (
            Config,
            ASRConfig,
            TTSConfig,
            GlobalConfig,
            RecorderConfig,
            HotkeyConfig,
            ConfigLoader,
            get_config,
        )

        assert Config is not None
        assert ASRConfig is not None
        assert TTSConfig is not None
        assert GlobalConfig is not None
        assert RecorderConfig is not None
        assert HotkeyConfig is not None
        assert ConfigLoader is not None
        assert get_config is not None


class TestConfigValidation:
    """测试配置验证"""

    def test_empty_yaml_file(self):
        """测试空 YAML 文件"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write("")
            f.flush()

            try:
                reset_config()
                loader = ConfigLoader(f.name)
                config = loader.load()

                # 应该使用默认值
                assert config.asr.primary_engine == "funasr"
            finally:
                os.unlink(f.name)

    def test_partial_config(self):
        """测试部分配置（只覆盖部分字段）"""
        yaml_content = """
asr:
  primary_engine: "custom-engine"
"""
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yaml', delete=False
        ) as f:
            f.write(yaml_content)
            f.flush()

            try:
                reset_config()
                loader = ConfigLoader(f.name)
                config = loader.load()

                # 自定义字段应该生效
                assert config.asr.primary_engine == "custom-engine"
                # 其他字段应该使用默认值
                assert config.asr.fallback_engine == "nano-2512"
                assert config.tts.vits_speaker_id == 77
            finally:
                os.unlink(f.name)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
