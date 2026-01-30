"""API Routes Package"""

from .asr import router as asr_router
from .tts import router as tts_router
from .admin import router as admin_router
from .docs import router as docs_router
from .speaker import router as speaker_router

__all__ = [
    "asr_router",
    "tts_router",
    "admin_router",
    "docs_router",
    "speaker_router",
]
