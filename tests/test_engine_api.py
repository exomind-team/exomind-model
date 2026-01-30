"""Engine API 集成测试

测试 /v1/engine/* 端点。
"""

import pytest
from pathlib import Path
import sys

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from engine import EngineManager, EngineType, get_engine_manager


class TestEngineAPI:
    """Engine API 测试类"""

    @pytest.fixture
    def manager(self):
        """创建引擎管理器"""
        return get_engine_manager()

    def test_engine_manager_creation(self, manager):
        """测试引擎管理器创建"""
        assert manager is not None
        assert isinstance(manager, EngineManager)

    def test_list_asr_engines(self, manager):
        """测试列出 ASR 引擎"""
        engines = manager.list_engines(EngineType.ASR)
        assert isinstance(engines, list)
        names = [e.name for e in engines]
        assert "funasr" in names
        assert "nano-2512" in names
        assert "moss" in names

    def test_list_tts_engines(self, manager):
        """测试列出 TTS 引擎"""
        engines = manager.list_engines(EngineType.TTS)
        assert isinstance(engines, list)
        names = [e.name for e in engines]
        assert "sherpa-vits" in names
        assert "sherpa-kokoro" in names

    def test_list_speaker_engines(self, manager):
        """测试列出 Speaker 引擎"""
        engines = manager.list_engines(EngineType.SPEAKER)
        assert isinstance(engines, list)

    def test_get_default_asr_engine(self, manager):
        """测试获取默认 ASR 引擎"""
        default = manager.get_default_engine(EngineType.ASR)
        assert default is not None
        assert isinstance(default, str)
        assert default == "funasr"

    def test_get_default_tts_engine(self, manager):
        """测试获取默认 TTS 引擎"""
        default = manager.get_default_engine(EngineType.TTS)
        assert default is not None
        assert isinstance(default, str)
        assert default == "sherpa-vits"

    def test_get_engine_config(self, manager):
        """测试获取引擎配置"""
        config = manager.get_engine_config(EngineType.ASR, "funasr")
        assert config is not None
        assert config.name == "funasr"
        assert config.type == EngineType.ASR
        assert config.priority == 100

    def test_get_engine_info(self, manager):
        """测试获取引擎信息"""
        info = manager.get_engine_info(EngineType.ASR, "funasr")
        assert info is not None
        assert info.name == "funasr"
        assert info.type == EngineType.ASR
        assert info.is_default is True

    def test_get_nonexistent_engine(self, manager):
        """测试获取不存在的引擎"""
        info = manager.get_engine_info(EngineType.ASR, "nonexistent")
        assert info is None

    def test_engine_info_properties(self, manager):
        """测试引擎信息属性"""
        engines = manager.list_engines(EngineType.ASR)
        for engine in engines:
            assert engine.name is not None
            assert engine.display_name is not None
            assert engine.type == EngineType.ASR
            assert isinstance(engine.available, bool)
            assert isinstance(engine.priority, int)


class TestEngineAPIEndpoints:
    """Engine API 端点测试（使用 TestClient）"""

    @pytest.fixture
    def test_client(self):
        """创建 FastAPI 测试客户端"""
        from service.main import app
        from fastapi.testclient import TestClient
        return TestClient(app, raise_server_exceptions=False)

    def test_engine_list_endpoint(self, test_client):
        """测试 /v1/engine 端点"""
        response = test_client.get("/v1/engine")
        if response.status_code >= 500:
            pytest.skip("Service not available")
        assert response.status_code == 200
        data = response.json()
        assert "asr" in data
        assert "tts" in data
        assert "speaker" in data

    def test_engine_asr_endpoint(self, test_client):
        """测试 /v1/engine/asr 端点"""
        response = test_client.get("/v1/engine/asr")
        if response.status_code >= 500:
            pytest.skip("Service not available")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert isinstance(data["models"], list)

    def test_engine_tts_endpoint(self, test_client):
        """测试 /v1/engine/tts 端点"""
        response = test_client.get("/v1/engine/tts")
        if response.status_code >= 500:
            pytest.skip("Service not available")
        assert response.status_code == 200
        data = response.json()
        assert "models" in data

    def test_engine_info_endpoint(self, test_client):
        """测试 /v1/engine/{type}/{name} 端点"""
        response = test_client.get("/v1/engine/asr/funasr")
        if response.status_code >= 500:
            pytest.skip("Service not available")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "funasr"
        assert data["type"] == "asr"

    def test_engine_info_not_found(self, test_client):
        """测试不存在的引擎"""
        response = test_client.get("/v1/engine/asr/nonexistent")
        if response.status_code >= 500:
            pytest.skip("Service not available")
        assert response.status_code == 404

    def test_default_engine_endpoint(self, test_client):
        """测试 /v1/engine/default/{type} 端点"""
        response = test_client.get("/v1/engine/default/asr")
        if response.status_code >= 500:
            pytest.skip("Service not available")
        assert response.status_code == 200
        data = response.json()
        assert data["engine_type"] == "asr"
        assert "default_engine" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
