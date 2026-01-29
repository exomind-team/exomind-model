"""Speaker 声纹识别模块

提供说话人注册、声纹验证和说话人分离功能。
"""

from speaker.base import (
    SpeakerClient,
    SpeakerEmbedding,
    SpeakerVerificationResult,
    SpeakerSegment,
)
from speaker.factory import (
    SpeakerClientFactory,
    create_speaker_client,
)

__all__ = [
    "SpeakerClient",
    "SpeakerEmbedding",
    "SpeakerVerificationResult",
    "SpeakerSegment",
    "SpeakerClientFactory",
    "create_speaker_client",
]
