"""CAM++ 声纹客户端

使用 FunASR 的 CAM++ 模型实现声纹识别。
"""

from pathlib import Path
from typing import Optional, List, Dict, Any
import os

import numpy as np

from speaker.base import (
    SpeakerClient,
    SpeakerEmbedding,
    SpeakerVerificationResult,
    SpeakerSegment,
)


class CAMPlusClient(SpeakerClient):
    """CAM++ 声纹识别客户端

    基于 FunASR 的 CAM++ 模型实现。
    """

    def __init__(
        self,
        embedding_dir: Optional[str] = None,
        device: str = "cpu",
    ):
        """初始化 CAM++ 客户端

        Args:
            embedding_dir: 声纹存储目录
            device: 设备 ("cpu" 或 "cuda")
        """
        self._embedding_dir = embedding_dir
        self._device = device
        self._model = None

    @property
    def name(self) -> str:
        return "cam++"

    @property
    def embedding_dim(self) -> int:
        return 192

    def _init_engine(self) -> None:
        """初始化 FunASR CAM++ 模型"""
        if self._model is not None:
            return

        try:
            from funasr import AutoModel

            self._model = AutoModel(
                model="paraformer-zh",
                spk_model="cam++",
                spk_model_revision="v2.0.2",
            )
        except ImportError:
            raise ImportError(
                "FunASR not installed. Install with: "
                "pip install funasr modelscope"
            )

    def extract_embedding(self, audio_path: str) -> np.ndarray:
        """从音频提取声纹向量

        Args:
            audio_path: 音频文件路径

        Returns:
            声纹向量 (192维)
        """
        self._init_engine()

        # 使用 FunASR 提取声纹
        # FunASR CAM++ 会返回 spk_embedding
        result = self._model.generate(
            input=audio_path,
            batch_size_s=60,
            return_raw=True,
        )

        # 提取声纹向量
        if isinstance(result, list) and len(result) > 0:
            raw_result = result[0]
            if isinstance(raw_result, dict):
                # 尝试获取声纹
                if "spk_embedding" in raw_result:
                    embedding = np.array(raw_result["spk_embedding"], dtype=np.float32)
                    return embedding

        # 如果没有返回声纹，抛出异常
        raise RuntimeError(f"Failed to extract embedding from {audio_path}")

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
        # 提取待验证音频的声纹
        test_embedding = self.extract_embedding(audio_path)

        # 计算余弦相似度
        similarity = self._cosine_similarity(test_embedding, embedding)

        return SpeakerVerificationResult(
            is_verified=similarity >= threshold,
            confidence=similarity,
            threshold=threshold,
            embedding=test_embedding,
        )

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
        self._init_engine()

        # 使用 FunASR + CAM++ 进行分离
        result = self._model.generate(
            input=audio_path,
            batch_size_s=300,
            num_spks=num_speakers if num_speakers else 2,
        )

        segments = []
        if isinstance(result, list) and len(result) > 0:
            raw_result = result[0]
            if isinstance(raw_result, dict):
                # 解析说话人信息
                timestamp = raw_result.get("timestamp", [])
                spk_info = raw_result.get("spk", [])

                for i, (ts, spk) in enumerate(zip(timestamp, spk_info)):
                    segments.append(SpeakerSegment(
                        speaker_id=f"S{int(spk) + 1:02d}" if isinstance(spk, (int, float)) else str(spk),
                        start_time=ts[0] / 1000,  # 转换为秒
                        end_time=ts[1] / 1000,
                        confidence=0.9,
                    ))

        return segments

    def is_available(self) -> bool:
        """检查引擎是否可用"""
        try:
            self._init_engine()
            return True
        except Exception:
            return False

    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """计算余弦相似度"""
        a = a / (np.linalg.norm(a) + 1e-8)
        b = b / (np.linalg.norm(b) + 1e-8)
        return float(np.dot(a, b))

    @staticmethod
    def check_dependencies() -> bool:
        """检查依赖是否满足"""
        try:
            import funasr
            return True
        except (ImportError, OSError):
            return False

    def close(self) -> None:
        """释放资源"""
        self._model = None
