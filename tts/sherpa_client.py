"""Sherpa-ONNX TTS 客户端实现"""

import os
from pathlib import Path
from typing import Optional
import numpy as np

import sherpa_onnx
import torch

from .base import TTSClient, TTSResult


class SherpaTTSClient(TTSClient):
    """Sherpa-ONNX TTS 客户端

    支持以下模型:
    - vits-zh-hf-fanchen-C: 中文 VITS 模型，187 个说话人
    - kokoro-multi-lang-v1_1: 多语言 Kokoro 模型，103 个说话人
    - vits-zh-aishell3: 中文 AISHELL-3 模型，6 个说话人

    Attributes:
        DEFAULT_VOLUME_DB: 默认音量增益 (dB)
        SUPPORTED_MODELS: 支持的模型列表
    """

    DEFAULT_VOLUME_DB = 25.0
    SUPPORTED_MODELS = [
        "vits-zh-hf-fanchen-C",
        "kokoro-multi-lang-v1_1",
        "vits-zh-aishell3",
    ]

    def __init__(
        self,
        model: str = "vits-zh-hf-fanchen-C",
        speaker_id: int = 77,
        volume_db: float = DEFAULT_VOLUME_DB,
        model_dir: Optional[str] = None,
        data_dir: Optional[str] = None,
    ):
        """初始化 Sherpa TTS 客户端

        Args:
            model: 模型名称
            speaker_id: 默认说话人 ID
            volume_db: 音量增益 (dB)，0 表示不调整
            model_dir: 模型目录，默认从 models/ 目录自动查找
            data_dir: 数据目录（Kokoro 需要 espeak-ng-data）

        Raises:
            FileNotFoundError: 模型文件不存在
            ValueError: 不支持的模型
        """
        self._model = model
        self._default_speaker_id = speaker_id
        self._volume_db = volume_db
        self._model_dir = model_dir or self._find_model_dir(model)
        self._data_dir = data_dir

        # Sherpa-ONNX 引擎实例
        self._tts: Optional[sherpa_onnx.OfflineTts] = None

        # 初始化引擎
        self._init_engine()

    def _find_model_dir(self, model: str) -> str:
        """查找模型目录

        Args:
            model: 模型名称

        Returns:
            模型目录路径（包含 .onnx 文件的目录）

        Raises:
            FileNotFoundError: 模型目录不存在
        """
        # 在多个可能的位置查找
        search_paths = [
            Path("models") / model,
            Path("/home/hailay/ExoMind-Obsidian-HailayLin/1-Projects/exomind-model/models") / model,
            Path(f"models/{model}"),
        ]

        for base_path in search_paths:
            if base_path.exists() and base_path.is_dir():
                # 检查是否有嵌套的同名子目录
                nested = base_path / model
                if nested.exists() and nested.is_dir():
                    return str(nested)
                # 直接返回基目录
                return str(base_path)

        # 模糊匹配
        models_base = Path("models")
        if models_base.exists():
            for entry in models_base.iterdir():
                if entry.is_dir() and model.lower() in entry.name.lower():
                    # 检查是否有嵌套的同名子目录
                    nested = entry / model
                    if nested.exists() and nested.is_dir():
                        return str(nested)
                    return str(entry)

        raise FileNotFoundError(
            f"Model not found: {model}. "
            f"Searched in: {[str(p) for p in search_paths]}"
        )

    def _init_engine(self):
        """初始化 TTS 引擎"""
        if self._model == "vits-zh-hf-fanchen-C":
            self._init_vits()
        elif self._model == "vits-zh-aishell3":
            self._init_vits()
        elif self._model == "kokoro-multi-lang-v1_1":
            self._init_kokoro()
        else:
            raise ValueError(
                f"Unsupported model: {self._model}. "
                f"Supported: {self.SUPPORTED_MODELS}"
            )

    def _init_vits(self):
        """初始化 VITS 引擎"""
        model_path = os.path.join(self._model_dir, f"{self._model}.onnx")
        tokens_path = os.path.join(self._model_dir, "tokens.txt")
        lexicon_path = os.path.join(self._model_dir, "lexicon.txt")

        # 检查必要文件
        for path in [model_path, tokens_path]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"Required file not found: {path}")

        model_config = sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=model_path,
                tokens=tokens_path,
                lexicon=lexicon_path,
            ),
        )
        config = sherpa_onnx.OfflineTtsConfig(model=model_config)
        self._tts = sherpa_onnx.OfflineTts(config)

    def _init_kokoro(self):
        """初始化 Kokoro 引擎"""
        model_path = os.path.join(self._model_dir, f"{self._model}.onnx")
        tokens_path = os.path.join(self._model_dir, "tokens.txt")

        # Kokoro 需要 espeak-ng-data 目录
        if self._data_dir is None:
            # 尝试自动查找
            possible_data_dirs = [
                Path(self._model_dir) / "espeak-ng-data",
                Path("/usr/share/espeak-ng-data"),
                Path("/home/hailay/ExoMind-Obsidian-HailayLin/1-Projects/exomind-model/models/kokoro-multi-lang-v1_1/espeak-ng-data"),
            ]
            for d in possible_data_dirs:
                if d.exists():
                    self._data_dir = str(d)
                    break

            if self._data_dir is None:
                raise ValueError(
                    "Kokoro requires espeak-ng-data directory. "
                    "Please specify data_dir parameter."
                )

        model_config = sherpa_onnx.OfflineTtsModelConfig(
            kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                model=model_path,
                tokens=tokens_path,
                data_dir=self._data_dir,
            ),
        )
        config = sherpa_onnx.OfflineTtsConfig(model=model_config)
        self._tts = sherpa_onnx.OfflineTts(config)

    @property
    def name(self) -> str:
        return f"sherpa-{self._model}"

    @property
    def sample_rate(self) -> int:
        return self._tts.sample_rate if self._tts else 16000

    @property
    def num_speakers(self) -> Optional[int]:
        return self._tts.num_speakers if self._tts else None

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
            text: 输入文本
            speaker_id: 说话人 ID
            speed: 语速 (0.5 - 2.0)
            volume_db: 音量增益 (dB)，覆盖默认设置
            **kwargs: 额外参数

        Returns:
            TTSResult: 生成结果

        Raises:
            RuntimeError: 引擎未初始化
            ValueError: 无效的说话人 ID
        """
        if not self._tts:
            raise RuntimeError("TTS engine not initialized")

        # 确定说话人 ID
        sid = speaker_id if speaker_id is not None else self._default_speaker_id

        # 确定音量增益
        db = volume_db if volume_db is not None else self._volume_db

        # 生成音频
        audio = self._tts.generate(text, sid=sid, speed=speed)

        # 转换为 numpy 数组
        audio_data = np.array(audio.samples, dtype=np.float32)

        # 应用音量增益
        if db != 0:
            audio_data = self._apply_volume_gain(audio_data, db)

        duration = len(audio_data) / self.sample_rate

        return TTSResult(
            audio=audio_data,
            sample_rate=self.sample_rate,
            duration=duration,
            text=text,
            speaker_id=sid,
        )

    def _apply_volume_gain(self, audio_data: np.ndarray, db: float) -> np.ndarray:
        """应用音量增益

        使用归一化和指数增益实现 +25dB 放大。

        Args:
            audio_data: 原始音频数据
            db: 增益分贝数

        Returns:
            增益后的音频数据
        """
        audio_tensor = torch.from_numpy(audio_data)

        # 归一化 + 增益
        # 10^(db/20) = 增益倍数（电压/振幅）
        gain_factor = 10 ** (db / 20)
        audio_gain = torch.nn.functional.normalize(
            audio_tensor, p=2, dim=0
        ) * gain_factor

        return audio_gain.numpy()

    def is_available(self) -> bool:
        return self._tts is not None

    def close(self):
        """释放资源"""
        if self._tts is not None:
            # Sherpa-ONNX 不需要显式释放
            self._tts = None

    def __repr__(self) -> str:
        return (
            f"<SherpaTTSClient: {self.name}, "
            f"speakers={self.num_speakers}, "
            f"sr={self.sample_rate}>"
        )
