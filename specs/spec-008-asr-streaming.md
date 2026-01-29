# Voice-IME 实时流式 ASR 规范

> **Spec ID**: spec-008-asr-streaming
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-001-config, spec-002-tts-architecture

## 1. 概述

本文档定义 Voice-IME 项目的实时流式 ASR（语音识别）规范，支持增量输出和低延迟交互。

## 2. 设计目标

- **低延迟**: < 600ms 端到端延迟
- **增量输出**: 实时返回识别结果，无需等待完整音频
- **统一接口**: 与现有 ASR 模块风格一致
- **流式支持**: 所有引擎可选支持流式模式

## 3. 架构设计.1 Streaming

### 3Result 数据类

```python
from dataclasses import dataclass
from typing import Optional, AsyncGenerator
from enum import Enum

class StreamingState(Enum):
    """流式识别状态"""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    INTERMEDIATE = "intermediate"  # 中间结果
    FINAL = "final"                # 最终结果
    COMPLETED = "completed"

@dataclass
class StreamingResult:
    """流式识别结果

    Attributes:
        text: 识别文本
        state: 识别状态
        is_final: 是否为最终结果
        confidence: 置信度
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        chunk_duration: 音频片段时长（秒）
    """
    text: str
    state: StreamingState = StreamingState.INTERMEDIATE
    is_final: bool = False
    confidence: float = 1.0
    start_time: float = 0.0
    end_time: float = 0.0
    chunk_duration: float = 0.0

    @property
    def with_speaker_label(self) -> str:
        """获取带说话人标签的文本"""
        ...
```

### 3.2 增强 ASRClient 基类

```python
class ASRClient(ABC):
    """ASR 引擎抽象基类（增强版，支持流式）"""

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
        """转写音频文件（离线模式）"""
        ...

    @abstractmethod
    def transcribe_streaming(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[StreamingResult, None]:
        """流式转写（实时模式）

        Args:
            audio_chunks: 音频数据异步生成器

        Yields:
            StreamingResult: 识别结果
        """
        ...

    @abstractmethod
    def transcribe_chunk(self, chunk: bytes) -> StreamingResult:
        """单次流式转写（简单模式）

        Args:
            chunk: 音频片段（bytes）

        Returns:
            StreamingResult: 识别结果
        """
        ...
```

### 3.3 FunASRNanoClient 流式支持

```python
class FunASRNanoClient(ASRClient):
    """Fun-ASR-Nano-2512 实时 ASR 引擎"""

    def transcribe_streaming(
        self,
        audio_chunks: AsyncGenerator[bytes, None],
    ) -> AsyncGenerator[StreamingResult, None]:
        """流式转写实现

        特点：
        - 延迟 < 600ms
        - 支持 31 种语言
        - 实时返回中间结果
        """
        async for chunk in audio_chunks:
            result = self.transcribe_chunk(chunk)
            yield result

    def transcribe_chunk(self, chunk: bytes) -> StreamingResult:
        """单次流式转写"""
        for text in self._model_instance.inference_stream([chunk]):
            return StreamingResult(
                text=text,
                state=StreamingState.FINAL,
                is_final=True,
            )
        return StreamingResult(text="")
```

## 4. 使用示例

### 4.1 基础流式识别

```python
import asyncio
from asr import create_asr_client

async def streaming_demo():
    """流式识别示例"""
    client = create_asr_client(engine="nano-2512")

    # 创建音频块生成器
    async def audio_generator():
        chunk_size = 3200  # 100ms @ 16kHz
        while True:
            chunk = await get_audio_chunk()  # 从麦克风获取
            if chunk is None:
                break
            yield chunk

    # 流式识别
    async for result in client.transcribe_streaming(audio_generator()):
        if result.is_final:
            print(f"[最终] {result.text}")
        else:
            print(f"[中间] {result.text}", end="\r")

asyncio.run(streaming_demo())
```

### 4.2 简单模式（单次调用）

```python
# 单次流式调用，适合短音频
client = create_asr_client(engine="nano-2512")
result = client.transcribe_chunk(audio_chunk)
print(f"识别结果: {result.text}")
```

### 4.3 带说话人分离的流式

```python
# 启用说话人分离
client = FunASRNanoClient()
async for result in client.transcribe_streaming(
    audio_generator(),
    enable_diarization=True,
    num_speakers=2,
):
    print(f"[{result.speaker_id}] {result.text}")
```

## 5. 配置集成

### 5.1 config.yaml

```yaml
asr:
  default_engine: "nano-2512"
  enable_streaming: true

  # 流式配置
  streaming:
    chunk_size_ms: 100      # 音频片段大小（毫秒）
    vad_threshold: 0.5      # VAD 阈值
    max_latency_ms: 600     # 最大延迟（毫秒）

  # 回退配置
  fallback_engine: "funasr"
```

### 5.2 命令行参数

```bash
# 启用流式模式
voice-ime --asr nano-2512 --streaming

# 指定音频片段大小
voice-ime --asr nano-2512 --streaming --chunk-size 100

# 禁用流式（离线模式）
voice-ime --asr nano-2512 --no-streaming
```

## 6. 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 端到端延迟 | < 600ms | 从音频输入到结果输出 |
| 首字延迟 | < 300ms | 第一个字的时间 |
| 吞吐率 | ≥1x 实时 | 实时率 |
| 准确率 | > 95% | 中文通用场景 |

## 7. 验收标准

- [ ] FunASRNanoClient 支持 `transcribe_streaming()`
- [ ] ASRClient 基类定义抽象流式方法
- [ ] 支持增量输出（中间结果 + 最终结果）
- [ ] 单元测试覆盖 > 80%
- [ ] 集成测试验证延迟 < 600ms

## 8. 后续扩展

- [ ] WebSocket 实时通信接口
- [ ] 浏览器端流式 ASR (WebRTC)
- [ ] 端到端加密传输
- [ ] 自适应 VAD

---

*本文档遵循 Voice-IME Spec 规范*
