"""Speaker 模块单元测试

测试 SpeakerClient 抽象基类和 CAM++ 客户端实现。
"""

import pytest
import tempfile
import os
from pathlib import Path
import numpy as np
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入 Speaker 模块
from speaker.base import (
    SpeakerClient,
    SpeakerEmbedding,
    SpeakerVerificationResult,
    SpeakerSegment,
)
from speaker.factory import (
    SpeakerClientFactory,
    create_speaker_client,
)


class TestSpeakerEmbedding:
    """测试 SpeakerEmbedding 数据类"""

    def test_create_embedding(self):
        """测试创建声纹"""
        embedding = np.random.randn(192).astype(np.float32)
        spk = SpeakerEmbedding(
            speaker_id="test_user",
            embedding=embedding,
            name="测试用户",
        )

        assert spk.speaker_id == "test_user"
        assert spk.name == "测试用户"
        assert len(spk.embedding) == 192
        assert spk.sample_rate == 16000

    def test_embedding_save_load(self):
        """测试声纹保存和加载"""
        embedding = np.random.randn(192).astype(np.float32)
        spk = SpeakerEmbedding(
            speaker_id="save_test",
            embedding=embedding,
            name="保存测试",
            sample_rate=16000,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            spk.save(tmpdir)

            # 验证文件存在
            assert os.path.exists(os.path.join(tmpdir, "save_test.npy"))
            assert os.path.exists(os.path.join(tmpdir, "save_test.json"))

            # 加载
            loaded = SpeakerEmbedding.load("save_test", tmpdir)
            assert loaded.speaker_id == "save_test"
            assert loaded.name == "保存测试"
            assert len(loaded.embedding) == 192

            # 验证向量相等
            np.testing.assert_array_almost_equal(
                loaded.embedding, embedding
            )

    def test_embedding_without_name(self):
        """测试不带名称的声纹"""
        embedding = np.random.randn(192).astype(np.float32)
        spk = SpeakerEmbedding(
            speaker_id="no_name",
            embedding=embedding,
        )

        assert spk.name is None


class TestSpeakerVerificationResult:
    """测试 SpeakerVerificationResult 数据类"""

    def test_create_result(self):
        """测试创建验证结果"""
        result = SpeakerVerificationResult(
            is_verified=True,
            confidence=0.85,
            threshold=0.5,
        )

        assert result.is_verified is True
        assert result.confidence == 0.85
        assert result.threshold == 0.5
        assert result.embedding is None

    def test_result_with_embedding(self):
        """测试带声纹向量的结果"""
        embedding = np.random.randn(192).astype(np.float32)
        result = SpeakerVerificationResult(
            is_verified=False,
            confidence=0.3,
            threshold=0.5,
            embedding=embedding,
        )

        assert result.embedding is embedding


class TestSpeakerSegment:
    """测试 SpeakerSegment 数据类"""

    def test_create_segment(self):
        """测试创建说话人片段"""
        segment = SpeakerSegment(
            speaker_id="S01",
            start_time=0.0,
            end_time=3.5,
            confidence=0.92,
        )

        assert segment.speaker_id == "S01"
        assert segment.start_time == 0.0
        assert segment.end_time == 3.5
        assert segment.confidence == 0.92


class TestSpeakerClient:
    """测试 SpeakerClient 抽象基类"""

    def test_abstract_methods(self):
        """测试抽象方法必须被实现"""
        with pytest.raises(TypeError):
            SpeakerClient()

    def test_concrete_implementation(self):
        """测试具体实现类"""
        class MockSpeakerClient(SpeakerClient):
            @property
            def name(self):
                return "mock"

            @property
            def embedding_dim(self):
                return 192

            def extract_embedding(self, audio_path):
                return np.random.randn(192).astype(np.float32)

            def verify(self, audio_path, embedding, threshold=0.5):
                return SpeakerVerificationResult(
                    is_verified=True,
                    confidence=0.9,
                    threshold=threshold,
                )

            def diarize(self, audio_path, num_speakers=None):
                return []

            def is_available(self):
                return True

        client = MockSpeakerClient()
        assert client.name == "mock"
        assert client.embedding_dim == 192
        assert client.is_available()

    def test_context_manager(self):
        """测试上下文管理器"""
        class MockSpeakerClient(SpeakerClient):
            @property
            def name(self):
                return "mock"

            @property
            def embedding_dim(self):
                return 192

            def extract_embedding(self, audio_path):
                return np.random.randn(192).astype(np.float32)

            def verify(self, audio_path, embedding, threshold=0.5):
                return SpeakerVerificationResult(
                    is_verified=True,
                    confidence=0.9,
                    threshold=threshold,
                )

            def diarize(self, audio_path, num_speakers=None):
                return []

            def is_available(self):
                return True

        with MockSpeakerClient() as client:
            assert client.is_available()


class TestSpeakerClientFactory:
    """测试 SpeakerClientFactory 工厂类"""

    def test_available_engines(self):
        """测试列出可用引擎"""
        engines = SpeakerClientFactory.available_engines()
        assert isinstance(engines, list)
        assert "mock" in engines

    def test_create_mock_engine(self):
        """测试创建 mock 引擎"""
        client = create_speaker_client(engine="mock")
        assert client.name == "mock-speaker"

    def test_create_unsupported_engine(self):
        """测试创建不支持的引擎"""
        with pytest.raises(ValueError) as exc_info:
            SpeakerClientFactory.create("non-existent-engine")

        assert "Unsupported speaker engine" in str(exc_info.value)

    def test_is_available(self):
        """测试检查引擎可用性"""
        assert SpeakerClientFactory.is_available("mock") is True
        assert SpeakerClientFactory.is_available("non-existent") is False

    def test_get_engine_info(self):
        """测试获取引擎信息"""
        info = SpeakerClientFactory.get_engine_info("mock")
        assert info["name"] == "mock"
        assert info["available"] is True


class TestCAMPlusClient:
    """测试 CAMPlusClient 实现"""

    def test_client_creation(self):
        """测试客户端创建"""
        from speaker.camplus_client import CAMPlusClient

        client = CAMPlusClient()
        assert client.name == "cam++"
        assert client.embedding_dim == 192

    def test_check_dependencies(self):
        """测试依赖检查"""
        from speaker.camplus_client import CAMPlusClient

        # 模拟引擎总是可用的
        # 实际测试会因环境而异
        available = CAMPlusClient.check_dependencies()
        # 这个测试只检查函数能正常调用，返回布尔值
        assert isinstance(available, bool)


class TestModuleExports:
    """测试模块导出"""

    def test_import_all(self):
        """测试导入所有公共 API"""
        from speaker import (
            SpeakerClient,
            SpeakerEmbedding,
            SpeakerVerificationResult,
            SpeakerSegment,
            SpeakerClientFactory,
            create_speaker_client,
        )

        assert SpeakerClient is not None
        assert SpeakerEmbedding is not None
        assert SpeakerVerificationResult is not None
        assert SpeakerSegment is not None
        assert SpeakerClientFactory is not None
        assert create_speaker_client is not None

    def test_all_defined(self):
        """测试 __all__ 定义"""
        import speaker

        expected = [
            "SpeakerClient",
            "SpeakerEmbedding",
            "SpeakerVerificationResult",
            "SpeakerSegment",
            "SpeakerClientFactory",
            "create_speaker_client",
        ]

        for name in expected:
            assert name in speaker.__all__


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
