# Voice-IME 声纹识别架构规范

> **Spec ID**: spec-005-speaker-recognition
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-002-tts-architecture

## 1. 概述

本文档定义 Voice-IME 项目的声纹识别功能，支持说话人注册、声纹验证和说话人分离。

## 2. 设计目标

- **说话人注册**: 从音频中提取并存储说话人声纹特征
- **声纹验证**: 验证音频是否属于已注册的说话人
- **说话人分离**: 在多人对话中自动识别不同说话人
- **统一接口**: 与现有 ASR/TTS 模块风格一致

## 3. 技术选型

### 3.1 核心模型

| 模型 | 参数量 | EER (VoxCeleb1-O) | 特点 |
|------|--------|-------------------|------|
| **CAM++** | 7.2M | 0.65% | 轻量、快速、FunASR 原生支持 |
| ECAPA-TDNN | 20.8M | 0.86% | 高精度，资源消耗大 |
| ERes2Net | 6.61M | 0.84% | 平衡性能与速度 |

### 3.2 选择理由

- **CAM++**: 7.2M 参数量小，推理快，与 FunASR 集成简单
- FunASR 原生支持，无需额外依赖

## 4. 架构设计

### 4.1 模块结构

```
exomind-model/
├── speaker/                      # 声纹识别模块
│   ├── __init__.py
│   ├── base.py                   # SpeakerClient 抽象基类
│   ├── factory.py                # 引擎工厂
│   ├── camplus_client.py         # CAM++ 实现
│   └── embedding.py              # 声纹向量处理
├── models/                       # 模型存储
│   └── speaker_embeddings/       # 已注册说话人声纹
└── tests/
    └── test_speaker.py           # 测试文件
```

### 4.2 类图

```python
class SpeakerClient(ABC):
    """声纹客户端抽象基类"""
    @property
    def name: str
    @property
    def embedding_dim: int
    def extract_embedding(audio_path) -> np.ndarray
    def verify(audio_path, speaker_id, threshold=0.5) -> float
    def register(audio_path, speaker_id) -> bool
    def identify(audio_path) -> List[Tuple[str, float]]
    def list_speakers() -> List[str]
    def delete_speaker(speaker_id) -> bool
```

### 4.3 数据结构

```python
@dataclass
class SpeakerEmbedding:
    """声纹特征"""
    speaker_id: str
    embedding: np.ndarray  # shape: (embedding_dim,)
    audio_path: Optional[str]
    created_at: float
    sample_rate: int

@dataclass
class SpeakerVerificationResult:
    """验证结果"""
    is_verified: bool
    confidence: float  # 0.0 ~ 1.0
    threshold: float
    embedding: Optional[np.ndarray]

@dataclass
class SpeakerSegment:
    """说话人片段"""
    speaker_id: str
    start_time: float
    end_time: float
    confidence: float
```

## 5. 接口设计

### 5.1 提取声纹

```python
def extract_embedding(audio_path: str) -> np.ndarray:
    """从音频提取声纹向量

    Args:
        audio_path: 音频文件路径

    Returns:
        声纹向量 (192维, CAM++ 默认)
    """
```

### 5.2 说话人注册

```python
def register_speaker(
    audio_path: str,
    speaker_id: str,
    name: Optional[str] = None,
) -> SpeakerEmbedding:
    """注册说话人

    Args:
        audio_path: 参考音频路径
        speaker_id: 说话人唯一标识
        name: 说话人名称（可选）

    Returns:
        注册的声纹对象
    """
```

### 5.3 声纹验证

```python
def verify_speaker(
    audio_path: str,
    speaker_id: str,
    threshold: float = 0.5,
) -> SpeakerVerificationResult:
    """验证说话人身份

    Args:
        audio_path: 待验证音频
        speaker_id: 已注册说话人 ID
        threshold: 验证阈值

    Returns:
        验证结果
    """
```

### 5.4 说话人分离

```python
def diarize(
    audio_path: str,
    num_speakers: Optional[int] = None,
) -> List[SpeakerSegment]:
    """说话人分离

    Args:
        audio_path: 音频文件路径
        num_speakers: 说话人数（可选，自动检测）

    Returns:
        说话人片段列表
    """
```

## 6. 使用示例

### 6.1 说话人注册

```python
from speaker import SpeakerClient, create_speaker_client

# 创建客户端
client = create_speaker_client(engine="cam++")

# 注册说话人 A
embedding_a = client.register(
    audio_path="speakers/user_a.wav",
    speaker_id="user_a",
    name="用户A"
)
print(f"注册成功: {embedding_a.speaker_id}")

# 注册说话人 B
client.register(
    audio_path="speakers/user_b.wav",
    speaker_id="user_b",
    name="用户B"
)
```

### 6.2 声纹验证

```python
# 验证音频是否属于用户 A
result = client.verify(
    audio_path="test_audio.wav",
    speaker_id="user_a",
    threshold=0.5
)

if result.is_verified:
    print(f"验证通过: 置信度 {result.confidence:.2%}")
else:
    print(f"验证失败: 置信度 {result.confidence:.2%}")
```

### 6.3 说话人分离

```python
# 分离多人对话
segments = client.diarize(
    audio_path="meeting.wav",
    num_speakers=2
)

for seg in segments:
    print(f"[{seg.start_time:.1f}s - {seg.end_time:.1f}s]: "
          f"Speaker {seg.speaker_id} ({seg.confidence:.1%})")
```

### 6.4 ASR 集成说话人标签

```python
# 使用 FunASR + CAM++ 进行带说话人标签的识别
from funasr import AutoModel

model = AutoModel(
    model="paraformer-zh",
    spk_model="cam++",
    vad_model="fsmn-vad",
    punc_model="ct-punc-c",
)

# 返回结果包含 speaker 信息
result = model.generate(input="meeting.wav")
print(result)
# {'text': '你好。', 'timestamp': [...], 'spk': 'S01', ...}
```

## 7. 存储设计

### 7.1 声纹存储

```python
# speaker_embeddings/{speaker_id}.npy
# speaker_embeddings/{speaker_id}.json (元数据)
```

### 7.2 存储格式

```json
{
  "speaker_id": "user_a",
  "name": "用户A",
  "embedding_dim": 192,
  "created_at": 1738089600.0,
  "sample_rate": 16000,
  "audio_path": "/path/to/reference.wav"
}
```

## 8. 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 声纹提取延迟 | < 100ms | 1秒音频 |
| 验证延迟 | < 50ms | 单次比对 |
| 分离延迟 | < 1.5x 音频时长 | 实时率 |
| EER | < 1.0% | 错误接受率 |
| 存储占用 | < 10KB/人 | 声纹向量 |

## 9. 验收标准

- [ ] 支持 CAM++ 声纹提取
- [ ] 支持说话人注册/验证/分离
- [ ] 声纹存储持久化
- [ ] 单元测试覆盖率 > 80%
- [ ] 与 ASR 模块集成（说话人标签）

## 10. 后续扩展

- [ ] 支持多模型 (ECAPA-TDNN, ERes2Net)
- [ ] 支持在线声纹注册
- [ ] 声纹质量检测
- [ ] 批量说话人注册

---

*本文档遵循 Voice-IME Spec 规范*
