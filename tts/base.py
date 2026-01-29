"""TTS 抽象基类定义"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import numpy as np


@dataclass
class TTSResult:
    """TTS 生成结果

    Attributes:
        audio: 音频数据 (float32, 范围 -1.0 ~ 1.0)
        sample_rate: 采样率 (Hz)
        duration: 音频时长（秒）
        text: 原始输入文本
        speaker_id: 说话人 ID（如果有）
    """
    audio: np.ndarray
    sample_rate: int
    duration: float
    text: str
    speaker_id: Optional[int] = None

    def save(self, filepath: str):
        """保存音频到文件

        Args:
            filepath: 输出文件路径
        """
        import sherpa_onnx
        sherpa_onnx.write_wave(
            filepath,
            self.audio,
            self.sample_rate
        )


class TTSClient(ABC):
    """TTS 客户端抽象基类

    定义统一的 TTS 接口，支持:
    - 文本转语音生成
    - 多说话人支持
    - 语速调节
    - 音量调节
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """返回引擎名称

        Returns:
            引擎标识符，如 'sherpa-vits', 'sherpa-kokoro'
        """
        pass

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """返回输出音频采样率

        Returns:
            采样率 (Hz)，如 16000, 24000
        """
        pass

    @property
    @abstractmethod
    def num_speakers(self) -> Optional[int]:
        """返回支持的说话人数量

        Returns:
            说话人数量，None 表示不支持多说话人
        """
        pass

    @abstractmethod
    def generate(
        self,
        text: str,
        speaker_id: Optional[int] = None,
        speed: float = 1.0,
        volume_db: Optional[float] = None,
        **kwargs
    ) -> TTSResult:
        """生成语音

        Args:
            text: 要转换的文本
            speaker_id: 说话人 ID（如果支持多说话人）
            speed: 语速 (0.5 - 2.0)，1.0 为正常速度
            volume_db: 音量增益 (dB)，None 使用默认值
            **kwargs: 额外参数

        Returns:
            TTSResult: 生成结果

        Raises:
            RuntimeError: 引擎未初始化
            ValueError: 无效的参数值
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用

        Returns:
            True 表示引擎已初始化且可正常使用
        """
        pass

    @abstractmethod
    def close(self):
        """释放资源

        关闭引擎，释放内存和其他资源。
        """
        pass

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，自动释放资源"""
        self.close()
        return False

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
