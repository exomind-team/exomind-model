"""Speaker 基类模块

定义声纹识别的抽象基类和 数据结构。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List, Tuple
import time
import numpy as np


@dataclass
class SpeakerEmbedding:
    """说话人声纹特征

    Attributes:
        speaker_id: 说话人唯一标识
        embedding: 声纹向量
        name: 说话人名称（可选）
        audio_path: 参考音频路径（可选）
        created_at: 创建时间戳
        sample_rate: 音频采样率
    """
    speaker_id: str
    embedding: np.ndarray
    name: Optional[str] = None
    audio_path: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    sample_rate: int = 16000

    def save(self, directory: str) -> str:
        """保存声纹到文件

        Args:
            directory: 保存目录

        Returns:
            保存的文件路径
        """
        import json
        import os

        Path(directory).mkdir(parents=True, exist_ok=True)

        # 保存 embedding
        embedding_path = os.path.join(directory, f"{self.speaker_id}.npy")
        np.save(embedding_path, self.embedding)

        # 保存元数据
        meta = {
            "speaker_id": self.speaker_id,
            "name": self.name,
            "audio_path": self.audio_path,
            "created_at": self.created_at,
            "sample_rate": self.sample_rate,
            "embedding_dim": len(self.embedding),
        }
        meta_path = os.path.join(directory, f"{self.speaker_id}.json")
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        return embedding_path

    @classmethod
    def load(cls, speaker_id: str, directory: str) -> "SpeakerEmbedding":
        """从文件加载声纹

        Args:
            speaker_id: 说话人 ID
            directory: 加载目录

        Returns:
            SpeakerEmbedding 实例
        """
        import json
        import os

        # 加载 embedding
        embedding_path = os.path.join(directory, f"{speaker_id}.npy")
        embedding = np.load(embedding_path)

        # 加载元数据
        meta_path = os.path.join(directory, f"{speaker_id}.json")
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)

        return cls(
            speaker_id=speaker_id,
            embedding=embedding,
            name=meta.get("name"),
            audio_path=meta.get("audio_path"),
            created_at=meta.get("created_at", time.time()),
            sample_rate=meta.get("sample_rate", 16000),
        )


@dataclass
class SpeakerVerificationResult:
    """声纹验证结果

    Attributes:
        is_verified: 是否验证通过
        confidence: 置信度 (0.0 ~ 1.0)
        threshold: 使用的阈值
        embedding: 提取的声纹向量（可选）
    """
    is_verified: bool
    confidence: float
    threshold: float
    embedding: Optional[np.ndarray] = None


@dataclass
class SpeakerSegment:
    """说话人片段

    Attributes:
        speaker_id: 说话人 ID
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        confidence: 置信度
    """
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float


class SpeakerClient(ABC):
    """声纹客户端抽象基类

    所有声纹识别引擎实现都需要继承此类。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        ...

    @property
    @abstractmethod
    def embedding_dim(self) -> int:
        """声纹向量维度"""
        ...

    @abstractmethod
    def extract_embedding(self, audio_path: str) -> np.ndarray:
        """从音频提取声纹向量

        Args:
            audio_path: 音频文件路径

        Returns:
            声纹向量
        """
        ...

    @abstractmethod
    def verify(
        self,
        audio_path: str,
        embedding: np.ndarray,
        threshold: float = 0.5,
    ) -> SpeakerVerificationResult:
        """验证声纹

        Args:
            audio_path: 待验证音频路径
            embedding: 参考声纹向量
            threshold: 验证阈值

        Returns:
            验证结果
        """
        ...

    @abstractmethod
    def diarize(
        self,
        audio_path: str,
        num_speakers: Optional[int] = None,
    ) -> List[SpeakerSegment]:
        """说话人分离

        Args:
            audio_path: 音频文件路径
            num_speakers: 说话人数（可选）

        Returns:
            说话人片段列表
        """
        ...

    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r})"

    def __enter__(self) -> "SpeakerClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        """释放资源（可选实现）"""
        pass
