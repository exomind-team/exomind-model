"""引擎选择器单元测试

测试 EngineSelector 的场景检测、评分和选择逻辑。
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from asr import (
    EngineSelector,
    AudioContext,
    Scenario,
    EngineScore,
    SelectionResult,
)


class TestScenarioEnum:
    """测试 Scenario 枚举"""

    def test_scenario_values(self):
        """测试场景值"""
        assert Scenario.REALTIME.value == 1
        assert Scenario.TRANSCRIPTION.value == 2
        assert Scenario.MEETING.value == 3
        assert Scenario.MULTILINGUAL.value == 4
        assert Scenario.COMMAND.value == 5
        assert Scenario.GENERAL.value == 6

    def test_scenario_count(self):
        """测试场景数量"""
        assert len(Scenario) == 6


class TestAudioContext:
    """测试 AudioContext 数据类"""

    def test_default_context(self):
        """测试默认上下文"""
        ctx = AudioContext()
        assert ctx.audio_path is None
        assert ctx.duration_seconds == 0.0
        assert ctx.estimated_speakers == 1
        assert ctx.language_hint == "auto"
        assert ctx.is_streaming is False
        assert ctx.priority == "balanced"

    def test_custom_context(self):
        """测试自定义上下文"""
        ctx = AudioContext(
            duration_seconds=30.0,
            estimated_speakers=3,
            language_hint="zh",
            is_streaming=True,
            priority="latency",
        )
        assert ctx.duration_seconds == 30.0
        assert ctx.estimated_speakers == 3
        assert ctx.language_hint == "zh"
        assert ctx.is_streaming is True
        assert ctx.priority == "latency"


class TestEngineSelector:
    """测试 EngineSelector"""

    def test_default_engines(self):
        """测试默认引擎列表"""
        selector = EngineSelector()
        assert "nano-2512" in selector._available_engines
        assert "paraformer-zh" in selector._available_engines
        assert "sensevoice" in selector._available_engines
        assert "moss" in selector._available_engines

    def test_filter_engines(self):
        """测试引擎过滤"""
        selector = EngineSelector(available_engines=["nano-2512", "moss"])
        assert len(selector._available_engines) == 2
        assert "nano-2512" in selector._available_engines
        assert "moss" in selector._available_engines

    def test_invalid_engine_filter(self):
        """测试无效引擎过滤"""
        selector = EngineSelector(available_engines=["unknown-engine"])
        assert len(selector._available_engines) == 0


class TestScenarioDetection:
    """测试场景检测"""

    def test_streaming_detects_realtime(self):
        """流式输入 → 实时场景"""
        selector = EngineSelector()
        ctx = AudioContext(is_streaming=True)
        scenario = selector.detect_scenario(ctx)
        assert scenario == Scenario.REALTIME

    def test_english_detects_multilingual(self):
        """英文 → 多语言场景"""
        selector = EngineSelector()
        ctx = AudioContext(language_hint="en")
        scenario = selector.detect_scenario(ctx)
        assert scenario == Scenario.MULTILINGUAL

    def test_multi_language_hint_detects_multilingual(self):
        """multi → 多语言场景"""
        selector = EngineSelector()
        ctx = AudioContext(language_hint="multi")
        scenario = selector.detect_scenario(ctx)
        assert scenario == Scenario.MULTILINGUAL

    def test_short_audio_latency_detects_command(self):
        """短音频 + 延迟敏感 → 命令场景"""
        selector = EngineSelector()
        ctx = AudioContext(
            duration_seconds=3.0,
            priority="latency",
        )
        scenario = selector.detect_scenario(ctx)
        assert scenario == Scenario.COMMAND

    def test_multi_speakers_detects_meeting(self):
        """多说话人 → 会议场景"""
        selector = EngineSelector()
        ctx = AudioContext(estimated_speakers=3)
        scenario = selector.detect_scenario(ctx)
        assert scenario == Scenario.MEETING

    def test_long_audio_accuracy_detects_transcription(self):
        """长音频 + 准确率优先 → 转写场景"""
        selector = EngineSelector()
        ctx = AudioContext(
            duration_seconds=120.0,
            priority="accuracy",
        )
        scenario = selector.detect_scenario(ctx)
        assert scenario == Scenario.TRANSCRIPTION

    def test_default_is_general(self):
        """默认 → 通用场景"""
        selector = EngineSelector()
        ctx = AudioContext()
        scenario = selector.detect_scenario(ctx)
        assert scenario == Scenario.GENERAL


class TestEngineScoring:
    """测试引擎评分"""

    def test_realtime_prefers_streaming(self):
        """实时场景偏好流式引擎"""
        selector = EngineSelector()
        ctx = AudioContext(is_streaming=True)

        result = selector.select(ctx)

        # 流式场景应该选择 nano-2512（唯一支持流式的引擎）
        assert result.recommended_engine == "nano-2512"

    def test_chinese_transcription_prefers_sensevoice(self):
        """中文转写偏好高准确率引擎"""
        selector = EngineSelector()
        # 设置高准确率优先
        ctx = AudioContext(
            duration_seconds=120.0,
            language_hint="zh",
            priority="accuracy",
        )
        result = selector.select(ctx, priority="accuracy")

        # 准确率优先时，优先选择高准确率引擎
        assert result.recommended_engine in ["sensevoice", "paraformer-zh", "nano-2512"]

    def test_meeting_prefers_diarization(self):
        """会议场景偏好支持说话人分离的引擎"""
        selector = EngineSelector()
        ctx = AudioContext(
            duration_seconds=3600.0,
            estimated_speakers=3,
        )

        result = selector.select(ctx)

        # 会议场景应该选择支持 diarization 的引擎
        assert result.recommended_engine in ["paraformer-zh", "moss"]

    def test_multilingual_prefers_many_languages(self):
        """多语言场景偏好支持语言多的引擎"""
        selector = EngineSelector()
        ctx = AudioContext(
            duration_seconds=60.0,
            language_hint="multi",
        )

        result = selector.select(ctx)

        # 多语言场景应该选择支持语言多的引擎
        assert result.recommended_engine in ["nano-2512", "sensevoice"]

    def test_result_has_fallback(self):
        """选择结果包含回退引擎"""
        selector = EngineSelector()
        ctx = AudioContext()
        result = selector.select(ctx)

        assert result.fallback_engine is not None
        assert result.fallback_engine != result.recommended_engine

    def test_result_has_confidence(self):
        """选择结果包含置信度"""
        selector = EngineSelector()
        ctx = AudioContext()
        result = selector.select(ctx)

        assert 0.0 <= result.confidence <= 1.0

    def test_result_has_score(self):
        """选择结果包含评分"""
        selector = EngineSelector()
        ctx = AudioContext()
        result = selector.select(ctx)

        assert isinstance(result.score, EngineScore)
        assert result.score.engine_name == result.recommended_engine


class TestEngineSelectorExplain:
    """测试选择解释"""

    def test_explain_selection(self):
        """测试选择解释生成"""
        selector = EngineSelector()
        ctx = AudioContext(is_streaming=True)
        result = selector.select(ctx)

        explanation = selector.explain_selection(result)

        assert "推荐引擎" in explanation
        assert result.recommended_engine in explanation
        assert "置信度" in explanation
        assert "场景" in explanation


class TestEngineCapabilities:
    """测试引擎能力查询"""

    def test_get_engine_info(self):
        """测试获取引擎信息"""
        selector = EngineSelector()
        info = selector.get_engine_info("nano-2512")

        assert "latency" in info
        assert "accuracy" in info
        assert "streaming" in info
        assert info["streaming"] is True

    def test_get_unknown_engine_info(self):
        """测试获取未知引擎信息"""
        selector = EngineSelector()
        info = selector.get_engine_info("unknown")

        assert info == {}

    def test_list_engines(self):
        """测试列出所有引擎"""
        selector = EngineSelector()
        engines = selector.list_engines()

        assert len(engines) == len(selector.ENGINE_CAPABILITIES)
        for engine in engines:
            assert "name" in engine
            assert engine["name"] in selector.ENGINE_CAPABILITIES


class TestEngineSelectorPriority:
    """测试优先级参数"""

    def test_latency_priority(self):
        """延迟优先参数"""
        selector = EngineSelector()
        ctx = AudioContext(priority="latency")
        result = selector.select(ctx, priority="latency")

        assert result.recommended_engine == "nano-2512"

    def test_accuracy_priority(self):
        """准确率优先参数"""
        selector = EngineSelector()
        ctx = AudioContext(priority="accuracy")
        result = selector.select(ctx, priority="accuracy")

        # 准确率优先应该选择高准确率引擎之一
        assert result.recommended_engine in ["sensevoice", "paraformer-zh", "nano-2512"]

    def test_balanced_priority(self):
        """平衡优先参数"""
        selector = EngineSelector()
        ctx = AudioContext(priority="balanced")
        result = selector.select(ctx, priority="balanced")

        assert result.recommended_engine in selector._available_engines


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
