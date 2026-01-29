"""
Admin API Endpoints
===================

管理 API 端点。
"""

from fastapi import APIRouter
from datetime import datetime
from service.models.response import ServiceStatus, HealthResponse

router = APIRouter(prefix="/v1/admin", tags=["Admin"])

# 服务启动时间
_start_time = datetime.utcnow()


@router.get("/status", response_model=ServiceStatus)
async def get_status():
    """
    获取服务状态

    返回服务运行状态、资源使用情况、已加载模型等信息。
    """
    import psutil
    import os

    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()

    # 获取已加载模型
    loaded_models = {
        "asr": ["paraformer-zh", "nano-2512"],  # TODO: 实际检测
        "tts": ["vits-zh-hf-fanchen-C"]
    }

    uptime = (datetime.utcnow() - _start_time).total_seconds()

    return ServiceStatus(
        status="healthy",
        version="2.0.0",
        uptime_seconds=int(uptime),
        memory_usage_mb=memory_info.rss / (1024 * 1024),
        cpu_usage_percent=psutil.cpu_percent(),
        loaded_models=loaded_models,
        request_stats={
            "total_requests": 0,
            "asr_requests": 0,
            "tts_requests": 0,
            "avg_response_time_ms": 0,
            "error_rate_percent": 0.0
        }
    )
