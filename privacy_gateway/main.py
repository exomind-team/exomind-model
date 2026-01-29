"""
Privacy Gateway Main Module
============================

隐私网关 FastAPI 应用入口
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as privacy_router
from .config import settings


def create_app() -> FastAPI:
    """创建 FastAPI 应用"""
    app = FastAPI(
        title="Privacy Gateway",
        description="隐私保护中转网关 - MVP 版本",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc"
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
    app.include_router(privacy_router)

    # 根路径
    @app.get("/")
    async def root():
        return {
            "service": "Privacy Gateway",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs"
        }

    return app


# 创建应用实例
app = create_app()


def run():
    """运行服务（用于命令行启动）"""
    import uvicorn
    uvicorn.run(
        "privacy_gateway.main:app",
        host="0.0.0.0",
        port=1922,
        reload=False
    )


if __name__ == "__main__":
    run()
