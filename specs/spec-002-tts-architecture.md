# Voice-IME TTS 模块架构规范

> **Spec ID**: spec-002-tts-architecture
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-001-config

## 1. 概述

本文档定义 Voice-IME TTS（文本转语音）模块的架构设计，包括：
- 抽象基类设计
- 引擎工厂模式
- Sherpa-ONNX 实现
- 音量增益处理

## 2. 模块结构

```
tts/
├── __init__.py           # 模块导出
├── base.py               # TTSClient 抽象基类
├── factory.py            # TTSClientFactory 工厂类
├── sherpa_client.py      # Sherpa-ONNX TTS 实现
├── config.py             # TTS 配置类
└── exceptions.py         # TTS 相关异常
```

## 3. 核心接口

### 3.1 TTSClient 抽象基类

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, List
import numpy as np

@dataclass
class TTSResult:
    """TTS 生成结果"""
    audio: np.ndarray          # 音频数据 (float32)
    sample_rate: int           # 采样率
    duration: float            # 音频时长（秒）
    text: str                  # 原始文本
    speaker_id: Optional[int]  # 说话人 ID（如果有）

class TTSClient(ABC):
    """TTS 客户端抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        pass

    @property
    @abstractmethod
    def sample_rate(self) -> int:
        """返回采样率"""
        pass

    @property
    @abstractmethod
    def num_speakers(self) -> Optional[int]:
        """返回说话人数量，None 表示不支持多说话人"""
        pass

    @abstractmethod
    def generate(
        self,
        text: str,
        speaker_id: Optional[int] = None,
        speed: float = 1.0,
        **kwargs
    ) -> TTSResult:
        """
        生成语音

        Args:
            text: 要转换的文本
            speaker_id: 说话人 ID（如果支持）
            speed: 语速 (0.5 - 2.0)
            **kwargs: 额外参数

        Returns:
            TTSResult: 生成结果
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查引擎是否可用"""
        pass

    @abstractmethod
    def close(self):
        """释放资源"""
        pass
```

### 3.2 SherpaTTSClient 实现

```python
import os
import sherpa_onnx
import numpy as np
import torch
from pathlib import Path
from typing import Optional

class SherpaTTSClient(TTSClient):
    """Sherpa-ONNX TTS 客户端"""

    def __init__(
        self,
        model: str = "vits-zh-hf-fanchen-C",
        speaker_id: int = 77,
        volume_db: float = 25.0,
        model_dir: Optional[str] = None
    ):
        """
        初始化 Sherpa TTS 客户端

        Args:
            model: 模型名称 (vits-zh-hf-fanchen-C | kokoro-multi-lang-v1_1)
            speaker_id: 默认说话人 ID
            volume_db: 音量增益 (dB)
            model_dir: 模型目录，默认从 models/ 目录查找
        """
        self._model = model
        self._default_speaker_id = speaker_id
        self._volume_db = volume_db
        self._model_dir = model_dir or self._find_model_dir(model)
        self._tts = None
        self._init_engine()

    def _find_model_dir(self, model: str) -> str:
        """查找模型目录"""
        base_dir = Path("models")
        for path in base_dir.iterdir():
            if path.is_dir() and model.lower() in path.name.lower():
                return str(path)
        raise FileNotFoundError(f"Model not found: {model}")

    def _init_engine(self):
        """初始化 TTS 引擎"""
        if self._model == "vits-zh-hf-fanchen-C":
            self._init_vits()
        elif self._model == "kokoro-multi-lang-v1_1":
            self._init_kokoro()
        else:
            raise ValueError(f"Unsupported model: {self._model}")

    def _init_vits(self):
        """初始化 VITS 引擎"""
        model_path = os.path.join(self._model_dir, f"{self._model}.onnx")
        tokens_path = os.path.join(self._model_dir, "tokens.txt")
        lexicon_path = os.path.join(self._model_dir, "lexicon.txt")

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
        # TODO: 实现 Kokoro 初始化
        pass

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
        """生成语音"""
        if not self._tts:
            raise RuntimeError("TTS engine not initialized")

        sid = speaker_id or self._default_speaker_id
        audio = self._tts.generate(text, sid=sid, speed=speed)

        # 转换为 numpy 数组
        audio_data = np.array(audio.samples, dtype=np.float32)

        # 应用音量增益
        db = volume_db if volume_db is not None else self._volume_db
        if db != 0:
            audio_tensor = torch.from_numpy(audio_data)
            audio_gain = torch.nn.functional.normalize(
                audio_tensor, p=2, dim=0
            ) * (10 ** (db / 20))
            audio_data = audio_gain.numpy()

        duration = len(audio_data) / self.sample_rate

        return TTSResult(
            audio=audio_data,
            sample_rate=self.sample_rate,
            duration=duration,
            text=text,
            speaker_id=sid
        )

    def is_available(self) -> bool:
        return self._tts is not None

    def close(self):
        """释放资源（Sherpa-ONNX 不需要显式释放）"""
        self._tts = None
```

### 3.3 TTSClientFactory 工厂类

```python
from typing import Dict, Type, Optional
from .base import TTSClient, TTSResult
from .sherpa_client import SherpaTTSClient

class TTSClientFactory:
    """TTS 客户端工厂"""

    _engines: Dict[str, Type[TTSClient]] = {
        "sherpa-vits": SherpaTTSClient,
        "sherpa-kokoro": SherpaTTSClient,
    }

    @classmethod
    def register(cls, name: str, engine_class: Type[TTSClient]):
        """注册新的 TTS 引擎"""
        cls._engines[name.lower()] = engine_class

    @classmethod
    def create(
        cls,
        engine: str = "sherpa-vits",
        **kwargs
    ) -> TTSClient:
        """
        创建 TTS 客户端实例

        Args:
            engine: 引擎名称
            **kwargs: 引擎特定参数

        Returns:
            TTSClient 实例

        Raises:
            ValueError: 不支持的引擎
        """
        engine = engine.lower()
        if engine not in cls._engines:
            raise ValueError(
                f"Unsupported TTS engine: {engine}. "
                f"Available: {list(cls._engines.keys())}"
            )

        return cls._engines[engine](**kwargs)

    @classmethod
    def available_engines(cls) -> list:
        """列出可用的引擎"""
        return list(cls._engines.keys())

    @classmethod
    def is_available(cls, engine: str) -> bool:
        """检查引擎是否可用"""
        try:
            client = cls.create(engine)
            available = client.is_available()
            client.close()
            return available
        except Exception:
            return False
```

## 4. 模块导出

### 4.1 __init__.py

```python
"""Voice-IME TTS 模块"""

from .base import TTSClient, TTSResult
from .factory import TTSClientFactory
from .sherpa_client import SherpaTTSClient

__all__ = [
    "TTSClient",
    "TTSResult",
    "TTSClientFactory",
    "SherpaTTSClient",
]

def create_tts_client(engine: str = "sherpa-vits", **kwargs) -> TTSClient:
    """便捷的 TTS 客户端创建函数"""
    return TTSClientFactory.create(engine, **kwargs)
```

## 5. 使用示例

```python
from tts import create_tts_client, TTSClientFactory

# 使用工厂创建客户端
tts = create_tts_client(
    engine="sherpa-vits",
    model="vits-zh-hf-fanchen-C",
    speaker_id=77,
    volume_db=25.0
)

# 生成语音
result = tts.generate("你好，我是语音助手！")
print(f"生成完成: {result.duration:.2f}秒")

# 列出可用引擎
print("可用引擎:", TTSClientFactory.available_engines())

# 释放资源
tts.close()
```

## 6. 验收标准

- [ ] TTSClient 抽象基类定义完整
- [ ] SherpaTTSClient 支持 vits-zh-hf-fanchen-C
- [ ] 支持音量增益 (+25dB)
- [ ] TTSClientFactory 工厂模式正常工作
- [ ] 支持引擎切换和回退
- [ ] 单元测试覆盖率 > 80%

## 7. 性能基准

| 指标 | 目标值 | 说明 |
|------|--------|------|
| RTF | < 0.5 | 生成速度 |
| 首字延迟 | < 100ms | 首字输出时间 |
| 内存占用 | < 500MB | 模型加载后 |

## 8. 后续扩展

- [ ] Kokoro 模型支持
- [ ] 实时流式 TTS
- [ ] 情感 TTS
- [ ] 声音克隆

---

*本文档遵循 Voice-IME Spec 规范*
