"""
Speaker API Endpoints
=====================

说话人分离 API 端点。

提供：
- 说话人分离（Diarization）
- 声纹注册
- 声纹验证
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import time
import tempfile
import wave
import os

from service.models.response import SpeakerDiarizeResult, SpeakerDiarizeSegment
from speaker.factory import SpeakerClientFactory

router = APIRouter(prefix="/v1/speaker", tags=["Speaker"])


@router.post("/diarize", response_model=SpeakerDiarizeResult)
async def diarize(
    audio: UploadFile = File(...),
    engine: str = Form("cam++"),
    num_speakers: Optional[int] = Form(None)
):
    """
    说话人分离 - 识别音频中的不同说话人

    - **audio**: 音频文件 (wav, mp3, m4a)
    - **engine**: 说话人分离引擎 ("cam++", "mock")
    - **num_speakers**: 说话人数（可选，自动检测）
    """
    start_time = time.time()

    # 验证文件类型
    allowed_types = ["audio/wav", "audio/mp3", "audio/m4a", "audio/x-m4a", "audio/x-wav"]
    content_type = audio.content_type or ""

    if content_type not in allowed_types and not any(
        audio.filename.endswith(ext) for ext in [".wav", ".mp3", ".m4a"]
    ):
        raise HTTPException(
            status_code=400,
            detail=f"不支持的音频格式。支持: wav, mp3, m4a。当前: {audio.filename}"
        )

    # 验证引擎可用性
    if not SpeakerClientFactory.is_available(engine):
        raise HTTPException(
            status_code=400,
            detail=f"说话人分离引擎 '{engine}' 不可用。请选择: {SpeakerClientFactory.available_engines()}"
        )

    try:
        # 读取音频数据
        audio_data = await audio.read()

        # 保存为临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name

        try:
            # 写入 WAV 数据（统一为 16kHz 单声道）
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data)

            # 创建 Speaker 客户端并执行分离
            speaker_client = SpeakerClientFactory.create(engine=engine)

            # 执行说话人分离
            segments = speaker_client.diarize(temp_path, num_speakers=num_speakers)

            processing_time_ms = int((time.time() - start_time) * 1000)

            # 获取唯一说话人数量
            speaker_ids = set()
            for seg in segments:
                speaker_ids.add(seg.speaker_id)

            return SpeakerDiarizeResult(
                success=True,
                audio_path=temp_path,
                engine=engine,
                num_speakers=len(speaker_ids),
                segments=[
                    SpeakerDiarizeSegment(
                        speaker_id=seg.speaker_id,
                        start_time=seg.start_time,
                        end_time=seg.end_time,
                        confidence=seg.confidence
                    )
                    for seg in segments
                ],
                processing_time_ms=processing_time_ms,
                metadata={
                    "engine": engine,
                    "audio_filename": audio.filename,
                    "num_segments": len(segments)
                }
            )

        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"说话人分离失败: {str(e)}"
        )


@router.get("/engines")
async def list_engines():
    """
    列出可用的说话人分离引擎

    返回所有已注册的说话人分离引擎及其状态。
    """
    engines = SpeakerClientFactory.available_engines()
    return {
        "engines": [
            {
                "name": name,
                "available": SpeakerClientFactory.is_available(name),
                **SpeakerClientFactory.get_engine_info(name)
            }
            for name in engines
        ]
    }


@router.get("/health/{engine}")
async def check_engine_health(engine: str):
    """
    检查说话人分离引擎健康状态

    - **engine**: 引擎名称
    """
    if not SpeakerClientFactory.is_available(engine):
        return {
            "engine": engine,
            "status": "unavailable",
            "message": f"引擎 '{engine}' 不可用或依赖未安装"
        }

    try:
        client = SpeakerClientFactory.create(engine)
        return {
            "engine": engine,
            "status": "healthy",
            "name": client.name,
            "embedding_dim": client.embedding_dim
        }
    except Exception as e:
        return {
            "engine": engine,
            "status": "error",
            "message": str(e)
        }
