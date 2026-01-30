"""
API Response Models
===================

Pydantic 响应数据模型。
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone


class SpeakerSegment(BaseModel):
    """说话人片段"""
    speaker_id: str
    text: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    confidence: float = 1.0


class ASRResult(BaseModel):
    """ASR 转写结果"""
    success: bool
    text: Optional[str] = None
    model: str
    confidence: Optional[float] = None
    duration_seconds: Optional[float] = None
    processing_time_ms: Optional[int] = None
    language: str = "zh"
    format: str = "json"
    segments: Optional[List[dict]] = None
    # 说话人分离字段
    speaker_segments: Optional[List[SpeakerSegment]] = None
    num_speakers: Optional[int] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None


class TTSResult(BaseModel):
    """TTS 合成结果"""
    success: bool
    audio_url: Optional[str] = None
    model: str
    voice_id: int
    voice_name: Optional[str] = None
    duration_seconds: Optional[float] = None
    processing_time_ms: Optional[int] = None
    audio_data: Optional[bytes] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None


class VoiceInfo(BaseModel):
    """音色信息"""
    id: int
    name: str
    model: str
    gender: str
    moods: List[str]
    language: str
    sample_url: Optional[str] = None
    performance: Optional[dict] = None
    tags: List[str] = []


class VoiceListResponse(BaseModel):
    """音色列表响应"""
    voices: List[VoiceInfo]
    pagination: dict
    filters_applied: Optional[dict] = None


class ModelInfo(BaseModel):
    """模型信息"""
    id: str
    name: str
    type: str
    status: str
    capabilities: dict
    performance: Optional[dict] = None
    default: bool = False


class ModelListResponse(BaseModel):
    """模型列表响应"""
    models: List[ModelInfo]


class ServiceStatus(BaseModel):
    """服务状态"""
    status: str
    version: str
    uptime_seconds: int
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    loaded_models: dict
    request_stats: Optional[dict] = None


class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str


class SpeakerDiarizeSegment(BaseModel):
    """说话人分离片段"""
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float = 1.0


class SpeakerDiarizeResult(BaseModel):
    """说话人分离结果"""
    success: bool
    audio_path: Optional[str] = None
    engine: str
    num_speakers: int
    segments: List[SpeakerDiarizeSegment]
    processing_time_ms: Optional[int] = None
    metadata: Optional[dict] = None
    error: Optional[str] = None
