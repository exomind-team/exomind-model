"""
ASR Client Abstract Base Class
=============================

语音识别引擎抽象基类。

定义了所有 ASR 引擎必须实现的接口，
确保不同引擎可以无缝切换。
"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator
from .result import StreamingResult, StreamingState


class ASRClient(ABC):
    """ASR 引擎抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """引擎是否可用"""
        pass

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """
        转写音频文件为文本

        Args:
            audio_path: 音频文件路径 (WAV)

        Returns:
            识别后的文本
        """
        pass

    @abstractmethod
    def transcribe_audio_data(self, audio_data) -> str:
        """
        转写音频数据为文本

        Args:
            audio_data: numpy 音频数组

        Returns:
            识别后的文本
        """
        pass

    # ========== 流式识别方法 ==========

    async def transcribe_streaming(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[StreamingResult, None]:
        """流式转写（实时模式）

        Args:
            audio_chunks: 音频数据异步生成器

        Yields:
            StreamingResult: 识别结果
        """
        # 默认实现：迭代音频块并调用 transcribe_chunk
        async for chunk in audio_chunks:
            yield self.transcribe_chunk(chunk)

    def transcribe_chunk(self, chunk: bytes) -> StreamingResult:
        """单次流式转写（简单模式）

        Args:
            chunk: 音频片段（bytes）

        Returns:
            StreamingResult: 识别结果
        """
        # 子类可以覆盖此方法以提供更高效的流式实现
        text = self._transcribe_chunk_simple(chunk)
        return StreamingResult(
            text=text,
            state=StreamingState.INTERMEDIATE,
            is_final=True,
            confidence=1.0,
        )

    def _transcribe_chunk_simple(self, chunk: bytes) -> str:
        """简单的单块转写（保存临时文件）

        Args:
            chunk: 音频片段（bytes）

        Returns:
            识别文本
        """
        import tempfile
        import wave
        import os
        import numpy as np

        # 保存为临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name

        try:
            # 写入 WAV (假设 16kHz, 16bit, mono)
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                # 将 bytes 转换为 int16 数组
                audio_data = np.frombuffer(chunk, dtype=np.int16)
                wf.writeframes(audio_data.tobytes())

            return self.transcribe(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
