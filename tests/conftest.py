"""
Test Configuration
==================

测试夹具和配置。
"""

import asyncio
import sys
from pathlib import Path

# 动态添加项目根目录到 sys.path（确保在 tests 目录之前）
FILE = Path(__file__).resolve()
ROOT = FILE.parents[2] / "voice-ime"

# 将 ROOT 放到 sys.path 最前面，覆盖 pytest 添加的 tests 目录
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))

import pytest
from httpx import AsyncClient, ASGITransport
from service.main import app


@pytest.fixture(scope="session")
def event_loop():
    """为异步 fixture 创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def client():
    """测试客户端 fixture"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sample_audio_bytes():
    """模拟音频字节"""
    return b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
