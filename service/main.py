"""
Voice-ime Service Main
======================

FastAPI 服务入口。

提供 ASR/TTS HTTP API 服务，端口 1921。
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime

from service.config import settings
from service.api import asr_router, tts_router, admin_router, docs_router, speaker_router, engine_router
from service.models.response import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """服务生命周期管理"""
    # 启动时
    print(f"🚀 Voice-ime Service 启动中...")
    print(f"   端口: {settings.port}")
    print(f"   文档: http://localhost:{settings.port}/docs")
    yield
    # 关闭时
    print("👋 Voice-ime Service 已关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.title,
    description=settings.description,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(asr_router)
app.include_router(tts_router)
app.include_router(admin_router)
app.include_router(docs_router)
app.include_router(speaker_router)
app.include_router(engine_router)


@app.get("/", tags=["Root"])
async def root():
    """服务根路径"""
    return {
        "service": "Voice-ime",
        "version": settings.version,
        "docs": f"http://localhost:{settings.port}/docs",
        "agent_docs": f"http://localhost:{settings.port}/v1/docs/agent",
        "health": f"http://localhost:{settings.port}/health"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=settings.version
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
