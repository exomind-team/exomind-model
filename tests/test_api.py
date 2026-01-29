"""
Service API Tests
=================

测试服务 API 端点。
"""

import sys
from pathlib import Path

# 动态添加项目根目录到 sys.path（确保在 tests 目录之前）
FILE = Path(__file__).resolve()
ROOT = FILE.parents[2] / "voice-ime"
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

import pytest
from httpx import AsyncClient, ASGITransport
from service.main import app


@pytest.fixture
async def client():
    """测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_audio_bytes():
    """模拟音频字节"""
    return b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"


class TestHealthEndpoint:
    """健康检查端点测试"""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查返回正常状态"""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestRootEndpoint:
    """根路径端点测试"""

    @pytest.mark.asyncio
    async def test_root_returns_service_info(self, client):
        """测试根路径返回服务信息"""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Voice-ime"
        assert "version" in data
        assert "docs" in data
        assert "health" in data


class TestASREndpoints:
    """ASR 端点测试"""

    @pytest.mark.asyncio
    async def test_transcribe_with_audio(self, client, sample_audio_bytes):
        """测试音频转写"""
        response = await client.post(
            "/v1/asr/transcribe",
            files={"audio": ("test.wav", sample_audio_bytes, "audio/wav")},
            data={"model": "paraformer-zh"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "text" in data
        assert data["model"] == "paraformer-zh"

    @pytest.mark.asyncio
    async def test_transcribe_with_nano_model(self, client, sample_audio_bytes):
        """测试使用 nano-2512 模型转写"""
        response = await client.post(
            "/v1/asr/transcribe",
            files={"audio": ("test.wav", sample_audio_bytes, "audio/wav")},
            data={"model": "nano-2512"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["model"] == "nano-2512"

    @pytest.mark.asyncio
    async def test_transcribe_invalid_format(self, client):
        """测试不支持的音频格式"""
        response = await client.post(
            "/v1/asr/transcribe",
            files={"audio": ("test.txt", b"text content", "text/plain")},
            data={"model": "paraformer-zh"}
        )
        assert response.status_code == 400
        assert "不支持" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_list_models(self, client):
        """测试列出 ASR 模型"""
        response = await client.get("/v1/asr/models")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert len(data["models"]) >= 3
        # 检查默认模型
        default_models = [m for m in data["models"] if m.get("default")]
        assert len(default_models) >= 1


class TestTTSEndpoints:
    """TTS 端点测试"""

    @pytest.mark.asyncio
    async def test_synthesize_text(self, client):
        """测试文本合成"""
        response = await client.post(
            "/v1/tts/synthesize",
            json={
                "text": "你好，这是测试",
                "voice_id": 77
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["voice_id"] == 77

    @pytest.mark.asyncio
    async def test_synthesize_with_speed(self, client):
        """测试带语速参数的合成"""
        response = await client.post(
            "/v1/tts/synthesize",
            json={
                "text": "测试文本",
                "voice_id": 77,
                "speed": 1.5
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_list_voices(self, client):
        """测试列出音色"""
        response = await client.get("/v1/tts/voices")
        assert response.status_code == 200
        data = response.json()
        assert "voices" in data
        assert "pagination" in data
        assert len(data["voices"]) >= 1

    @pytest.mark.asyncio
    async def test_list_voices_with_filter(self, client):
        """测试带筛选条件的音色列表"""
        response = await client.get("/v1/tts/voices?gender=female")
        assert response.status_code == 200
        data = response.json()
        # 检查筛选是否生效
        for voice in data["voices"]:
            assert voice["gender"].lower() == "female"

    @pytest.mark.asyncio
    async def test_voice_sample_exists(self, client):
        """测试获取存在的音色样例"""
        response = await client.get("/v1/tts/samples/77.wav")
        # 204 No Content 或 200 都是可接受的
        assert response.status_code in [200, 204]

    @pytest.mark.asyncio
    async def test_voice_sample_not_found(self, client):
        """测试获取不存在的音色样例"""
        response = await client.get("/v1/tts/samples/999.wav")
        assert response.status_code == 404


class TestAdminEndpoints:
    """Admin 端点测试"""

    @pytest.mark.asyncio
    async def test_get_status(self, client):
        """测试获取服务状态"""
        response = await client.get("/v1/admin/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "uptime_seconds" in data
        assert "loaded_models" in data


class TestDocsEndpoints:
    """文档端点测试"""

    @pytest.mark.asyncio
    async def test_agent_docs_exists(self, client):
        """测试 Agent 文档端点存在"""
        response = await client.get("/v1/docs/agent")
        assert response.status_code == 200
        data = response.json()
        assert "service" in data
        assert "endpoints" in data
        assert "models" in data

    @pytest.mark.asyncio
    async def test_agent_docs_contains_endpoints(self, client):
        """测试 Agent 文档包含端点信息"""
        response = await client.get("/v1/docs/agent")
        data = response.json()
        assert "asr_transcribe" in data["endpoints"]
        assert "tts_synthesize" in data["endpoints"]
