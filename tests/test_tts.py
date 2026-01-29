"""TTS 模块单元测试

测试 TTSClient 抽象基类和 SherpaTTSClient 实现。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入 TTS 模块
from tts.base import TTSClient, TTSResult


class TestTTSResult:
    """测试 TTSResult 数据类"""

    def test_create_result(self):
        """测试创建 TTSResult"""
        audio = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        result = TTSResult(
            audio=audio,
            sample_rate=16000,
            duration=0.0001875,
            text="你好",
            speaker_id=77,
        )

        assert result.audio is audio
        assert result.sample_rate == 16000
        assert result.duration == 0.0001875
        assert result.text == "你好"
        assert result.speaker_id == 77

    def test_result_without_speaker(self):
        """测试不带说话人 ID 的结果"""
        audio = np.array([0.1, 0.2], dtype=np.float32)
        result = TTSResult(
            audio=audio,
            sample_rate=16000,
            duration=0.000125,
            text="测试",
        )

        assert result.speaker_id is None

    def test_audio_properties(self):
        """测试音频属性"""
        audio = np.array([0.5, -0.5, 0.25], dtype=np.float32)
        result = TTSResult(
            audio=audio,
            sample_rate=16000,
            duration=0.0001875,
            text="测试",
        )

        assert result.audio.dtype == np.float32
        assert len(result.audio) == 3


class TestTTSClient:
    """测试 TTSClient 抽象基类"""

    def test_abstract_methods(self):
        """测试抽象方法必须被实现"""
        # 直接实例化应该失败
        with pytest.raises(TypeError):
            TTSClient()

    def test_concrete_implementation(self):
        """测试具体实现类"""
        # 创建一个 mock 实现
        class MockTTSClient(TTSClient):
            @property
            def name(self):
                return "mock-tts"

            @property
            def sample_rate(self):
                return 16000

            @property
            def num_speakers(self):
                return 10

            def generate(self, text, **kwargs):
                return TTSResult(
                    audio=np.array([0.1], dtype=np.float32),
                    sample_rate=16000,
                    duration=0.0000625,
                    text=text,
                    speaker_id=0,
                )

            def is_available(self):
                return True

            def close(self):
                pass

        client = MockTTSClient()
        assert client.name == "mock-tts"
        assert client.sample_rate == 16000
        assert client.num_speakers == 10
        assert client.is_available() is True

    def test_context_manager(self):
        """测试上下文管理器"""
        class MockTTSClient(TTSClient):
            @property
            def name(self):
                return "mock-tts"

            @property
            def sample_rate(self):
                return 16000

            @property
            def num_speakers(self):
                return None

            def generate(self, text, **kwargs):
                return TTSResult(
                    audio=np.array([0.1], dtype=np.float32),
                    sample_rate=16000,
                    duration=0.0000625,
                    text=text,
                )

            def is_available(self):
                return True

            def close(self):
                pass

        with MockTTSClient() as client:
            assert client.is_available()

    def test_repr(self):
        """测试 __repr__"""
        class MockTTSClient(TTSClient):
            @property
            def name(self):
                return "mock-tts"

            @property
            def sample_rate(self):
                return 16000

            @property
            def num_speakers(self):
                return 5

            def generate(self, text, **kwargs):
                pass

            def is_available(self):
                return True

            def close(self):
                pass

        client = MockTTSClient()
        assert "MockTTSClient" in repr(client)
        assert "mock-tts" in repr(client)


class TestTTSClientFactory:
    """测试 TTSClientFactory 工厂类"""

    def test_available_engines(self):
        """测试列出可用引擎"""
        from tts.factory import TTSClientFactory

        engines = TTSClientFactory.available_engines()
        assert isinstance(engines, list)
        assert "sherpa-vits" in engines
        assert "sherpa-kokoro" in engines

    def test_register_alias(self):
        """测试注册别名"""
        from tts.factory import TTSClientFactory

        # 创建一个 mock 引擎类
        class MockEngine(TTSClient):
            @property
            def name(self):
                return "mock-engine"

            @property
            def sample_rate(self):
                return 16000

            @property
            def num_speakers(self):
                return None

            def generate(self, text, **kwargs):
                pass

            def is_available(self):
                return True

            def close(self):
                pass

        TTSClientFactory.register("mock", MockEngine)
        TTSClientFactory.register_alias("alias", "mock")

        assert "mock" in TTSClientFactory.available_engines()

    def test_create_with_alias(self):
        """测试使用别名创建引擎"""
        from tts.factory import TTSClientFactory

        class MockEngine(TTSClient):
            @property
            def name(self):
                return "test-engine"

            @property
            def sample_rate(self):
                return 16000

            @property
            def num_speakers(self):
                return None

            def generate(self, text, **kwargs):
                pass

            def is_available(self):
                return True

            def close(self):
                pass

        TTSClientFactory.register("test-engine", MockEngine)
        TTSClientFactory.register_alias("alias", "test-engine")

        # 使用别名创建
        client = TTSClientFactory.create("alias")
        assert client.name == "test-engine"

    def test_create_unsupported_engine(self):
        """测试创建不支持的引擎"""
        from tts.factory import TTSClientFactory

        with pytest.raises(ValueError) as exc_info:
            TTSClientFactory.create("non-existent-engine")

        assert "Unsupported TTS engine" in str(exc_info.value)

    def test_is_available(self):
        """测试检查引擎可用性"""
        from tts.factory import TTSClientFactory

        class MockEngine(TTSClient):
            @property
            def name(self):
                return "mock"

            @property
            def sample_rate(self):
                return 16000

            @property
            def num_speakers(self):
                return None

            def generate(self, text, **kwargs):
                pass

            def is_available(self):
                return True

            def close(self):
                pass

        class FailingEngine(TTSClient):
            @property
            def name(self):
                return "fail"

            @property
            def sample_rate(self):
                return 16000

            @property
            def num_speakers(self):
                return None

            def generate(self, text, **kwargs):
                raise RuntimeError("Engine failed")

            def is_available(self):
                return False

            def close(self):
                pass

        TTSClientFactory.register("mock", MockEngine)
        TTSClientFactory.register("fail", FailingEngine)

        assert TTSClientFactory.is_available("mock") is True
        assert TTSClientFactory.is_available("fail") is False

    def test_get_engine_info(self):
        """测试获取引擎信息"""
        from tts.factory import TTSClientFactory

        class MockEngine(TTSClient):
            @property
            def name(self):
                return "mock-engine"

            @property
            def sample_rate(self):
                return 24000

            @property
            def num_speakers(self):
                return 100

            def generate(self, text, **kwargs):
                pass

            def is_available(self):
                return True

            def close(self):
                pass

        TTSClientFactory.register("mock-engine", MockEngine)

        info = TTSClientFactory.get_engine_info("mock-engine")
        assert info["name"] == "mock-engine"
        assert info["sample_rate"] == 24000
        assert info["num_speakers"] == 100
        assert info["available"] is True


class TestSherpaTTSClient:
    """测试 SherpaTTSClient 实现"""

    def test_model_not_found(self):
        """测试模型不存在时的错误"""
        from tts.sherpa_client import SherpaTTSClient

        with pytest.raises(FileNotFoundError) as exc_info:
            SherpaTTSClient(model="non-existent-model")

        assert "Model not found" in str(exc_info.value)

    @pytest.mark.skip(reason="需要实际的模型文件")
    def test_init_with_valid_model(self):
        """测试使用有效模型初始化"""
        from tts.sherpa_client import SherpaTTSClient

        client = SherpaTTSClient(
            model="vits-zh-hf-fanchen-C",
            speaker_id=77,
        )
        assert client.is_available()
        assert client.name == "sherpa-vits-zh-hf-fanchen-C"
        client.close()

    @pytest.mark.skip(reason="需要实际的模型文件")
    def test_generate_audio(self):
        """测试生成音频"""
        from tts.sherpa_client import SherpaTTSClient

        client = SherpaTTSClient(
            model="vits-zh-hf-fanchen-C",
            speaker_id=77,
            volume_db=25.0,
        )

        result = client.generate("你好，我是语音助手！")

        assert isinstance(result, TTSResult)
        assert result.sample_rate == 16000
        assert result.text == "你好，我是语音助手！"
        assert result.speaker_id == 77
        assert result.duration > 0
        assert len(result.audio) > 0
        assert -1.0 <= result.audio.min() <= result.audio.max() <= 1.0

        client.close()

    @pytest.mark.skip(reason="需要实际的模型文件")
    def test_volume_gain(self):
        """测试音量增益"""
        from tts.sherpa_client import SherpaTTSClient

        # 创建一个 client
        client = SherpaTTSClient(
            model="vits-zh-hf-fanchen-C",
            speaker_id=77,
            volume_db=0,  # 无增益
        )

        # 生成无增益的音频
        result_no_gain = client.generate("测试音量")

        # 设置增益
        client._volume_db = 25.0
        result_with_gain = client.generate("测试音量")

        # 增益后的音频应该振幅更大
        assert result_with_gain.audio.max() > result_no_gain.audio.max()

        client.close()

    def test_repr(self):
        """测试 __repr__"""
        from tts.sherpa_client import SherpaTTSClient

        # 使用 mock 避免加载真实模型
        with patch.object(SherpaTTSClient, '_init_engine'):
            client = SherpaTTSClient.__new__(SherpaTTSClient)
            client._model = "test-model"
            client._tts = Mock()
            client._tts.sample_rate = 16000
            client._tts.num_speakers = 10

            repr_str = repr(client)
            assert "SherpaTTSClient" in repr_str
            assert "test-model" in repr_str


class TestModuleExports:
    """测试模块导出"""

    def test_import_all(self):
        """测试导入所有公共 API"""
        from tts import (
            TTSClient,
            TTSResult,
            TTSClientFactory,
            SherpaTTSClient,
            create_tts_client,
        )

        assert TTSClient is not None
        assert TTSResult is not None
        assert TTSClientFactory is not None
        assert SherpaTTSClient is not None
        assert create_tts_client is not None

    def test_all_exports(self):
        """测试 __all__ 定义"""
        import tts

        expected = [
            "TTSClient",
            "TTSResult",
            "TTSClientFactory",
            "SherpaTTSClient",
        ]

        for name in expected:
            assert name in tts.__all__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
