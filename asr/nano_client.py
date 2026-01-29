"""
Fun-ASR-Nano-2512 Client
========================

Fun-ASR-Nano-2512 实时语音识别引擎实现。

使用阿里通义 Fun-ASR-Nano-2512 模型，支持：
- 低延迟实时转写（<600ms）
- 31 种语言识别
- 7 种中文方言 + 26 种口音
- 流式音频处理
"""

import time
from typing import AsyncGenerator, Dict, Any, Optional

from .base import ASRClient
from .result import StreamingResult, StreamingState


class FunASRNanoClient(ASRClient):
    """
    Fun-ASR-Nano-2512 实时 ASR 引擎客户端

    特点：
    - 原生流式支持，延迟 < 600ms
    - 31 种语言，7 种中文方言
    - 推理速度 ≥1x 实时率
    - 显存占用 < 4GB
    """

    # 支持的模型
    SUPPORTED_MODELS = {
        'nano-2512': 'Fun-ASR-Nano-2512 (多语言，31种语言)',
        'nano-mlt': 'Fun-ASR-MLT-Nano-2512 (多语言增强版)',
    }

    # 模型仓库映射
    MODEL_REPO_MAP = {
        'nano-2512': 'FunAudioLLM/Fun-ASR-Nano-2512',
        'nano-mlt': 'FunAudioLLM/Fun-ASR-MLT-Nano-2512',
    }

    def __init__(self, model: str = 'nano-2512', device: str = 'cpu'):
        """
        初始化 Fun-ASR-Nano-2512 客户端

        Args:
            model: 模型名称 (nano-2512 / nano-mlt)
            device: 计算设备 (cuda / cpu)
        """
        self._model_name = model
        self._device = device
        self._model_instance = None
        self._model_kwargs = None
        self._chunk_start_time = 0.0
        self._load_model()

    def _load_model(self):
        """加载 Fun-ASR-Nano-2512 模型"""
        try:
            from funasr import AutoModel

            repo_id = self.MODEL_REPO_MAP.get(self._model_name, self._model_name)
            print(f"🔄 加载 Fun-ASR-Nano-2512 模型: {repo_id}")
            print(f"   设备: {self._device}")

            # Fun-ASR-Nano-2512 需要使用 trust_remote_code 和 remote_code 参数
            # remote_code 指向仓库中的 model.py
            import os
            model_dir = os.path.dirname(os.path.abspath(__file__))
            remote_code = os.path.join(model_dir, "model.py")

            self._model_instance = AutoModel(
                model=repo_id,
                trust_remote_code=True,
                remote_code=remote_code,
                device=self._device,
                disable_update=True
            )

            # 模型参数字典（用于 inference 调用）
            self._model_kwargs = {}

            print(f"✅ Fun-ASR-Nano-2512 模型加载成功")

        except ImportError as e:
            raise RuntimeError(
                f"Fun-ASR-Nano-2512 依赖未安装: {e}\n"
                "请确保已安装: pip install funasr modelscope\n"
                "或参考: https://github.com/FunAudioLLM/Fun-ASR"
            )
        except Exception as e:
            raise RuntimeError(f"Fun-ASR-Nano-2512 模型加载失败: {e}")

    @property
    def name(self) -> str:
        return f"Fun-ASR-Nano-2512 ({self._model_name})"

    @property
    def is_available(self) -> bool:
        return self._model_instance is not None

    def transcribe(self, audio_path: str) -> str:
        """
        转写音频文件（离线模式）

        Args:
            audio_path: 音频文件路径

        Returns:
            识别后的文本
        """
        if not self._model_instance:
            raise RuntimeError("Fun-ASR-Nano-2512 模型未加载")

        try:
            # 离线转写
            results = self._model_instance.inference(
                [audio_path],
                **self._model_kwargs
            )

            # 提取文本
            if results and len(results) > 0:
                result = results[0]
                if isinstance(result, list) and len(result) > 0:
                    # 格式: [[{"text": "识别文本"}]]
                    return result[0].get('text', '')
                elif isinstance(result, dict):
                    return result.get('text', '')

            return ""

        except Exception as e:
            raise RuntimeError(f"Fun-ASR-Nano-2512 转写失败: {e}")

    def transcribe_chunk(self, chunk: bytes) -> StreamingResult:
        """
        单次流式转写（高效模式）

        Args:
            chunk: 音频片段（bytes）

        Returns:
            StreamingResult: 流式识别结果
        """
        if not self._model_instance:
            raise RuntimeError("Fun-ASR-Nano-2512 模型未加载")

        start_time = time.time()

        try:
            # 流式推理 - 返回第一个结果
            for result in self._model_instance.inference_stream([chunk]):
                # 提取文本
                text = ""
                if result and len(result) > 0:
                    r = result[0]
                    if isinstance(r, list) and len(r) > 0:
                        text = r[0].get('text', '')
                    elif isinstance(r, dict):
                        text = r.get('text', '')

                chunk_duration = time.time() - start_time

                return StreamingResult(
                    text=text,
                    state=StreamingState.INTERMEDIATE,
                    is_final=True,
                    confidence=1.0,
                    start_time=self._chunk_start_time,
                    end_time=self._chunk_start_time + chunk_duration,
                    chunk_duration=chunk_duration,
                )

            # 无结果返回空
            return StreamingResult(text="")

        except Exception as e:
            raise RuntimeError(f"Fun-ASR-Nano-2512 流式转写失败: {e}")

    async def transcribe_streaming(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[StreamingResult, None]:
        """流式转写（实时模式）

        Args:
            audio_chunks: 音频数据异步生成器

        Yields:
            StreamingResult: 流式识别结果
        """
        self._chunk_start_time = 0.0
        chunk_index = 0

        async for chunk in audio_chunks:
            result = self.transcribe_chunk(chunk)

            # 更新开始时间（累计）
            if chunk_index > 0:
                # 假设每个块约 100ms，累积计算时间
                result.start_time = chunk_index * 0.1
                result.end_time = result.start_time + result.chunk_duration

            yield result
            chunk_index += 1

    def start_streaming_session(self):
        """开始流式会话（重置时间戳）"""
        self._chunk_start_time = 0.0

    def end_streaming_session(self) -> StreamingResult:
        """结束流式会话"""
        return StreamingResult(
            text="",
            state=StreamingState.COMPLETED,
            is_final=True,
        )

    def transcribe_audio_data(self, audio_data) -> str:
        """
        转写音频数据（保存为临时文件）

        Args:
            audio_data: numpy 音频数组

        Returns:
            识别后的文本
        """
        import tempfile
        import wave
        import os

        # 保存为临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name

        # 写入 WAV
        try:
            with wave.open(temp_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(audio_data.astype('int16').tobytes())

            return self.transcribe(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def batch_transcribe(self, audio_paths: list) -> list:
        """
        批量转写音频文件

        Args:
            audio_paths: 音频文件路径列表

        Returns:
            识别文本列表
        """
        if not self._model_instance:
            raise RuntimeError("Fun-ASR-Nano-2512 模型未加载")

        try:
            results = self._model_instance.inference(
                audio_paths,
                **self._model_kwargs
            )

            texts = []
            for result in results:
                if isinstance(result, list) and len(result) > 0:
                    texts.append(result[0].get('text', ''))
                elif isinstance(result, dict):
                    texts.append(result.get('text', ''))
                else:
                    texts.append('')

            return texts

        except Exception as e:
            raise RuntimeError(f"Fun-ASR-Nano-2512 批量转写失败: {e}")
