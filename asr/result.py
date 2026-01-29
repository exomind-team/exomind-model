"""ASR 增强结果模块

提供支持说话人分离和多格式输出的 ASRResult 数据类。
支持 JSON、SRT、VTT、TXT、LRC 格式导出。
"""

from dataclasses import dataclass, field, asdict
from typing import List, Optional, Tuple, Union, AsyncGenerator
from enum import Enum
import json


class OutputFormat(Enum):
    """输出格式枚举"""
    JSON = "json"
    SRT = "srt"
    VTT = "vtt"
    TXT = "txt"
    LRC = "lrc"


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

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "text": self.text,
            "state": self.state.value,
            "is_final": self.is_final,
            "confidence": self.confidence,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "chunk_duration": self.chunk_duration,
        }


@dataclass
class SpeakerSegment:
    """说话人片段

    Attributes:
        speaker_id: 说话人 ID (S01, S02, ...)
        text: 该片段的文本内容
        start_time: 开始时间（秒）
        end_time: 结束时间（秒）
        confidence: 置信度
    """
    speaker_id: str
    text: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    confidence: float = 1.0

    @property
    def formatted_time(self) -> str:
        """获取格式化时间 (HH:MM:SS.mmm)"""
        return format_time(self.start_time, "srt")

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "speaker_id": self.speaker_id,
            "text": self.text,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "confidence": self.confidence,
        }


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


@dataclass
class ASRResult:
    """ASR 识别结果（增强版，支持说话人分离和多格式输出）

    Attributes:
        text: 识别文本
        confidence: 置信度 (0.0 ~ 1.0)
        speaker_segments: 说话人片段列表
        num_speakers: 检测到的说话人数
        timestamps: 时间戳列表 [(start, end), ...]
        audio_duration: 音频时长（秒）
        engine: 使用的 ASR 引擎
    """

    text: str
    confidence: float = 1.0
    speaker_segments: List[SpeakerSegment] = field(default_factory=list)
    num_speakers: Optional[int] = None
    timestamps: Optional[List[Tuple[float, float]]] = None
    audio_duration: Optional[float] = None
    engine: str = "unknown"

    # ========== 原有方法 ==========

    @property
    def with_speaker_labels(self) -> str:
        """获取带说话人标签的文本

        Returns:
            带 [S01] 标签的文本
        """
        if not self.speaker_segments:
            return self.text

        # 按时间排序
        segments = sorted(self.speaker_segments, key=lambda x: x.start_time)

        # 构建带标签的文本
        lines = []
        current_speaker = None
        current_lines = []

        for seg in segments:
            if seg.speaker_id != current_speaker:
                if current_lines:
                    lines.append(f"[{current_speaker}] " + " ".join(current_lines))
                current_speaker = seg.speaker_id
                current_lines = [seg.text]
            else:
                current_lines.append(seg.text)

        # 添加最后一个说话人的内容
        if current_lines:
            lines.append(f"[{current_speaker}] " + " ".join(current_lines))

        return "\n".join(lines)

    def get_speaker_text(self, speaker_id: str) -> str:
        """获取指定说话人的所有文本

        Args:
            speaker_id: 说话人 ID

        Returns:
            该说话人的所有文本拼接
        """
        segments = [s for s in self.speaker_segments if s.speaker_id == speaker_id]
        return " ".join(s.text for s in sorted(segments, key=lambda x: x.start_time))

    def get_speakers(self) -> List[str]:
        """获取所有说话人 ID

        Returns:
            说话人 ID 列表
        """
        return list(set(s.speaker_id for s in self.speaker_segments))

    # ========== 新增：多格式输出方法 ==========

    def export(self, format: Union[OutputFormat, str], **kwargs) -> str:
        """导出为指定格式

        Args:
            format: 输出格式 (OutputFormat 或字符串)
            **kwargs: 格式特定参数
                - srt_index_start: SRT 序号起始值 (default: 1)
                - lrc_offset: LRC 时间偏移秒数 (default: 0.0)
                - indent: JSON 缩进空格数 (default: 2)

        Returns:
            格式化后的字符串
        """
        if isinstance(format, str):
            format = OutputFormat(format.lower())

        if format == OutputFormat.JSON:
            return self.to_json(**kwargs)
        elif format == OutputFormat.SRT:
            return self.to_srt(**kwargs)
        elif format == OutputFormat.VTT:
            return self.to_vtt(**kwargs)
        elif format == OutputFormat.TXT:
            return self.to_txt(**kwargs)
        elif format == OutputFormat.LRC:
            return self.to_lrc(**kwargs)
        else:
            raise ValueError(f"Unknown format: {format}")

    def to_json(self, indent: int = 2) -> str:
        """导出为 JSON 格式

        Args:
            indent: JSON 缩进空格数

        Returns:
            JSON 格式字符串
        """
        data = {
            "text": self.text,
            "confidence": self.confidence,
            "num_speakers": self.num_speakers,
            "audio_duration": self.audio_duration,
            "engine": self.engine,
            "speaker_segments": [seg.to_dict() for seg in self.speaker_segments],
        }
        return json.dumps(data, ensure_ascii=False, indent=indent)

    def to_srt(self, index_start: int = 1) -> str:
        """导出为 SRT 字幕格式

        Args:
            index_start: SRT 序号起始值

        Returns:
            SRT 格式字符串
        """
        if not self.speaker_segments:
            return ""

        segments = sorted(self.speaker_segments, key=lambda x: x.start_time)
        lines = []

        for i, seg in enumerate(segments):
            index = index_start + i
            start = format_time(seg.start_time, "srt")
            end = format_time(seg.end_time, "srt")
            speaker_label = f"[{seg.speaker_id}] " if seg.speaker_id else ""
            text = seg.text or ""

            lines.append(str(index))
            lines.append(f"{start} --> {end}")
            lines.append(f"{speaker_label}{text}")
            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def to_vtt(self) -> str:
        """导出为 VTT 字幕格式（WebVTT）

        Returns:
            VTT 格式字符串
        """
        if not self.speaker_segments:
            return "WEBVTT\n\n"

        segments = sorted(self.speaker_segments, key=lambda x: x.start_time)
        lines = ["WEBVTT", ""]

        for seg in segments:
            start = format_time(seg.start_time, "vtt")
            end = format_time(seg.end_time, "vtt")
            speaker_label = f"[{seg.speaker_id}] " if seg.speaker_id else ""
            text = seg.text or ""

            lines.append(f"{start} --> {end}")
            lines.append(f"{speaker_label}{text}")
            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def to_txt(self) -> str:
        """导出为纯文本格式（带说话人标签）

        Returns:
            纯文本字符串
        """
        return self.with_speaker_labels

    def to_lrc(self, offset: float = 0.0) -> str:
        """导出为 LRC 歌词格式

        Args:
            offset: 时间偏移秒数

        Returns:
            LRC 格式字符串
        """
        if not self.speaker_segments:
            return ""

        segments = sorted(self.speaker_segments, key=lambda x: x.start_time)
        lines = []

        for seg in segments:
            time = format_time(seg.start_time + offset, "lrc")
            speaker_label = f"[{seg.speaker_id}]" if seg.speaker_id else ""
            text = seg.text or ""

            lines.append(f"[{time}] {speaker_label} {text}")

        return "\n".join(lines)

    def to_dict(self) -> dict:
        """转换为 JSON 兼容的字典

        Returns:
            字典数据
        """
        return {
            "text": self.text,
            "confidence": self.confidence,
            "num_speakers": self.num_speakers,
            "audio_duration": self.audio_duration,
            "engine": self.engine,
            "speaker_segments": [seg.to_dict() for seg in self.speaker_segments],
        }


@dataclass
class DiarizationResult:
    """纯说话人分离结果（不含 ASR）

    Attributes:
        segments: 说话人片段列表
        num_speakers: 检测到的说话人数
    """
    segments: List[SpeakerSegment]
    num_speakers: Optional[int] = None

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        data = self.to_dict()
        return json.dumps(data, ensure_ascii=False, indent=indent)

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "num_speakers": self.num_speakers,
            "segments": [seg.to_dict() for seg in self.segments],
        }

    def to_srt(self, index_start: int = 1) -> str:
        """导出为 SRT 格式"""
        if not self.segments:
            return ""

        sorted_segments = sorted(self.segments, key=lambda x: x.start_time)
        lines = []

        for i, seg in enumerate(sorted_segments):
            index = index_start + i
            start = format_time(seg.start_time, "srt")
            end = format_time(seg.end_time, "srt")
            lines.append(str(index))
            lines.append(f"{start} --> {end}")
            lines.append(f"[{seg.speaker_id}]")
            lines.append("")

        return "\n".join(lines)
