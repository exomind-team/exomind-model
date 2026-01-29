"""ASR 说话人分离功能单元测试

测试 FunASRClient.recognize() 方法和 ASRResult 解析。
"""

import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path

import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from asr import FunASRClient, ASRResult, SpeakerSegment


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

    def test_segment_defaults(self):
        """测试默认值"""
        segment = SpeakerSegment(
            speaker_id="S02",
            start_time=0.0,
            end_time=1.0,
        )
        assert segment.text == ""
        assert segment.confidence == 1.0


class TestASRResult:
    """测试 ASRResult 数据类"""

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

    def test_result_with_speaker_segments(self):
        """测试带说话人片段的结果"""
        segments = [
            SpeakerSegment(speaker_id="S01", text="你好", start_time=0.0, end_time=1.0),
            SpeakerSegment(speaker_id="S02", text="再见", start_time=1.0, end_time=2.0),
        ]
        result = ASRResult(
            text="[S01] 你好 [S02] 再见",
            confidence=0.90,
            speaker_segments=segments,
            num_speakers=2,
        )
        assert len(result.speaker_segments) == 2
        assert result.num_speakers == 2

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


class TestFunASRClientRecognize:
    """测试 FunASRClient.recognize() 方法"""

    @pytest.fixture
    def mock_model(self):
        """创建模拟的 FunASR 模型"""
        mock = MagicMock()
        return mock

    @pytest.fixture
    def client_with_mock(self, mock_model):
        """创建带模拟模型的客户端（跳过模型加载）"""
        client = FunASRClient.__new__(FunASRClient)
        client._model_name = 'paraformer-zh'
        client._device = 'cpu'
        client._enable_diarization = True
        client._model_instance = mock_model
        return client

    def test_recognize_basic(self, client_with_mock, mock_model):
        """测试基础识别（无说话人分离）"""
        # 模拟 FunASR 返回结果
        mock_model.generate.return_value = [
            {"text": "今天天气很好"}
        ]

        result = client_with_mock.recognize("test.wav", enable_diarization=False)

        assert result.text == "今天天气很好"
        assert result.confidence > 0
        assert result.speaker_segments == []

    def test_recognize_with_diarization(self, client_with_mock, mock_model):
        """测试带说话人分离的识别"""
        # 模拟 FunASR 返回说话人分离结果
        mock_model.generate.return_value = [{
            "text": "[S01] 你好 [S02] 再见",
            "spk": [0, 1, 0],
            "timestamp": [[0, 1000], [1000, 2000], [2000, 3000]],
            "timestamp_wed": [
                [["word1", 0, 500], ["word2", 500, 1000]],
                [["word3", 1000, 1500]],
                [["word4", 2000, 2500], ["word5", 2500, 3000]],
            ],
        }]

        result = client_with_mock.recognize("test.wav", enable_diarization=True)

        assert result.text == "[S01] 你好 [S02] 再见"
        assert result.num_speakers == 2
        assert len(result.speaker_segments) == 3

        # 验证第一个片段
        assert result.speaker_segments[0].speaker_id == "S01"
        assert result.speaker_segments[0].start_time == 0.0
        assert result.speaker_segments[0].end_time == 1.0

        # 验证第二个片段
        assert result.speaker_segments[1].speaker_id == "S02"
        assert result.speaker_segments[1].start_time == 1.0
        assert result.speaker_segments[1].end_time == 2.0

    def test_recognize_num_speakers_override(self, client_with_mock, mock_model):
        """测试 num_speakers 参数覆盖"""
        mock_model.generate.return_value = [
            {"text": "测试文本"}
        ]

        # 客户端默认启用 diarization，但传入 num_speakers=3
        result = client_with_mock.recognize(
            "test.wav",
            enable_diarization=True,
            num_speakers=3,
        )

        # 验证 generate 被调用时传入了 num_spks=3
        mock_model.generate.assert_called_once()
        call_kwargs = mock_model.generate.call_args[1]
        assert call_kwargs.get("num_spks") == 3

    def test_parse_result_empty(self, client_with_mock):
        """测试空结果解析"""
        result = client_with_mock._parse_result([], False)
        assert result.text == ""
        assert result.confidence == 0.0

    def test_parse_result_single_speaker(self, client_with_mock):
        """测试单说话人结果"""
        result = client_with_mock._parse_result(
            [{"text": "只有一个说话人", "spk": [0, 0], "timestamp": [[0, 1000], [1000, 2000]]}],
            use_diarization=True,
        )
        assert result.num_speakers == 1
        assert len(result.speaker_segments) == 2


class TestFunASRClientDiarizationFlag:
    """测试 FunASRClient 说话人分离标志"""

    def test_enable_diarization_in_init(self):
        """测试初始化时启用说话人分离（跳过模型加载）"""
        client = FunASRClient.__new__(FunASRClient)
        client._model_name = 'paraformer-zh'
        client._device = 'cpu'
        client._enable_diarization = True
        client._model_instance = MagicMock()
        assert client._enable_diarization is True

    def test_disable_diarization_in_init(self):
        """测试初始化时禁用说话人分离（跳过模型加载）"""
        client = FunASRClient.__new__(FunASRClient)
        client._model_name = 'paraformer-zh'
        client._device = 'cpu'
        client._enable_diarization = False
        client._model_instance = MagicMock()
        assert client._enable_diarization is False

    def test_diarization_override_in_recognize(self):
        """测试 recognize() 中覆盖 diarization 设置"""
        client = FunASRClient.__new__(FunASRClient)
        client._model_name = 'paraformer-zh'
        client._device = 'cpu'
        client._enable_diarization = False
        mock_model = MagicMock()
        mock_model.generate.return_value = [{"text": "测试"}]
        client._model_instance = mock_model

        # recognize 时启用
        result = client.recognize("test.wav", enable_diarization=True)
        assert result is not None  # 调用成功


class TestSpeakerIdFormat:
    """测试说话人 ID 格式"""

    def test_numeric_speaker_id(self):
        """测试数字说话人 ID 格式化"""
        segment = SpeakerSegment(
            speaker_id="S01",  # 应该由解析逻辑生成
            text="测试",
            start_time=0.0,
            end_time=1.0,
        )
        assert segment.speaker_id.startswith("S")

    def test_multiple_speakers(self):
        """测试多说话人场景"""
        segments = [
            SpeakerSegment(speaker_id=f"S{i:02d}", text=f"说话{i}", start_time=i, end_time=i+1)
            for i in range(5)
        ]
        assert len(segments) == 5
        assert segments[0].speaker_id == "S00"
        assert segments[4].speaker_id == "S04"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
