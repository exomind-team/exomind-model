"""
Model Tests
===========

测试 Pydantic 数据模型。
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
from pydantic import ValidationError
from service.models.request import ASRTranscribeRequest, TTSSynthesizeRequest
from service.models.response import (
    ASRResult, TTSResult, VoiceInfo, VoiceListResponse,
    ModelInfo, ModelListResponse, ServiceStatus, HealthResponse
)


class TestASRRequestModel:
    """ASR 请求模型测试"""

    def test_default_values(self):
        """测试默认值"""
        request = ASRTranscribeRequest()
        assert request.model.value == "paraformer-zh"
        assert request.enable_diarization is False
        assert request.language == "zh"
        assert request.response_format == "json"

    def test_custom_values(self):
        """测试自定义值"""
        request = ASRTranscribeRequest(
            model="nano-2512",
            enable_diarization=True,
            language="en"
        )
        assert request.model.value == "nano-2512"
        assert request.enable_diarization is True
        assert request.language == "en"


class TestTTSRequestModel:
    """TTS 请求模型测试"""

    def test_default_values(self):
        """测试默认值"""
        request = TTSSynthesizeRequest(text="测试")
        assert request.model.value == "vits-zh-hf-fanchen-C"
        assert request.voice_id == 77
        assert request.speed == 1.0
        assert request.volume_db == 25.0
        assert request.format.value == "wav"

    def test_speed_range(self):
        """测试语速范围"""
        # 有效范围
        request = TTSSynthesizeRequest(text="测试", speed=0.5)
        assert request.speed == 0.5

        request = TTSSynthesizeRequest(text="测试", speed=2.0)
        assert request.speed == 2.0

        # 无效值应抛出异常
        with pytest.raises(ValidationError):
            TTSSynthesizeRequest(text="测试", speed=0.1)

        with pytest.raises(ValidationError):
            TTSSynthesizeRequest(text="测试", speed=3.0)

    def test_empty_text_rejected(self):
        """测试空文本被拒绝"""
        with pytest.raises(ValidationError):
            TTSSynthesizeRequest(text="")

    def test_long_text_accepted(self):
        """测试长文本被接受"""
        long_text = "a" * 5000
        request = TTSSynthesizeRequest(text=long_text)
        assert len(request.text) == 5000


class TestResponseModels:
    """响应模型测试"""

    def test_asr_result_success(self):
        """测试成功的 ASR 结果"""
        result = ASRResult(
            success=True,
            text="测试文本",
            model="paraformer-zh",
            confidence=0.95
        )
        assert result.success is True
        assert result.text == "测试文本"

    def test_asr_result_error(self):
        """测试错误的 ASR 结果"""
        result = ASRResult(
            success=False,
            model="paraformer-zh",
            error="引擎加载失败"
        )
        assert result.success is False
        assert result.error == "引擎加载失败"

    def test_tts_result(self):
        """测试 TTS 结果"""
        result = TTSResult(
            success=True,
            audio_url="/v1/tts/audio/123.wav",
            model="vits-zh-hf-fanchen-C",
            voice_id=77
        )
        assert result.success is True
        assert result.voice_id == 77

    def test_voice_info(self):
        """测试音色信息"""
        voice = VoiceInfo(
            id=77,
            name="沉稳 温暖",
            model="vits-zh-hf-fanchen-C",
            gender="female",
            moods=["warm", "calm"],
            language="zh"
        )
        assert voice.id == 77
        assert "warm" in voice.moods

    def test_model_info(self):
        """测试模型信息"""
        model = ModelInfo(
            id="paraformer-zh",
            name="中文通用模型",
            type="funasr",
            status="available",
            capabilities={"streaming": False},
            default=True
        )
        assert model.default is True

    def test_service_status(self):
        """测试服务状态"""
        status = ServiceStatus(
            status="healthy",
            version="2.0.0",
            uptime_seconds=3600,
            loaded_models={"asr": [], "tts": []}
        )
        assert status.status == "healthy"
        assert status.uptime_seconds == 3600

    def test_health_response(self):
        """测试健康响应"""
        health = HealthResponse(
            status="healthy",
            version="2.0.0"
        )
        assert health.status == "healthy"
        assert health.timestamp is not None
        assert health.version == "2.0.0"
