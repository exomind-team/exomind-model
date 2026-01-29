"""
FunASR Local ASR Client
=======================

FunASR 本地语音识别引擎实现。

使用阿里达摩院 FunASR 库进行本地语音转写。
支持说话人分离（Speaker Diarization）功能。
支持 SenseVoiceSmall 高精度多语言模型。
"""

import re
from typing import Optional, List

from .base import ASRClient
from .result import ASRResult, SpeakerSegment


class FunASRClient(ASRClient):
    """FunASR 本地 ASR 引擎"""

    # 支持的模型列表（用户友好名称）
    SUPPORTED_MODELS = {
        'paraformer-zh': '中文通用模型（默认）',
        'sensevoice': '高精度中文模型',
        'paraformer-en': '英文模型',
        'telephone': '电话语音模型',
    }

    # 模型名称到 ModelScope repo_id 的映射 (FunASR 1.3.1 简化格式)
    MODEL_REPO_MAP = {
        'paraformer-zh': 'paraformer-zh',
        'sensevoice': 'SenseVoiceSmall',  # FunASR 1.3.1 简化格式
        'paraformer-en': 'paraformer-en',
        'telephone': 'paraformer-zh',
    }

    def __init__(self, model: str = 'paraformer-zh', device: str = 'cpu', enable_diarization: bool = False):
        """
        初始化 FunASR 客户端

        Args:
            model: 模型名称（默认 paraformer-zh）
            device: 计算设备（默认 cpu）
            enable_diarization: 是否启用说话人分离（默认 False）
        """
        self._model_name = model
        self._device = device
        self._enable_diarization = enable_diarization
        self._model_instance = None
        self._load_model()

    def _load_model(self):
        """加载 FunASR 模型 (FunASR 1.3.1)"""
        try:
            from funasr import AutoModel
            # 获取实际的 ModelScope repo_id
            repo_id = self.MODEL_REPO_MAP.get(self._model_name, self._model_name)
            print(f"🔄 加载 FunASR 模型: {self._model_name} ({repo_id})")

            # 构建模型参数 (FunASR 1.3.1 简化格式)
            model_kwargs = {
                'model': repo_id,
            }

            # SenseVoice 需要启用 VAD 和 PUNC
            if self._model_name == 'sensevoice':
                model_kwargs['vad_model'] = "fsmn-vad"
                model_kwargs['punc_model'] = "ct-punc-c"

            # 启用说话人分离
            if self._enable_diarization:
                # 检查模型是否支持说话人分离
                supports_diar = self._model_name in ['paraformer-zh', 'paraformer-en', 'telephone']
                if not supports_diar:
                    print(f"⚠️  模型 {self._model_name} 不支持说话人分离，已禁用")
                    self._enable_diarization = False
                else:
                    # 必须启用 VAD 和 PUNC 才能说话人分离
                    model_kwargs['vad_model'] = "fsmn-vad"
                    model_kwargs['punc_model'] = "ct-punc-c"  # 正确的模型名称
                    model_kwargs['spk_model'] = "cam++"
                    print(f"🔊 说话人分离已启用 (cam++)")

            self._model_instance = AutoModel(**model_kwargs)
            print(f"✅ 模型加载成功")
        except ImportError:
            raise RuntimeError(
                "FunASR 未安装，请运行: pip install funasr\n"
                "或: uv pip install funasr"
            )
        except Exception as e:
            raise RuntimeError(f"FunASR 模型加载失败: {e}")

    @staticmethod
    def _clean_sensevoice_output(text: str) -> str:
        """
        清理 SenseVoice 输出文本

        SenseVoice 输出格式示例:
        <|zh|><|NEUTRAL|><|Speech|><|woitn|><|wav|><|nes|><|5.89|><|0.0|>这是识别文本。

        Args:
            text: 原始输出

        Returns:
            清理后的纯文本
        """
        # 移除所有 <|xxx|> 格式的标签
        text = re.sub(r'<\|[^|]+\|>', '', text)
        # 移除多余空白（换行、制表符等）
        text = re.sub(r'\s+', ' ', text)
        # 去除首尾空白
        return text.strip()

    @property
    def name(self) -> str:
        return f"FunASR ({self._model_name})"

    @property
    def is_available(self) -> bool:
        return self._model_instance is not None

    def transcribe(self, audio_path: str) -> str:
        """
        转写音频文件

        Args:
            audio_path: 音频文件路径

        Returns:
            识别后的文本
        """
        if not self._model_instance:
            raise RuntimeError("FunASR 模型未加载")

        result = self._model_instance.generate(audio_path)

        # 处理结果
        if not result:
            return ""

        # FunASR 说话人分离可能返回多种格式
        if isinstance(result, list) and len(result) > 0:
            first_result = result[0]

            # 说话人分离结果在 'text' 字段中（包含 [spk0]: 标签）
            if 'text' in first_result:
                text = first_result['text']
            else:
                # 其他格式，尝试拼接
                text = ""
                for r in result:
                    if isinstance(r, dict) and 'text' in r:
                        text += r['text']
        else:
            text = str(result)

        # SenseVoice 输出需要清理特殊标记
        if self._model_name == 'sensevoice':
            text = self._clean_sensevoice_output(text)

        return text
    
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
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data.astype('int16').tobytes())
        
        try:
            return self.transcribe(temp_path)
        finally:
            os.unlink(temp_path)

    def recognize(
        self,
        audio_path: str,
        enable_diarization: Optional[bool] = None,
        num_speakers: Optional[int] = None,
    ) -> ASRResult:
        """
        识别音频（支持说话人分离）

        Args:
            audio_path: 音频文件路径
            enable_diarization: 是否启用说话人分离（覆盖 __init__ 设置）
            num_speakers: 预期说话人数（仅 diarization 模式有效）

        Returns:
            ASRResult: 包含文本、说话人片段、置信度等
        """
        if not self._model_instance:
            raise RuntimeError("FunASR 模型未加载")

        # 确定是否启用说话人分离
        use_diarization = self._enable_diarization
        if enable_diarization is not None:
            use_diarization = enable_diarization

        # 调用 FunASR
        result = self._model_instance.generate(
            audio_path,
            batch_size_s=300,
            num_spks=num_speakers if num_speakers and use_diarization else 2,
        )

        # 解析结果
        return self._parse_result(result, use_diarization)

    def _parse_result(self, result, use_diarization: bool) -> ASRResult:
        """解析 FunASR 返回的结果"""
        if not result:
            return ASRResult(text="", confidence=0.0)

        raw = result[0] if isinstance(result, list) and len(result) > 0 else result
        if not isinstance(raw, dict):
            return ASRResult(text=str(result), confidence=0.0)

        # 基础文本
        text = raw.get("text", "")

        # SenseVoice 输出需要清理特殊标记
        if self._model_name == 'sensevoice':
            text = self._clean_sensevoice_output(text)

        # 说话人分离结果
        speaker_segments: List[SpeakerSegment] = []
        num_speakers: Optional[int] = None

        if use_diarization:
            spk_info = raw.get("spk", [])
            timestamps = raw.get("timestamp", [])
            word_ts = raw.get("timestamp_wed", [])

            # 收集唯一说话人
            unique_speakers = set()
            for spk in spk_info:
                if isinstance(spk, (int, float)):
                    unique_speakers.add(int(spk))
            num_speakers = len(unique_speakers) if unique_speakers else None

            # 构建说话人片段
            for i, (ts, spk) in enumerate(zip(timestamps, spk_info)):
                speaker_id = f"S{int(spk) + 1:02d}" if isinstance(spk, (int, float)) else str(spk)

                # 尝试从 word_timestamp 获取该片段的文本
                segment_text = ""
                if i < len(word_ts) and isinstance(word_ts[i], list):
                    # word_ts[i] 是词级别时间戳列表 [word, start_ms, end_ms, ...]
                    words = []
                    for w in word_ts[i]:
                        if isinstance(w, list) and len(w) > 2:
                            word = w[2] if isinstance(w[2], str) else ""
                            if word:
                                words.append(word)
                    segment_text = "".join(words)

                speaker_segments.append(SpeakerSegment(
                    speaker_id=speaker_id,
                    text=segment_text,
                    start_time=ts[0] / 1000.0,  # 毫秒 → 秒
                    end_time=ts[1] / 1000.0,
                    confidence=0.9,
                ))

        return ASRResult(
            text=text,
            confidence=0.95,  # FunASR 默认真实置信度
            speaker_segments=speaker_segments,
            num_speakers=num_speakers,
        )
