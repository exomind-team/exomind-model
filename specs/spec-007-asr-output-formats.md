# Voice-IME ASR 输出格式规范

> **Spec ID**: spec-007-asr-output-formats
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-006-asr-diarization

## 1. 概述

本文档定义 Voice-IME 项目的 ASR 输出格式规范，支持多种格式导出（JSON、SRT、VTT），并支持说话人标签。

## 2. 支持格式

| 格式 | 用途 | 说话人支持 | 时间戳 |
|------|------|-----------|--------|
| **JSON** | 程序处理 | ✅ | ✅ |
| **SRT** | 字幕文件 | ✅ | ✅ |
| **VTT** | Web 字幕 | ✅ | ✅ |
| **TXT** | 纯文本 | ✅ | ❌ |
| **LRC** | 歌词同步 | ✅ | ✅ |

## 3. 接口设计

### 3.1 ASRResult 增强

```python
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from enum import Enum

class OutputFormat(Enum):
    JSON = "json"
    SRT = "srt"
    VTT = "vtt"
    TXT = "txt"
    LRC = "lrc"

@dataclass
class ASRResult:
    """ASR 识别结果（增强版，支持多格式输出）"""

    # 基础字段
    text: str
    confidence: float = 1.0

    # 说话人分离字段
    speaker_segments: List[SpeakerSegment] = field(default_factory=list)
    num_speakers: Optional[int] = None

    # 元数据
    audio_duration: Optional[float] = None
    engine: str = "unknown"

    def export(self, format: OutputFormat, **kwargs) -> str:
        """导出为指定格式

        Args:
            format: 输出格式
            **kwargs: 格式特定参数
                - srt_index_start: SRT 序号起始值 (default: 1)
                - srt_separator: SRT 时间分隔符 (default: ' --> ')
                - lrc_offset: LRC 时间偏移秒数 (default: 0.0)
                - indent: JSON 缩进空格数 (default: 2)

        Returns:
            格式化后的字符串
        """
        ...

    def to_json(self, indent: int = 2) -> str:
        """导出为 JSON 格式"""
        ...

    def to_srt(self, index_start: int = 1) -> str:
        """导出为 SRT 字幕格式"""
        ...

    def to_vtt(self) -> str:
        """导出为 VTT 字幕格式"""
        ...

    def to_txt(self) -> str:
        """导出为纯文本格式"""
        ...

    def to_lrc(self, offset: float = 0.0) -> str:
        """导出为 LRC 歌词格式"""
        ...
```

### 3.2 SpeakerSegment 增强

```python
@dataclass
class SpeakerSegment:
    """说话人片段"""

    speaker_id: str           # S01, S02, ...
    text: str = ""
    start_time: float = 0.0   # 秒
    end_time: float = 0.0     # 秒
    confidence: float = 1.0

    @property
    def formatted_time(self) -> str:
        """获取格式化时间 (HH:MM:SS.mmm)"""
        ...
```

## 4. 格式规范

### 4.1 JSON 格式

```json
{
  "text": "你好，今天的会议到此结束。",
  "confidence": 0.95,
  "num_speakers": 2,
  "audio_duration": 30.5,
  "engine": "funasr",
  "speaker_segments": [
    {
      "speaker_id": "S01",
      "text": "你好，欢迎参加今天的会议。",
      "start_time": 0.0,
      "end_time": 3.5,
      "confidence": 0.92
    }
  ]
}
```

### 4.2 SRT 格式

```
1
00:00:00,000 --> 00:00:03,500
[S01] 你好，欢迎参加今天的会议。

2
00:00:03,500 --> 00:00:05,200
[S02] 谢谢，我们开始吧。
```

### 4.3 VTT 格式

```
WEBVTT

00:00:00.000 --> 00:00:03.500
[S01] 你好，欢迎参加今天的会议。

00:00:03.500 --> 00:00:05.200
[S02] 谢谢，我们开始吧。
```

### 4.4 LRC 格式

```
[00:00.00] [S01] 你好，欢迎参加今天的会议。
[00:03.50] [S02] 谢谢，我们开始吧。
```

### 4.5 TXT 格式（带说话人）

```
[S01] 你好，欢迎参加今天的会议。
[S02] 谢谢，我们开始吧。
[S01] 好的，首先请大家看一下这份报告。
```

## 5. 时间格式化

### 5.1 时间格式定义

| 格式 | 分隔符 | 毫秒 | 示例 |
|------|--------|------|------|
| SRT | `,` | 3位 | `00:00:00,000` |
| VTT | `.` | 3位 | `00:00:00.000` |
| LRC | `.` | 2位 | `00:00.00` |

### 5.2 时间转换

```python
def format_time(seconds: float, format: str = "srt") -> str:
    """将秒数转换为指定格式的时间字符串

    Args:
        seconds: 时间（秒）
        format: 格式类型 (srt, vtt, lrc)

    Returns:
        格式化的时间字符串
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    if format == "lrc":
        return f"{minutes:02d}:{secs:05.2f}"
    elif format == "vtt":
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
    else:  # srt
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace(".", ",")
```

## 6. 使用示例

### 6.1 基础导出

```python
from asr import FunASRClient, ASRResult

result = client.recognize("meeting.wav", enable_diarization=True)

# 导出为 SRT 字幕
srt = result.to_srt()
with open("meeting.srt", "w", encoding="utf-8") as f:
    f.write(srt)

# 导出为 VTT（Web）
vtt = result.to_vtt()

# 导出为 LRC（歌词）
lrc = result.to_lrc(offset=0.0)
```

### 6.2 使用 export() 方法

```python
# 使用 export 方法，指定格式
json_str = result.export("json", indent=2)
srt_str = result.export("srt", index_start=0)
```

### 6.3 带时间轴的完整导出

```python
# 包含所有信息的 JSON
full_json = result.to_json(indent=2)
print(full_json)
```

## 7. 配置集成

### 7.1 config.yaml

```yaml
asr:
  default_engine: "funasr"
  enable_speaker_diarization: false

  # 输出格式配置
  output:
    default_format: "txt"  # 默认输出格式
    srt:
      index_start: 1       # 序号起始值
    lrc:
      offset: 0.0          # 时间偏移（秒）
```

### 7.2 命令行参数

```bash
# 导出为 SRT
exomind-model --asr funasr --diarization --output srt -o meeting.srt

# 导出为 VTT
exomind-model --asr funasr --diarization --output vtt -o meeting.vtt

# 导出为 JSON（带完整信息）
exomind-model --asr funasr --diarization --output json -o meeting.json
```

## 8. 验收标准

- [ ] ASRResult 支持 5 种输出格式 (JSON, SRT, VTT, TXT, LRC)
- [ ] 时间戳正确格式化（SRT/VTT/LRC）
- [ ] 说话人标签正确显示
- [ ] 单元测试覆盖 > 80%
- [ ] 集成测试验证导出文件格式正确

## 9. 后续扩展

- [ ] Word/PDF 文档导出
- [ ] Markdown 格式（带时间轴）
- [ ] 批量文件导出
- [ ] 自定义模板支持

---

*本文档遵循 Voice-IME Spec 规范*
