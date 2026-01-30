"""Speaker API 集成测试

测试 /v1/speaker/* 端点。
"""

import pytest
import tempfile
import wave
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
import sys
sys.path.insert(0, str(project_root))


def create_test_wav(path: str, duration: float = 3.0, sample_rate: int = 16000):
    """创建测试 WAV 文件"""
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        # 生成简单的正弦波
        import math
        import struct
        for i in range(int(duration * sample_rate)):
            value = int(32767 * 0.5 * math.sin(2 * math.pi * 440 * i / sample_rate))
            wf.writeframes(struct.pack('<h', value))


class TestSpeakerAPI:
    """Speaker API 测试类"""

    @pytest.fixture
    def test_wav_file(self):
        """创建测试 WAV 文件"""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name
        create_test_wav(temp_path, duration=3.0)
        yield temp_path
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        from service.main import app
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_diarize_endpoint_exists(self, client):
        """测试 diarize 端点存在"""
        response = client.post(
            "/v1/speaker/diarize",
            files={"audio": ("test.wav", b"", "audio/wav")}
        )
        # 应该返回 422 (验证错误) 而不是 404
        assert response.status_code in [400, 422, 500]

    def test_diarize_with_audio(self, client, test_wav_file):
        """测试带音频的说话人分离"""
        with open(test_wav_file, 'rb') as f:
            audio_data = f.read()

        response = client.post(
            "/v1/speaker/diarize",
            files={"audio": ("test.wav", audio_data, "audio/wav")},
            data={"engine": "mock", "num_speakers": "2"}
        )

        # Mock 引擎应该可用
        if response.status_code == 200:
            data = response.json()
            assert data["success"] is True
            assert data["engine"] == "mock"
            assert "segments" in data
            assert "num_speakers" in data
        elif response.status_code == 400:
            # 引擎不可用
            assert "不可用" in response.json()["detail"] or "available" in response.json()["detail"].lower()

    def test_diarize_invalid_format(self, client):
        """测试不支持格式"""
        response = client.post(
            "/v1/speaker/diarize",
            files={"audio": ("test.txt", b"text content", "text/plain")}
        )
        assert response.status_code == 400
        assert "不支持" in response.json()["detail"] or "不支持" in response.json()["detail"]

    def test_list_engines(self, client):
        """测试列出引擎"""
        response = client.get("/v1/speaker/engines")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert isinstance(data["engines"], list)

    def test_check_engine_health_mock(self, client):
        """测试检查 mock 引擎健康状态"""
        response = client.get("/v1/speaker/health/mock")
        assert response.status_code == 200
        data = response.json()
        assert data["engine"] == "mock"
        assert data["status"] in ["healthy", "unavailable"]

    def test_check_engine_health_invalid(self, client):
        """测试检查不存在的引擎"""
        response = client.get("/v1/speaker/health/non-existent-engine")
        assert response.status_code == 200
        data = response.json()
        assert data["engine"] == "non-existent-engine"
        assert data["status"] == "unavailable"


class TestSpeakerModels:
    """Speaker 数据模型测试"""

    def test_diarize_request_model(self):
        """测试请求模型"""
        from service.models.request import SpeakerDiarizeRequest, SpeakerEngine

        req = SpeakerDiarizeRequest(engine=SpeakerEngine.CAMPLUS, num_speakers=2)
        assert req.engine == "cam++"
        assert req.num_speakers == 2

    def test_diarize_result_model(self):
        """测试响应模型"""
        from service.models.response import SpeakerDiarizeResult, SpeakerDiarizeSegment

        segments = [
            SpeakerDiarizeSegment(speaker_id="S01", start_time=0.0, end_time=3.0, confidence=0.9),
            SpeakerDiarizeSegment(speaker_id="S02", start_time=3.0, end_time=6.0, confidence=0.85),
        ]

        result = SpeakerDiarizeResult(
            success=True,
            engine="mock",
            num_speakers=2,
            segments=segments,
            processing_time_ms=100
        )

        assert result.success is True
        assert result.engine == "mock"
        assert result.num_speakers == 2
        assert len(result.segments) == 2
        assert result.segments[0].speaker_id == "S01"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
