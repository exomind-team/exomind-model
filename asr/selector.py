"""
ASR Engine Selector
===================

智能引擎选择器。根据场景自动选择最佳 ASR 引擎。

支持根据以下因素智能决策：
- 实时性要求（流式输入）
- 准确率要求（离线转写）
- 说话人分离需求（会议场景）
- 多语言支持
- 资源消耗限制
"""

from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path


class Scenario(Enum):
    """语音识别场景类型"""
    REALTIME = auto()          # 实时语音输入（低延迟优先）
    TRANSCRIPTION = auto()     # 离线转写（准确率优先）
    MEETING = auto()           # 会议记录（说话人分离）
    MULTILINGUAL = auto()      # 多语言场景
    COMMAND = auto()           # 语音命令（短文本）
    GENERAL = auto()           # 通用场景（平衡选择）


@dataclass
class AudioContext:
    """音频上下文（用于场景判断）

    Attributes:
        audio_path: 音频文件路径
        duration_seconds: 音频时长（秒）
        estimated_speakers: 预估说话人数
        language_hint: 语言提示 ("zh", "en", "multi", "auto")
        is_streaming: 是否流式输入
        priority: 优先考虑 ("latency", "accuracy", "balanced")
    """
    audio_path: Optional[Path] = None
    duration_seconds: float = 0.0
    estimated_speakers: int = 1
    language_hint: str = "auto"
    is_streaming: bool = False
    priority: str = "balanced"


@dataclass
class EngineScore:
    """引擎评分"""
    engine_name: str
    total_score: float = 0.0
    latency_score: float = 0.0      # 0-100
    accuracy_score: float = 0.0     # 0-100
    resource_score: float = 0.0     # 0-100
    feature_score: float = 0.0      # 0-100
    reasons: List[str] = field(default_factory=list)


@dataclass
class SelectionResult:
    """选择结果"""
    recommended_engine: str
    fallback_engine: str
    scenario: Scenario
    score: EngineScore
    confidence: float = 0.0         # 0-1
    alternatives: List[str] = field(default_factory=list)


class EngineSelector:
    """智能引擎选择器

    根据音频上下文和场景，自动选择最佳 ASR 引擎。
    """

    # 引擎能力定义
    ENGINE_CAPABILITIES: Dict[str, Dict[str, Any]] = {
        'nano-2512': {
            'latency': 95,       # 极低延迟
            'accuracy': 80,      # 基础准确率
            'resource': 70,      # 中等资源消耗
            'streaming': True,
            'diarization': False,
            'languages': 31,
            'model_names': ['nano-2512', 'nano-mlt'],
        },
        'paraformer-zh': {
            'latency': 50,
            'accuracy': 90,
            'resource': 60,
            'streaming': False,
            'diarization': True,
            'languages': 1,
            'model_names': ['paraformer-zh'],
        },
        'sensevoice': {
            'latency': 40,
            'accuracy': 95,
            'resource': 50,
            'streaming': False,
            'diarization': False,
            'languages': 5,
            'model_names': ['sensevoice'],
        },
        'moss': {
            'latency': 30,
            'accuracy': 88,
            'resource': 100,     # 云端无本地资源消耗
            'streaming': False,
            'diarization': True,
            'languages': 1,
            'model_names': ['moss-transcribe-diarize'],
        },
    }

    # 场景权重配置 (latency, accuracy, resource)
    SCENARIO_WEIGHTS: Dict[Scenario, Dict[str, float]] = {
        Scenario.REALTIME: {'latency': 0.5, 'accuracy': 0.3, 'resource': 0.2},
        Scenario.TRANSCRIPTION: {'latency': 0.2, 'accuracy': 0.6, 'resource': 0.2},
        Scenario.MEETING: {'latency': 0.3, 'accuracy': 0.4, 'resource': 0.3},
        Scenario.MULTILINGUAL: {'latency': 0.3, 'accuracy': 0.4, 'resource': 0.3},
        Scenario.COMMAND: {'latency': 0.6, 'accuracy': 0.3, 'resource': 0.1},
        Scenario.GENERAL: {'latency': 0.3, 'accuracy': 0.4, 'resource': 0.3},
    }

    # 引擎回退映射
    FALLBACK_CHAIN: Dict[str, List[str]] = {
        'nano-2512': ['paraformer-zh', 'moss'],
        'paraformer-zh': ['sensevoice', 'moss'],
        'sensevoice': ['paraformer-zh', 'moss'],
        'moss': ['paraformer-zh'],  # 云端失败则用本地
    }

    def __init__(self, available_engines: Optional[List[str]] = None):
        """
        初始化选择器

        Args:
            available_engines: 可用引擎列表（None 表示全部）
        """
        if available_engines is None:
            self._available_engines: List[str] = list(self.ENGINE_CAPABILITIES.keys())
        else:
            self._available_engines: List[str] = [
                e for e in available_engines
                if e in self.ENGINE_CAPABILITIES
            ]

    def select(
        self,
        context: AudioContext,
        priority: Optional[str] = None,
    ) -> SelectionResult:
        """智能选择最佳引擎

        Args:
            context: 音频上下文
            priority: 优先考虑 ("latency", "accuracy", "balanced")

        Returns:
            SelectionResult: 选择结果
        """
        # 检测场景
        scenario = self.detect_scenario(context)

        # 获取权重
        if priority and priority != 'auto':
            weights = self._get_priority_weights(priority)
        else:
            weights = self.SCENARIO_WEIGHTS[scenario]

        # 评分所有可用引擎
        scores: List[tuple[str, EngineScore]] = []
        for engine in self._available_engines:
            score = self._score_engine(engine, scenario, context, weights)
            scores.append((engine, score))

        # 按总分排序
        scores.sort(key=lambda x: x[1].total_score, reverse=True)

        if not scores:
            # 无可用引擎，返回默认
            return SelectionResult(
                recommended_engine='paraformer-zh',
                fallback_engine='moss',
                scenario=Scenario.GENERAL,
                confidence=0.0,
                score=EngineScore(engine_name='none'),
                alternatives=[],
            )

        # 选择最佳引擎
        best_engine, best_score = scores[0]
        fallback = self.FALLBACK_CHAIN.get(best_engine, ['moss'])[0]

        # 计算置信度
        if len(scores) > 1:
            confidence = (best_score.total_score - scores[1][1].total_score) / 100
            confidence = max(0.0, min(1.0, confidence))
        else:
            confidence = 1.0

        return SelectionResult(
            recommended_engine=best_engine,
            fallback_engine=fallback,
            scenario=scenario,
            confidence=confidence,
            score=best_score,
            alternatives=[e for e, _ in scores[1:4]],  # 前3备选
        )

    def detect_scenario(self, context: AudioContext) -> Scenario:
        """检测场景类型

        Args:
            context: 音频上下文

        Returns:
            Scenario: 检测到的场景类型
        """
        # 1. 流式输入 → 实时场景
        if context.is_streaming:
            return Scenario.REALTIME

        # 2. 多语言提示 → 多语言场景
        if context.language_hint in ('en', 'multi'):
            return Scenario.MULTILINGUAL

        # 3. 短音频 + 高延迟敏感 → 命令场景
        if context.duration_seconds < 5 and context.priority == 'latency':
            return Scenario.COMMAND

        # 4. 多说话人 → 会议场景
        if context.estimated_speakers > 1:
            return Scenario.MEETING

        # 5. 长音频 + 高准确率优先 → 转写场景
        if context.duration_seconds > 60 and context.priority == 'accuracy':
            return Scenario.TRANSCRIPTION

        # 6. 默认通用场景
        return Scenario.GENERAL

    def _score_engine(
        self,
        engine: str,
        scenario: Scenario,
        context: AudioContext,
        weights: Dict[str, float],
    ) -> EngineScore:
        """评分单个引擎

        Args:
            engine: 引擎名称
            scenario: 场景类型
            context: 音频上下文
            weights: 权重配置

        Returns:
            EngineScore: 引擎评分
        """
        capabilities = self.ENGINE_CAPABILITIES.get(engine, {})

        # 基础分数
        latency_score = capabilities.get('latency', 0)
        accuracy_score = capabilities.get('accuracy', 0)
        resource_score = capabilities.get('resource', 0)
        reasons: List[str] = []

        # 场景特定调整
        if scenario == Scenario.REALTIME:
            if not capabilities.get('streaming', False):
                latency_score *= 0.1  # 非流式引擎扣分严重
                reasons.append("不支持流式输入")
            else:
                reasons.append("原生流式支持，低延迟")

        if scenario == Scenario.MEETING:
            if not capabilities.get('diarization', False):
                accuracy_score *= 0.5  # 无说话人分离扣分
                reasons.append("不支持说话人分离")
            else:
                reasons.append("支持说话人分离")

        if scenario == Scenario.MULTILINGUAL:
            lang_count = capabilities.get('languages', 1)
            if lang_count < 5:
                accuracy_score *= 0.7
                reasons.append(f"仅支持 {lang_count} 种语言")
            else:
                reasons.append(f"支持 {lang_count} 种语言")

        if scenario == Scenario.TRANSCRIPTION:
            if capabilities.get('accuracy', 0) >= 90:
                reasons.append("高精度模型")

        if scenario == Scenario.COMMAND:
            if capabilities.get('latency', 0) >= 80:
                reasons.append("低延迟响应")

        # 语言特定调整
        if context.language_hint == 'zh':
            if capabilities.get('languages', 0) >= 1:
                accuracy_score *= 1.1  # 中文优化
                reasons.append("中文优化")

        if context.language_hint == 'en':
            model_names = capabilities.get('model_names', [])
            if 'en' in model_names or 'paraformer-en' in model_names:
                accuracy_score *= 1.1
                reasons.append("英文支持")

        # 计算加权总分
        total_score = (
            latency_score * weights['latency'] +
            accuracy_score * weights['accuracy'] +
            resource_score * weights['resource']
        )

        return EngineScore(
            engine_name=engine,
            total_score=total_score,
            latency_score=latency_score,
            accuracy_score=accuracy_score,
            resource_score=resource_score,
            feature_score=0,
            reasons=reasons,
        )

    def _get_priority_weights(self, priority: str) -> Dict[str, float]:
        """获取优先级的权重配置"""
        if priority == 'latency':
            return {'latency': 0.6, 'accuracy': 0.3, 'resource': 0.1}
        elif priority == 'accuracy':
            return {'latency': 0.2, 'accuracy': 0.7, 'resource': 0.1}
        else:  # balanced
            return {'latency': 0.4, 'accuracy': 0.4, 'resource': 0.2}

    def explain_selection(self, result: SelectionResult) -> str:
        """生成选择解释

        Args:
            result: 选择结果

        Returns:
            str: 人类可读的解释
        """
        lines = [
            f"推荐引擎: {result.recommended_engine}",
            f"置信度: {result.confidence:.1%}",
            f"场景: {result.scenario.name}",
            "",
            "评分详情:",
            f"   延迟: {result.score.latency_score:.0f}/100",
            f"   准确率: {result.score.accuracy_score:.0f}/100",
            f"   资源效率: {result.score.resource_score:.0f}/100",
            "",
            "选择原因:",
        ]

        if result.score.reasons:
            for reason in result.score.reasons:
                lines.append(f"   - {reason}")
        else:
            lines.append("   - 平衡选择")

        if result.alternatives:
            lines.append("")
            lines.append(f"备选引擎: {', '.join(result.alternatives)}")

        return "\n".join(lines)

    def get_engine_info(self, engine: str) -> Dict[str, Any]:
        """获取引擎信息

        Args:
            engine: 引擎名称

        Returns:
            dict: 引擎信息
        """
        return self.ENGINE_CAPABILITIES.get(engine, {})

    def list_engines(self) -> List[Dict[str, Any]]:
        """列出所有引擎信息"""
        return [
            {
                'name': name,
                **info,
            }
            for name, info in self.ENGINE_CAPABILITIES.items()
        ]
