"""
API Request Models
==================

Pydantic 请求数据模型。
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ASRModel(str, Enum):
    """ASR 模型选择"""
    PARAFORMER_ZH = "paraformer-zh"
    NANO_2512 = "nano-2512"
    SENSEVOICE = "sensevoice"
    MOSS = "moss"


class TTSModel(str, Enum):
    """TTS 模型选择"""
    VITS_ZH_FANCHEN_C = "vits-zh-hf-fanchen-C"
    KOKORO_MULTI = "kokoro-multi-lang-v1_1"


class AudioFormat(str, Enum):
    """音频格式"""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"


class ASRTranscribeRequest(BaseModel):
    """ASR 转写请求"""
    model: ASRModel = ASRModel.PARAFORMER_ZH
    enable_diarization: bool = False
    language: str = "zh"
    response_format: str = "json"

    class Config:
        json_schema_extra = {
            "example": {
                "model": "paraformer-zh",
                "enable_diarization": False,
                "language": "zh",
                "response_format": "json"
            }
        }


class TTSSynthesizeRequest(BaseModel):
    """TTS 合成请求"""
    text: str = Field(..., min_length=1, max_length=5000)
    model: TTSModel = TTSModel.VITS_ZH_FANCHEN_C
    voice_id: int = 77
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    volume_db: float = Field(default=25.0, ge=-60.0, le=60.0)
    format: AudioFormat = AudioFormat.WAV
    sample_rate: int = Field(default=44100, ge=8000, le=96000)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "你好，这是语音合成的测试",
                "model": "vits-zh-hf-fanchen-C",
                "voice_id": 77,
                "speed": 1.0,
                "volume_db": 25.0,
                "format": "wav",
                "sample_rate": 44100
            }
        }


class VoiceFilterRequest(BaseModel):
    """音色筛选请求"""
    model: Optional[TTSModel] = None
    gender: Optional[str] = None
    mood: Optional[str] = None
    language: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class SpeakerEngine(str, Enum):
    """说话人分离引擎选择"""
    CAMPLUS = "cam++"
    MOCK = "mock"


class SpeakerDiarizeRequest(BaseModel):
    """说话人分离请求"""
    engine: SpeakerEngine = SpeakerEngine.CAMPLUS
    num_speakers: Optional[int] = Field(default=None, ge=1, le=20)

    class Config:
        json_schema_extra = {
            "example": {
                "engine": "cam++",
                "num_speakers": 2
            }
        }
