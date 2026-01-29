"""ASR 流式识别单元测试

测试 StreamingResult、StreamingState 和流式识别功能。
"""

import pytest
import sys
import asyncio
import numpy as np
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from asr import StreamingResult, StreamingState, ASRClient


class TestStreamingState:
    """测试 StreamingState 枚举"""

    def test_state_values(self):
        """测试状态值"""
        assert StreamingState.STARTED.value == "started"
        assert StreamingState.IN_PROGRESS.value == "in_progress"
        assert StreamingState.INTERMEDIATE.value == "intermediate"
        assert StreamingState.FINAL.value == "final"
        assert StreamingState.COMPLETED.value == "completed"

    def test_state_count(self):
        """测试状态数量"""
        assert len(StreamingState) == 5


class TestStreamingResult:
    """测试 StreamingResult 数据类"""

    def test_create_empty_result(self):
        """测试创建空结果"""
        result = StreamingResult(text="")
        assert result.text == ""
        assert result.state == StreamingState.INTERMEDIATE
        assert result.is_final == False
        assert result.confidence == 1.0

    def test_create_full_result(self):
        """测试创建完整结果"""
        result = StreamingResult(
            text="你好",
            state=StreamingState.FINAL,
            is_final=True,
            confidence=0.95,
            start_time=0.0,
            end_time=1.5,
            chunk_duration=0.1,
        )
        assert result.text == "你好"
        assert result.state == StreamingState.FINAL
        assert result.is_final == True
        assert result.confidence == 0.95
        assert result.start_time == 0.0
        assert result.end_time == 1.5
        assert result.chunk_duration == 0.1

    def test_to_dict(self):
        """测试转换为字典"""
        result = StreamingResult(
            text="测试",
            state=StreamingState.INTERMEDIATE,
            is_final=True,
            confidence=0.9,
            start_time=0.5,
            end_time=1.0,
            chunk_duration=0.1,
        )
        data = result.to_dict()
        assert data["text"] == "测试"
        assert data["state"] == "intermediate"
        assert data["is_final"] == True
        assert data["confidence"] == 0.9
        assert data["start_time"] == 0.5
        assert data["end_time"] == 1.0
        assert data["chunk_duration"] == 0.1


class TestASRClientStreaming:
    """测试 ASRClient 流式方法（Mock）"""

    def test_transcribe_chunk_returns_streaming_result(self):
        """测试 transcribe_chunk 返回 StreamingResult"""

        # 创建 Mock 客户端
        class MockClient(ASRClient):
            def __init__(self):
                self._name = "MockClient"

            @property
            def name(self):
                return self._name

            @property
            def is_available(self):
                return True

            def transcribe(self, audio_path: str) -> str:
                return "mock transcription"

            def transcribe_audio_data(self, audio_data) -> str:
                return "mock audio data transcription"

        client = MockClient()

        # 测试 transcribe_chunk 返回 StreamingResult
        # 使用有效的 16bit audio buffer size (3200 bytes = 1600 samples)
        chunk = np.zeros(1600, dtype=np.int16).tobytes()
        result = client.transcribe_chunk(chunk)

        assert isinstance(result, StreamingResult)
        assert result.state == StreamingState.INTERMEDIATE
        assert result.is_final == True

    def test_transcribe_chunk_with_custom_state(self):
        """测试自定义状态的 transcribe_chunk"""

        class CustomClient(ASRClient):
            @property
            def name(self):
                return "Custom"

            @property
            def is_available(self):
                return True

            def transcribe(self, audio_path: str) -> str:
                return "result"

            def transcribe_audio_data(self, audio_data) -> str:
                return "result"

            def transcribe_chunk(self, chunk: bytes) -> StreamingResult:
                return StreamingResult(
                    text="custom result",
                    state=StreamingState.FINAL,
                    is_final=True,
                )

        client = CustomClient()
        chunk = np.zeros(1600, dtype=np.int16).tobytes()
        result = client.transcribe_chunk(chunk)

        assert result.text == "custom result"
        assert result.state == StreamingState.FINAL
        assert result.is_final == True

    @pytest.mark.asyncio
    async def test_transcribe_streaming_async_generator(self):
        """测试异步生成器流式识别"""

        class StreamingClient(ASRClient):
            def __init__(self):
                self.call_count = 0

            @property
            def name(self):
                return "Streaming"

            @property
            def is_available(self):
                return True

            def transcribe(self, audio_path: str) -> str:
                return "transcribe"

            def transcribe_audio_data(self, audio_data) -> str:
                return "transcribe"

            def transcribe_chunk(self, chunk: bytes) -> StreamingResult:
                self.call_count += 1
                return StreamingResult(
                    text=f"chunk {self.call_count}",
                    state=StreamingState.INTERMEDIATE,
                    is_final=True,
                )

        client = StreamingClient()

        # 创建异步生成器
        async def audio_gen():
            for i in range(3):
                yield f"chunk_{i}".encode()

        # 测试流式识别
        results = []
        async for result in client.transcribe_streaming(audio_gen()):
            results.append(result)

        # 验证结果
        assert len(results) == 3
        assert results[0].text == "chunk 1"
        assert results[1].text == "chunk 2"
        assert results[2].text == "chunk 3"


class TestStreamingResultStateTransitions:
    """测试流式识别状态转换"""

    def test_intermediate_to_final(self):
        """测试中间结果到最终结果的转换"""
        intermediate = StreamingResult(
            text="你好",
            state=StreamingState.INTERMEDIATE,
            is_final=False,
        )
        final = StreamingResult(
            text="你好世界",
            state=StreamingState.FINAL,
            is_final=True,
        )

        assert intermediate.is_final == False
        assert final.is_final == True
        assert intermediate.state != final.state

    def test_session_lifecycle(self):
        """测试会话生命周期状态"""
        # 开始会话
        started = StreamingResult(text="", state=StreamingState.STARTED)

        # 识别中
        in_progress = StreamingResult(text="你好", state=StreamingState.IN_PROGRESS)

        # 中间结果
        intermediate = StreamingResult(text="你好世", state=StreamingState.INTERMEDIATE)

        # 最终结果
        final = StreamingResult(text="你好世界", state=StreamingState.FINAL, is_final=True)

        # 会话完成
        completed = StreamingResult(text="", state=StreamingState.COMPLETED, is_final=True)

        # 验证状态顺序
        states = [
            started.state,
            in_progress.state,
            intermediate.state,
            final.state,
            completed.state,
        ]
        expected = [
            StreamingState.STARTED,
            StreamingState.IN_PROGRESS,
            StreamingState.INTERMEDIATE,
            StreamingState.FINAL,
            StreamingState.COMPLETED,
        ]
        assert states == expected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
