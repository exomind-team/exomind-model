# Voice-IME SenseVoiceSmall 支持规范

> **Spec ID**: spec-011-sensevoice
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-002-funasr-integration

## 1. 概述

本文档定义 Voice-IME 对 SenseVoiceSmall 模型的支持规范。

**SenseVoiceSmall** 是阿里达摩院开源的高精度多语言语音理解模型，具备以下特性：
- ASR（语音识别）+ LID（语言检测）+ SER（情感识别）+ AED（事件检测）
- 330M 参数，中文为主，支持 5 种语言
- 高准确率，适合离线转写场景

## 2. 模型特性

### 2.1 支持的功能

| 功能 | 支持状态 | 说明 |
|------|----------|------|
| 语音识别 (ASR) | ✅ | 核心功能 |
| 语言检测 (LID) | ✅ | 自动检测语种 |
| 情感识别 (SER) | ✅ | 4种情感类别 |
| 说话人分离 | ❌ | 不支持 |
| 流式识别 | ❌ | 不支持 |
| 时间戳 | ❌ | 不支持 |

### 2.2 支持的语言

| 语言 | 代码 | 支持状态 |
|------|------|----------|
| 中文 | zh | ✅ 默认 |
| 英文 | en | ✅ |
| 日文 | ja | ✅ |
| 韩文 | ko | ✅ |
| 粤文 | yue | ✅ |

### 2.3 性能指标

| 指标 | 数值 | 说明 |
|------|------|------|
| 参数量 | 330M | 中等大小 |
| RTF | 0.4x | 2.5倍速实时 |
| 准确率 | 95/100 | 高精度 |
| 内存占用 | ~2GB | 模型加载后 |

## 3. 架构设计

### 3.1 集成方式

```
voice_ime.py
    │
    ▼
ASRClientFactory.create_with_fallback()
    │
    ▼
FunASRClient (model='sensevoice')
    │
    ▼
AutoModel(SenseVoiceSmall) + VAD + PUNC
```

### 3.2 输出格式

SenseVoice 输出包含特殊标记，示例：

```
<|zh|><|NEUTRAL|><|Speech|><|woitn|><|wav|><|nes|><|5.89|><|0.0|>这是识别文本。
```

**清理规则**：

| 标记 | 含义 | 处理 |
|------|------|------|
| `<\|zh\|>` | 中文 | 移除 |
| `<\|en\|>` | 英文 | 移除 |
| `<\|ja\|>` | 日文 | 移除 |
| `<\|ko\|>` | 韩文 | 移除 |
| `<\|yue\|>` | 粤文 | 移除 |
| `<\|NEUTRAL\|>` | 中性情感 | 移除 |
| `<\|SPEECH\|>` | 语音类型 | 移除 |
| `<\|woitn\|>` | 未知 | 移除 |
| `<\|wav\|>` | 音频类型 | 移除 |
| `<\|nes\|>` | 未知 | 移除 |
| `<\|5.89\|>` | 置信度 | 移除 |
| `<\|0.0\|>` | 时间戳 | 移除 |

**清理结果**：`这是识别文本。`

## 4. 接口设计

### 4.1 使用方式

```bash
# 命令行使用
python voice_ime.py --asr funasr --funasr-model sensevoice

# 智能选择模式（自动选择）
python voice_ime.py --smart --priority accuracy
```

### 4.2 引擎名称映射

| 内部名称 | 模型 ID | 说明 |
|----------|---------|------|
| `sensevoice` | `SenseVoiceSmall` | FunASR 1.3.1 格式 |

## 5. 输出处理

### 5.1 文本清理实现

```python
import re

def clean_sensevoice_output(text: str) -> str:
    """
    清理 SenseVoice 输出文本

    Args:
        text: 原始输出

    Returns:
        清理后的纯文本
    """
    # 移除所有 <|xxx|> 格式的标签
    text = re.sub(r'<\|[^|]+\|>', '', text)
    # 移除多余空白
    text = re.sub(r'\s+', ' ', text)
    # 去除首尾空白
    return text.strip()
```

### 5.2 情感信息提取

SenseVoice 返回结果示例：

```python
{
    "text": "<|zh|><|NEUTRAL|>你好世界",
    "labels": [
        {"label": "NEUTRAL", "score": 0.95},
        {"label": "HAPPY", "score": 0.03},
        {"label": "ANGRY", "score": 0.01},
        {"label": "SAD", "score": 0.01},
    ]
}
```

**情感映射**：

| SenseVoice 标签 | 含义 |
|-----------------|------|
| NEUTRAL | 中性 |
| HAPPY | 开心 |
| ANGRY | 生气 |
| SAD | 悲伤 |

## 6. 测试用例

### 6.1 单元测试

| 用例 | 输入 | 期望输出 |
|------|------|----------|
| 纯中文 | `<\|zh\|>你好世界` | `你好世界` |
| 带情感 | `<\|zh\|><\|NEUTRAL\|>测试` | `测试` |
| 英文 | `<\|en\|>Hello World` | `Hello World` |
| 多语言混合 | `<\|zh\|><\|en\|>你好Hello` | `你好Hello` |

### 6.2 集成测试

- [ ] FunASRClient 可以正确加载 sensevoice 模型
- [ ] transcribe() 返回清理后的纯文本
- [ ] 智能选择器正确评估 sensevoice 能力
- [ ] CLI 参数 --funasr-model sensevoice 正常工作

## 7. 与其他引擎对比

| 引擎 | 准确率 | 延迟 | 语言数 | 说话人分离 | 适用场景 |
|------|--------|------|--------|------------|----------|
| **sensevoice** | 95 | 中 | 5 | ❌ | 高精度转写 |
| paraformer-zh | 90 | 中 | 1 | ✅ | 通用中文 |
| nano-2512 | 80 | 低 | 31 | ❌ | 实时流式 |
| moss | 88 | 低 | 1 | ✅ | 云端备用 |

## 8. 验收标准

- [ ] `--asr funasr --funasr-model sensevoice` 正常工作
- [ ] 输出文本不包含 `<|...|>` 标记
- [ ] 智能选择器能正确推荐 sensevoice（准确率优先场景）
- [ ] 单元测试覆盖 > 80%
- [ ] 文档完整

## 9. 后续扩展

- [ ] 情感信息作为 ASRResult 的一部分返回
- [ ] 语言检测结果作为元数据返回
- [ ] 支持 sensevoice 的时间戳输出（未来版本）

---

*本文档遵循 Voice-IME Spec 规范*
