# Voice-IME 说话人分离集成规范

> **Spec ID**: spec-006-asr-diarization
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-001-config, spec-005-speaker-recognition

## 1. 概述

本文档定义 Voice-IME 项目的说话人分离（Speaker Diarization）集成规范，将 CAM++ 声纹分离与 ASR 引擎结合，实现带说话人标签的语音识别输出。

## 2. 设计目标

- **带标签识别**: 识别结果包含说话人标签（S01, S02...）
- **时间戳输出**: 每个片段有精确的时间戳
- **统一接口**: 与现有 ASR 模块风格一致
- **可选功能**: 默认关闭，需要时启用

## 3. 架构设计

### 3.1 修改 ASRResult

```python
@dataclass
class ASRResult:
    """ASR 识别结果（增强版，支持说话人分离）"""

    # 基础字段
    text: str                          # 识别文本
    confidence: float = 1.0            # 置信度

    # 说话人分离字段（可选）
    speaker_segments: List[SpeakerSegment] = field(default_factory=list)
    num_speakers: Optional[int] = None  # 检测到的说话人数

    # 时间戳字段
    timestamps: Optional[List[Tuple[float, float]]] = None  # [(start, end), ...]

    @property
    def with_speaker_labels(self) -> str:
        """获取带说话人标签的文本"""
        ...
```

### 3.2 SpeakerSegment 数据类

```python
@dataclass
class SpeakerSegment:
    """说话人片段"""
    speaker_id: str           # 说话人 ID (S01, S02, ...)
    text: str                 # 该片段的文本
    start_time: float         # 开始时间（秒）
    end_time: float           # 结束时间（秒）
    confidence: float         # 置信度
```

### 3.3 修改 ASRClient 接口

```python
class ASRClient(ABC):
    """ASR 客户端抽象基类（增强版）"""

    @abstractmethod
    def recognize(
        self,
        audio_path: str,
        enable_diarization: bool = False,
        num_speakers: Optional[int] = None,
    ) -> ASRResult:
        """识别音频

        Args:
            audio_path: 音频文件路径
            enable_diarization: 是否启用说话人分离
            num_speakers: 预期说话人数（可选）

        Returns:
            ASRResult: 识别结果
        """
        ...
```

## 4. FunASR 集成

### 4.1 修改 FunASRClient

```python
class FunASRClient(ASRClient):
    """FunASR 语音识别客户端（支持说话人分离）"""

    def __init__(
        self,
        model: str = "paraformer-zh",
        enable_diarization: bool = False,
        **kwargs,
    ):
        """初始化 FunASR 客户端

        Args:
            model: 模型名称
            enable_diarization: 是否默认启用说话人分离
            **kwargs: 其他参数
        """
        self._enable_diarization = enable_diarization
        # ...

    def recognize(
        self,
        audio_path: str,
        enable_diarization: bool = False,
        num_speakers: Optional[int] = None,
    ) -> ASRResult:
        """识别音频（支持说话人分离）"""
        # 构建 FunASR 模型参数
        model_kwargs = {}

        if enable_diarization or self._enable_diarization:
            model_kwargs.update({
                "spk_model": "cam++",
                "spk_model_revision": "v2.0.2",
            })

        # 调用 FunASR
        model = AutoModel(**model_kwargs)
        result = model.generate(input=audio_path)

        # 解析结果
        return self._parse_result(result, enable_diarization)
```

### 4.2 结果解析

```python
def _parse_result(
    self,
    funasr_result: List[Dict],
    enable_diarization: bool,
) -> ASRResult:
    """解析 FunASR 结果"""
    if not funasr_result:
        return ASRResult(text="", confidence=0.0)

    raw = funasr_result[0]

    # 基础文本
    text = raw.get("text", "")

    # 说话人分离结果
    speaker_segments = []
    if enable_diarization and "spk" in raw:
        timestamps = raw.get("timestamp", [])
        spk_info = raw.get("spk", [])

        for ts, spk in zip(timestamps, spk_info):
            speaker_segments.append(SpeakerSegment(
                speaker_id=f"S{int(spk):02d}" if isinstance(spk, (int, float)) else str(spk),
                text="",  # 需要从 word_timestamp 中提取
                start_time=ts[0] / 1000,
                end_time=ts[1] / 1000,
                confidence=0.9,
            ))

    return ASRResult(
        text=text,
        speaker_segments=speaker_segments,
        num_speakers=len(set(s.speaker_id for s in speaker_segments)) if speaker_segments else None,
    )
```

## 5. 使用示例

### 5.1 基础识别（无说话人分离）

```python
from asr import create_asr_client

client = create_asr_client(engine="funasr")
result = client.recognize("meeting.wav")
print(result.text)  # "你好，今天的会议到此结束。"
```

### 5.2 带说话人分离的识别

```python
# 启用说话人分离
result = client.recognize(
    "meeting.wav",
    enable_diarization=True,
    num_speakers=2,
)

# 打印带标签的结果
for segment in result.speaker_segments:
    print(f"[{segment.start_time:.1f}s - {segment.end_time:.1f}s] "
          f"{segment.speaker_id}: {segment.text}")
```

### 5.3 带标签的完整文本

```python
print(result.with_speaker_labels)
# 输出:
# [S01] 你好，欢迎参加今天的会议。
# [S02] 谢谢，我们开始吧。
# [S01] 好的，首先请大家看一下这份报告。
```

## 6. 配置集成

### 6.1 config.yaml

```yaml
asr:
  default_engine: "funasr"
  enable_speaker_diarization: false  # 默认关闭

  # FunASR 特定配置
  funasr:
    model: "paraformer-zh"
    vad_model: "fsmn-vad"
    punc_model: "ct-punc-c"

    # 说话人分离（可选）
    diarization:
      enabled: false
      num_speakers: 2  # 自动检测如果未指定
```

### 6.2 命令行参数

```bash
# 启用说话人分离
exomind-model --asr funasr --diarization

# 指定说话人数
exomind-model --asr funasr --diarization --num-speakers 3
```

## 7. 输出格式

### 7.1 ASRResult JSON 输出

```json
{
  "text": "你好，今天的会议到此结束。",
  "confidence": 0.95,
  "num_speakers": 2,
  "speaker_segments": [
    {
      "speaker_id": "S01",
      "text": "你好，欢迎参加今天的会议。",
      "start_time": 0.0,
      "end_time": 3.5,
      "confidence": 0.92
    },
    {
      "speaker_id": "S02",
      "text": "谢谢，我们开始吧。",
      "start_time": 3.5,
      "end_time": 5.2,
      "confidence": 0.89
    }
  ]
}
```

## 8. 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 识别延迟 | < 2x 音频时长 | 不含分离 |
| 分离额外延迟 | < 0.5x 音频时长 | 说话人分离 |
| DER (Diarization Error Rate) | < 10% | 标准数据集 |
| 内存占用 | < 4GB | 运行时峰值 |

## 9. 验收标准

- [ ] FunASR 客户端支持 `enable_diarization` 参数
- [ ] ASRResult 包含 `speaker_segments` 字段
- [ ] 支持 `num_speakers` 参数指定说话人数
- [ ] 单元测试覆盖 > 80%
- [ ] 集成测试验证分离效果

## 10. 后续扩展

- [ ] MOSS 云端引擎支持说话人分离
- [ ] 说话人名称映射（ID → 姓名）
- [ ] 实时流式说话人分离
- [ ] 说话人自适应（基于少量样本）

---

*本文档遵循 Voice-IME Spec 规范*
