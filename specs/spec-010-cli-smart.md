# Voice-IME CLI 增强规范

> **Spec ID**: spec-010-cli-smart
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-009-engine-selector

## 1. 概述

本文档定义 Voice-IME 命令行界面的智能选择增强，支持根据场景自动选择最佳 ASR 引擎。

## 2. 设计目标

- **智能模式**：使用 `EngineSelector` 自动选择引擎
- **透明可解释**：显示选择原因和置信度
- **灵活控制**：支持手动指定场景和优先级
- **向后兼容**：保持现有参数不变

## 3. 新增命令行参数

### 3.1 智能选择参数

```bash
# 启用智能选择模式
voice-ime --smart

# 智能选择 + 显示选择解释
voice-ime --smart --explain

# 智能选择 + 指定场景
voice-ime --smart --scenario meeting

# 智能选择 + 指定优先级
voice-ime --smart --priority latency

# 组合使用
voice-ime --smart --explain --scenario realtime
```

### 3.2 参数详情

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--smart`, `-s` | 启用智能选择模式 | false |
| `--explain`, `-e` | 显示引擎选择解释 | false |
| `--scenario` | 强制指定场景 | auto |
| `--priority` | 优先考虑 (latency/accuracy/balanced) | balanced |

### 3.3 场景值

| 场景 | 说明 |
|------|------|
| `realtime` | 实时语音输入（低延迟优先） |
| `transcription` | 离线转写（准确率优先） |
| `meeting` | 会议记录（说话人分离） |
| `multilingual` | 多语言场景 |
| `command` | 语音命令（短文本） |
| `general` | 通用场景（平衡选择） |

## 4. 使用示例

### 4.1 基本智能选择

```bash
# 自动根据场景选择最佳引擎
voice-ime --smart

# 输出示例:
# 🎯 智能选择: nano-2512
# 📊 置信度: 85.0%
# 📋 场景: REALTIME (流式输入检测)
#    • 原生流式支持，低延迟
# 🔄 备选: paraformer-zh, moss
```

### 4.2 会议场景

```bash
# 会议记录，自动选择支持说话人分离的引擎
voice-ime --smart --scenario meeting --explain

# 输出示例:
# 🎯 智能选择: paraformer-zh
# 📊 置信度: 72.0%
# 📋 场景: MEETING (多说话人检测)
#    • 支持说话人分离
# 🔄 备选: moss
```

### 4.3 高准确率转写

```bash
# 长文本转写，准确率优先
voice-ime --smart --priority accuracy

# 输出示例:
# 🎯 智能选择: sensevoice
# 📊 置信度: 68.0%
# 📋 场景: TRANSCRIPTION (长音频 + 准确率优先)
#    • 高精度模型
```

## 5. 架构设计

### 5.1 流程图

```
┌──────────────────┐
│   命令行参数解析  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│   --smart ?      │────►│  创建 AudioContext│
└────────┬─────────┘     │  (从参数推断场景) │
         │               └────────┬─────────┘
         ▼                        ▼
┌──────────────────┐     ┌──────────────────┐
│   传统模式       │     │  EngineSelector  │
│ (--asr 指定引擎) │◄────│  .select()       │
└──────────────────┘     └────────┬─────────┘
                                  │
                                  ▼
                         ┌──────────────────┐
                         │ create_smart()   │
                         │ 返回 client +    │
                         │ selection_result │
                         └──────────────────┘
```

### 5.2 核心代码

```python
def parse_args():
    parser = argparse.ArgumentParser(...)

    # 新增智能选择参数
    parser.add_argument(
        '--smart', '-s',
        action='store_true',
        help='启用智能选择模式（自动选择最佳引擎）'
    )
    parser.add_argument(
        '--explain', '-e',
        action='store_true',
        help='显示引擎选择解释'
    )
    parser.add_argument(
        '--scenario',
        choices=['realtime', 'transcription', 'meeting',
                 'multilingual', 'command', 'general'],
        help='强制指定场景类型'
    )
    parser.add_argument(
        '--priority',
        choices=['latency', 'accuracy', 'balanced'],
        default='balanced',
        help='优先考虑因素 (默认: balanced)'
    )

    return parser.parse_args()


def main():
    args = parse_args()

    if args.smart:
        # 智能选择模式
        context = AudioContext(
            duration_seconds=0.0,  # 实时录音未知时长
            estimated_speakers=1,
            language_hint="auto",
            is_streaming=True,
            priority=args.priority or "balanced",
        )

        if args.scenario:
            context = override_scenario(context, args.scenario)

        client, result = ASRClientFactory.create_smart(context, explain=args.explain)

        print(f"🏭 使用引擎: {client.name}")
        if args.explain:
            print(f"📊 选择置信度: {result.confidence:.1%}")
```

## 6. 输出格式

### 6.1 智能选择输出

```
🎤 VoiceIME 语音输入工具
============================================================

📌 快捷键: F2
   - 第一次按下: 开始录音
   - 第二次按下: 自动识别并输入

🎯 智能选择模式已启用
📊 置信度: 85.0%
📋 场景: REALTIME
   • 原生流式支持，低延迟
🔄 备选引擎: paraformer-zh, moss

🏭 ASR 引擎: Fun-ASR-Nano-2512

📁 临时文件目录: /home/user/.voice_ime/temp

💡 提示: 按 ESC 可退出程序

🛋️  等待录音 (按 F2 开始)
```

## 7. 验收标准

- [ ] `--smart` 参数启用智能选择
- [ ] `--explain` 参数显示选择解释
- [ ] `--scenario` 参数强制指定场景
- [ ] `--priority` 参数设置优先考虑
- [ ] 向后兼容现有 `--asr` 参数
- [ ] 单元测试覆盖 > 80%
- [ ] 集成测试验证 E2E 流程

## 8. 后续扩展

- [ ] 保存用户偏好（~/.voice_ime/preferences.yaml）
- [ ] 基于历史使用学习用户偏好
- [ ] A/B 测试支持不同选择策略

---

*本文档遵循 Voice-IME Spec 规范*
