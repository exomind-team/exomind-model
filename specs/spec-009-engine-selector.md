# Voice-IME 智能引擎选择器规范

> **Spec ID**: spec-009-engine-selector
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-001-config, spec-008-asr-streaming

## 1. 概述

本文档定义 Voice-IME 项目的智能引擎选择器（Engine Selector），支持根据场景自动选择最佳 ASR 引擎。

## 2. 设计目标

- **场景感知**：根据音频特性自动选择最佳引擎
- **多维度决策**：实时性、准确率、资源消耗、语言支持
- **透明可解释**：记录选择原因，支持用户干预
- **向后兼容**：保持现有 API 兼容

## 3. 架构设计

### 3.1 引擎能力矩阵

| 引擎 | 类型 | 语言 | 延迟 | 准确率 | 说话人分离 | 适用场景 |
|------|------|------|------|--------|-----------|---------|
| **nano-2512** | 本地 | 31种 | <600ms | ⭐⭐⭐ | ❌ | 实时语音输入、会议 |
| **paraformer-zh** | 本地 | 中文 | 离线 | ⭐⭐⭐⭐ | ✅ | 离线转写、字幕 |
| **sensevoice** | 本地 | 多语言 | 离线 | ⭐⭐⭐⭐⭐ | ❌ | 高精度转写 |
| **moss** | 云端 | 中文 | 网络 | ⭐⭐⭐⭐ | ✅ | 云端处理、API 备用 |

### 3.2 场景类型

```python
from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional
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
    """音频上下文（用于场景判断）"""
    audio_path: Optional[Path] = None
    duration_seconds: float = 0.0
    estimated_speakers: int = 1
    language_hint: str = "auto"  # "zh", "en", "multi", "auto"
    is_streaming: bool = False   # 是否流式输入
    priority: str = "balanced"   # "latency", "accuracy", "auto"
```

### 3.3 引擎评分系统

```python
@dataclass
class EngineScore:
    """引擎评分"""
    engine_name: str
    total_score: float
    latency_score: float      # 0-100
    accuracy_score: float     # 0-100
    resource_score: float     # 0-100
    feature_score: float      # 0-100
    reasons: list[str]        # 选择原因

@dataclass
class SelectionResult:
    """选择结果"""
    recommended_engine: str
    fallback_engine: str
    scenario: Scenario
    confidence: float         # 0-1
    score: EngineScore
    alternatives: list[str]
```

### 3.4 EngineSelector 类

```python
class EngineSelector:
    """智能引擎选择器"""

    # 引擎能力定义
    ENGINE_CAPABILITIES = {
        'nano-2512': {
            'latency': 95,       # 极低延迟
            'accuracy': 80,      # 基础准确率
            'resource': 70,      # 中等资源
            'streaming': True,
            'diarization': False,
            'languages': 31,
            'models': ['nano-2512', 'nano-mlt'],
        },
        'paraformer-zh': {
            'latency': 50,
            'accuracy': 90,
            'resource': 60,
            'streaming': False,
            'diarization': True,
            'languages': 1,
            'models': ['paraformer-zh'],
        },
        'sensevoice': {
            'latency': 40,
            'accuracy': 95,
            'resource': 50,
            'streaming': False,
            'diarization': False,
            'languages': 5,
            'models': ['sensevoice'],
        },
        'moss': {
            'latency': 30,
            'accuracy': 88,
            'resource': 100,     # 云端无本地资源
            'streaming': False,
            'diarization': True,
            'languages': 1,
            'models': ['moss-transcribe-diarize'],
        },
    }

    # 场景权重配置
    SCENARIO_WEIGHTS = {
        Scenario.REALTIME: {'latency': 0.5, 'accuracy': 0.3, 'resource': 0.2},
        Scenario.TRANSCRIPTION: {'latency': 0.2, 'accuracy': 0.6, 'resource': 0.2},
        Scenario.MEETING: {'latency': 0.3, 'accuracy': 0.4, 'resource': 0.3},
        Scenario.MULTILINGUAL: {'latency': 0.3, 'accuracy': 0.4, 'resource': 0.3},
        Scenario.COMMAND: {'latency': 0.6, 'accuracy': 0.3, 'resource': 0.1},
        Scenario.GENERAL: {'latency': 0.3, 'accuracy': 0.4, 'resource': 0.3},
    }

    def select(
        self,
        context: AudioContext,
        available_engines: list[str] = None,
    ) -> SelectionResult:
        """智能选择最佳引擎

        Args:
            context: 音频上下文
            available_engines: 可用引擎列表（None 表示全部）

        Returns:
            SelectionResult: 选择结果
        """
        ...

    def detect_scenario(self, context: AudioContext) -> Scenario:
        """检测场景类型"""
        ...

    def score_engine(
        self,
        engine: str,
        scenario: Scenario,
        context: AudioContext,
    ) -> EngineScore:
        """评分单个引擎"""
        ...

    def explain_selection(self, result: SelectionResult) -> str:
        """生成选择解释"""
        ...
```

### 3.5 场景检测逻辑

```python
def detect_scenario(self, context: AudioContext) -> Scenario:
    """检测场景类型"""

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
```

### 3.6 评分计算

```python
def score_engine(
    self,
    engine: str,
    scenario: Scenario,
    context: AudioContext,
) -> EngineScore:
    """评分单个引擎"""

    capabilities = self.ENGINE_CAPABILITIES.get(engine, {})
    weights = self.SCENARIO_WEIGHTS[scenario]

    # 基础分数
    latency_score = capabilities.get('latency', 0)
    accuracy_score = capabilities.get('accuracy', 0)
    resource_score = capabilities.get('resource', 0)

    # 场景特定调整
    if scenario == Scenario.REALTIME:
        if not capabilities.get('streaming'):
            latency_score *= 0.1  # 非流式引擎扣分严重

    if scenario == Scenario.MEETING:
        if not capabilities.get('diarization'):
            accuracy_score *= 0.5  # 无说话人分离扣分

    if scenario == Scenario.MULTILINGUAL:
        if capabilities.get('languages', 1) < 5:
            accuracy_score *= 0.7  # 少语言支持扣分

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
        feature_score=0,  # 待实现
        reasons=[],
    )
```

## 4. 使用示例

### 4.1 基本使用

```python
from asr import EngineSelector, AudioContext, Scenario

selector = EngineSelector()

# 检测场景并选择
context = AudioContext(
    duration_seconds=30.0,
    language_hint="zh",
)
result = selector.select(context)

print(f"推荐引擎: {result.recommended_engine}")
print(f"选择原因: {result.score.reasons}")
```

### 4.2 流式场景

```python
# 流式输入 → 自动选择 nano-2512
context = AudioContext(
    is_streaming=True,
    duration_seconds=0.0,
)
result = selector.select(context)
assert result.recommended_engine == 'nano-2512'
```

### 4.3 会议场景（多说话人）

```python
# 会议记录 → 选择支持说话人分离的引擎
context = AudioContext(
    duration_seconds=3600.0,
    estimated_speakers=3,
    language_hint="zh",
)
result = selector.select(context)
# 推荐: paraformer-zh (本地) 或 moss (云端)
```

### 4.4 多语言场景

```python
# 多语言 → 选择支持语言多的引擎
context = AudioContext(
    duration_seconds=60.0,
    language_hint="multi",
)
result = selector.select(context)
# 推荐: nano-2512 (31种语言)
```

## 5. 配置集成

### 5.1 config.yaml

```yaml
asr:
  # 智能选择配置
  smart_selection:
    enabled: true           # 启用智能选择
    explain: true           # 显示选择原因
    allow_override: true    # 允许用户覆盖

  # 场景映射
  scenario_mapping:
    streaming: "nano-2512"
    meeting: "funasr"
    transcription: "sensevoice"
    multilingual: "nano-2512"

  # 引擎优先级（权重）
  engine_priority:
    latency_first: ["nano-2512", "paraformer-zh", "moss"]
    accuracy_first: ["sensevoice", "paraformer-zh", "moss"]
    balanced: ["paraformer-zh", "nano-2512", "moss"]
```

### 5.2 环境变量

```bash
# 禁用智能选择
VOICE_IME_SMART_SELECTION=false

# 设置首选引擎
VOICE_IME_PREFERRED_ENGINE=nano-2512

# 强制使用指定引擎
VOICE_IME_FORCE_ENGINE=nano-2512
```

### 5.3 命令行参数

```bash
# 显示选择解释
voice-ime --explain-engine

# 禁用智能选择
voice-ime --no-smart-select

# 强制使用指定引擎
voice-ime --engine nano-2512

# 设置场景模式
voice-ime --scenario meeting
```

## 6. 增强 ASRClientFactory

```python
class ASRClientFactory:
    """ASR 客户端工厂（增强版，支持智能选择）"""

    @classmethod
    def create_smart(
        cls,
        context: AudioContext,
        explain: bool = False,
        **kwargs
    ) -> ASRClient:
        """
        智能创建 ASR 客户端

        Args:
            context: 音频上下文
            explain: 是否显示选择解释
            **kwargs: 引擎特定配置

        Returns:
            ASRClient 实例
        """
        selector = EngineSelector()
        result = selector.select(context)

        if explain:
            print(f"🎯 智能选择: {result.recommended_engine}")
            print(f"📊 置信度: {result.confidence:.2%}")
            for reason in result.score.reasons:
                print(f"   • {reason}")

        return cls.create_with_fallback(
            primary_engine=result.recommended_engine,
            fallback_engine=result.fallback_engine,
            **kwargs
        )
```

## 7. 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 选择延迟 | < 10ms | 场景检测 + 评分时间 |
| 准确率 | > 90% | 与专家选择一致率 |
| 覆盖率 | 100% | 所有场景都能处理 |

## 8. 验收标准

- [ ] EngineSelector 实现场景检测
- [ ] 支持 6 种场景类型
- [ ] 评分系统正确工作
- [ ] ASRClientFactory 支持 create_smart()
- [ ] 单元测试覆盖 > 80%
- [ ] 集成测试验证选择正确性

## 9. 后续扩展

- [ ] 硬件资源检测（GPU/CPU）
- [ ] 用户偏好学习
- [ ] 自定义场景规则
- [ ] A/B 测试支持

---

*本文档遵循 Voice-IME Spec 规范*
