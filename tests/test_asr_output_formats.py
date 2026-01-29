"""ASR 输出格式单元测试

测试 ASRResult 多格式导出功能 (JSON, SRT, VTT, TXT, LRC)。
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from asr import ASRResult, SpeakerSegment, OutputFormat


class TestSpeakerSegment:
    """测试 SpeakerSegment 数据类"""

    def test_create_segment(self):
        """测试创建说话人片段"""
        segment = SpeakerSegment(
            speaker_id="S01",
            text="你好",
            start_time=0.0,
            end_time=1.5,
            confidence=0.95,
        )
        assert segment.speaker_id == "S01"
        assert segment.text == "你好"
        assert segment.start_time == 0.0
        assert segment.end_time == 1.5
        assert segment.confidence == 0.95

    def test_to_dict(self):
        """测试转换为字典"""
        segment = SpeakerSegment(
            speaker_id="S01",
            text="测试",
            start_time=1.0,
            end_time=2.0,
            confidence=0.9,
        )
        data = segment.to_dict()
        assert data["speaker_id"] == "S01"
        assert data["text"] == "测试"
        assert data["start_time"] == 1.0
        assert data["end_time"] == 2.0


class TestFormatTime:
    """测试时间格式化函数"""

    def test_srt_format(self):
        """测试 SRT 时间格式"""
        from asr.result import format_time

        # 0 秒
        assert format_time(0.0, "srt") == "00:00:00,000"
        # 1 秒
        assert format_time(1.0, "srt") == "00:00:01,000"
        # 1 分 30 秒
        assert format_time(90.0, "srt") == "00:01:30,000"
        # 1 小时
        assert format_time(3600.0, "srt") == "01:00:00,000"

    def test_vtt_format(self):
        """测试 VTT 时间格式"""
        from asr.result import format_time

        assert format_time(0.0, "vtt") == "00:00:00.000"
        assert format_time(1.0, "vtt") == "00:00:01.000"
        assert format_time(90.0, "vtt") == "00:01:30.000"

    def test_lrc_format(self):
        """测试 LRC 时间格式"""
        from asr.result import format_time

        assert format_time(0.0, "lrc") == "00:00.00"
        assert format_time(30.0, "lrc") == "00:30.00"
        assert format_time(90.0, "lrc") == "01:30.00"


class TestASRResultBasic:
    """测试 ASRResult 基础功能"""

    def test_create_result(self):
        """测试创建 ASR 结果"""
        result = ASRResult(
            text="今天天气很好",
            confidence=0.92,
        )
        assert result.text == "今天天气很好"
        assert result.confidence == 0.92
        assert result.speaker_segments == []
        assert result.num_speakers is None

    def test_with_speaker_labels(self):
        """测试带标签文本属性"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="第一句", start_time=0.0, end_time=1.0),
            SpeakerSegment(speaker_id="S02", text="第二句", start_time=1.0, end_time=2.0),
        ]
        result = ASRResult(
            text="第一句第二句",
            speaker_segments=segments,
        )
        labels = result.with_speaker_labels
        assert "S01" in labels
        assert "S02" in labels

    def test_get_speakers(self):
        """测试获取说话人列表"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="第一句", start_time=0.0, end_time=1.0),
            SpeakerSegment(speaker_id="S02", text="第二句", start_time=1.0, end_time=2.0),
            SpeakerSegment(speaker_id="S01", text="第三句", start_time=2.0, end_time=3.0),
        ]
        result = ASRResult(
            text="测试",
            speaker_segments=segments,
        )
        speakers = result.get_speakers()
        assert len(speakers) == 2
        assert "S01" in speakers
        assert "S02" in speakers


class TestASRResultToJson:
    """测试 ASRResult JSON 导出"""

    def test_to_json_empty(self):
        """测试空结果 JSON"""
        result = ASRResult(text="测试")
        json_str = result.to_json()
        assert "测试" in json_str

    def test_to_json_with_segments(self):
        """测试带片段结果 JSON"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="你好", start_time=0.0, end_time=1.0),
        ]
        result = ASRResult(
            text="你好",
            confidence=0.95,
            speaker_segments=segments,
            num_speakers=1,
            audio_duration=10.0,
            engine="funasr",
        )
        json_str = result.to_json(indent=2)
        assert "S01" in json_str
        assert "0.95" in json_str
        assert "10.0" in json_str
        assert "funasr" in json_str


class TestASRResultToSrt:
    """测试 ASRResult SRT 导出"""

    def test_to_srt_empty(self):
        """测试空结果 SRT"""
        result = ASRResult(text="测试")
        srt = result.to_srt()
        assert srt == ""

    def test_to_srt_single_segment(self):
        """测试单片段 SRT"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="你好", start_time=0.0, end_time=1.5),
        ]
        result = ASRResult(
            text="你好",
            speaker_segments=segments,
        )
        srt = result.to_srt()
        assert "1" in srt
        assert "00:00:00,000 --> 00:00:01,500" in srt
        assert "[S01] 你好" in srt

    def test_to_srt_multiple_segments(self):
        """测试多片段 SRT"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="第一句", start_time=0.0, end_time=1.0),
            SpeakerSegment(speaker_id="S02", text="第二句", start_time=1.0, end_time=2.0),
            SpeakerSegment(speaker_id="S01", text="第三句", start_time=2.0, end_time=3.0),
        ]
        result = ASRResult(
            text="测试",
            speaker_segments=segments,
        )
        srt = result.to_srt(index_start=0)
        lines = [l for l in srt.split("\n") if l]  # 过滤空行
        # 检查索引从 0 开始
        assert lines[0] == "0"
        assert lines[3] == "1"
        assert lines[6] == "2"

    def test_to_srt_time_format(self):
        """测试 SRT 时间格式正确性"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="测试", start_time=90.5, end_time=95.0),
        ]
        result = ASRResult(text="测试", speaker_segments=segments)
        srt = result.to_srt()
        assert "00:01:30,500 --> 00:01:35,000" in srt


class TestASRResultToVtt:
    """测试 ASRResult VTT 导出"""

    def test_to_vtt_empty(self):
        """测试空结果 VTT"""
        result = ASRResult(text="测试")
        vtt = result.to_vtt()
        assert "WEBVTT" in vtt

    def test_to_vtt_with_segments(self):
        """测试带片段结果 VTT"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="你好", start_time=0.0, end_time=1.5),
        ]
        result = ASRResult(
            text="你好",
            speaker_segments=segments,
        )
        vtt = result.to_vtt()
        assert "WEBVTT" in vtt
        assert "00:00:00.000 --> 00:00:01.500" in vtt
        assert "[S01] 你好" in vtt

    def test_vtt_time_format(self):
        """测试 VTT 时间格式（点号分隔）"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="测试", start_time=1.0, end_time=2.0),
        ]
        result = ASRResult(text="测试", speaker_segments=segments)
        vtt = result.to_vtt()
        assert "00:00:01.000 --> 00:00:02.000" in vtt


class TestASRResultToTxt:
    """测试 ASRResult TXT 导出"""

    def test_to_txt_no_segments(self):
        """测试无片段 TXT"""
        result = ASRResult(text="纯文本内容")
        txt = result.to_txt()
        assert txt == "纯文本内容"

    def test_to_txt_with_speaker_labels(self):
        """测试带说话人标签 TXT"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="第一句", start_time=0.0, end_time=1.0),
            SpeakerSegment(speaker_id="S02", text="第二句", start_time=1.0, end_time=2.0),
        ]
        result = ASRResult(
            text="测试",
            speaker_segments=segments,
        )
        txt = result.to_txt()
        assert "[S01] 第一句" in txt
        assert "[S02] 第二句" in txt


class TestASRResultToLrc:
    """测试 ASRResult LRC 导出"""

    def test_to_lrc_empty(self):
        """测试空结果 LRC"""
        result = ASRResult(text="测试")
        lrc = result.to_lrc()
        assert lrc == ""

    def test_to_lrc_with_segments(self):
        """测试带片段结果 LRC"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="歌词一", start_time=0.0, end_time=1.0),
            SpeakerSegment(speaker_id="S02", text="歌词二", start_time=30.0, end_time=31.0),
        ]
        result = ASRResult(text="测试", speaker_segments=segments)
        lrc = result.to_lrc()
        assert "[00:00.00] [S01] 歌词一" in lrc
        assert "[00:30.00] [S02] 歌词二" in lrc

    def test_lrc_offset(self):
        """测试 LRC 时间偏移"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="歌词", start_time=0.0, end_time=1.0),
        ]
        result = ASRResult(text="测试", speaker_segments=segments)
        lrc = result.to_lrc(offset=5.0)
        assert "[00:05.00]" in lrc


class TestASRResultExport:
    """测试 ASRResult export 方法"""

    def test_export_json_string(self):
        """测试字符串格式导出"""
        result = ASRResult(text="测试")
        json_str = result.export("json")
        assert "测试" in json_str

    def test_export_srt_string(self):
        """测试字符串格式导出"""
        segments = [SpeakerSegment(speaker_id="S01", text="测试", start_time=0.0, end_time=1.0)]
        result = ASRResult(text="测试", speaker_segments=segments)
        srt = result.export("srt")
        assert "S01" in srt

    def test_export_vtt_string(self):
        """测试字符串格式导出"""
        segments = [SpeakerSegment(speaker_id="S01", text="测试", start_time=0.0, end_time=1.0)]
        result = ASRResult(text="测试", speaker_segments=segments)
        vtt = result.export("vtt")
        assert "WEBVTT" in vtt

    def test_export_lrc_string(self):
        """测试字符串格式导出"""
        segments = [SpeakerSegment(speaker_id="S01", text="测试", start_time=0.0, end_time=1.0)]
        result = ASRResult(text="测试", speaker_segments=segments)
        lrc = result.export("lrc")
        assert "S01" in lrc

    def test_export_txt_string(self):
        """测试字符串格式导出"""
        result = ASRResult(text="纯文本")
        txt = result.export("txt")
        assert txt == "纯文本"

    def test_export_enum(self):
        """测试枚举格式导出"""
        result = ASRResult(text="测试")
        json_str = result.export(OutputFormat.JSON)
        assert "测试" in json_str


class TestOutputFormat:
    """测试 OutputFormat 枚举"""

    def test_format_values(self):
        """测试格式值"""
        assert OutputFormat.JSON.value == "json"
        assert OutputFormat.SRT.value == "srt"
        assert OutputFormat.VTT.value == "vtt"
        assert OutputFormat.TXT.value == "txt"
        assert OutputFormat.LRC.value == "lrc"


class TestASRResultToDict:
    """测试 ASRResult to_dict 方法"""

    def test_to_dict_empty(self):
        """测试空结果转字典"""
        result = ASRResult(text="测试")
        data = result.to_dict()
        assert data["text"] == "测试"
        assert data["confidence"] == 1.0

    def test_to_dict_with_segments(self):
        """测试带片段转字典"""
        segments = [SpeakerSegment(speaker_id="S01", text="测试", start_time=0.0, end_time=1.0)]
        result = ASRResult(
            text="测试",
            speaker_segments=segments,
            num_speakers=1,
            audio_duration=10.0,
            engine="funasr",
        )
        data = result.to_dict()
        assert data["num_speakers"] == 1
        assert data["audio_duration"] == 10.0
        assert data["engine"] == "funasr"
        assert len(data["speaker_segments"]) == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
