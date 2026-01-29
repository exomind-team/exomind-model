# VoiceIME 项目计划

> **项目**: VoiceIME ASR 引擎重构
> **创建日期**: 2026-01-27
> **状态**: 执行中
> **Ralph Loop**: 激活 (max_iterations: 30)

---

## 项目目标

实现多 ASR 引擎支持（FunASR 本地 + MOSS 云端），支持热切换和自动回退。

## 任务列表

### Phase 1: 基础设施

| ID | 任务 | 状态 | 输出 | 迭代 |
|----|------|------|------|------|
| T-01 | 创建 asr/ 目录结构 | ✅ 完成 | asr/__init__.py, base.py | 1 |
| T-02 | 实现 ASRClient 抽象基类 | ✅ 完成 | asr/base.py | 1 |
| T-03 | 实现 ASRClientFactory 工厂类 | ✅ 完成 | asr/factory.py | 1 |

### Phase 2: 引擎实现

| ID | 任务 | 状态 | 输出 | 迭代 |
|----|------|------|------|------|
| T-04 | 重构 MossClient 适配新接口 | ✅ 完成 | asr/moss_client.py | 1 |
| T-05 | 实现 FunASRClient | ✅ 完成 | asr/funasr_client.py | 1 |
| T-06 | 单元测试 | ✅ 完成 | test_funasr.py | 1 |

### Phase 3: 主程序集成

| ID | 任务 | 状态 | 输出 | 迭代 |
|----|------|------|------|------|
| T-07 | 修改 voice_ime.py 集成引擎选择 | ✅ 完成 | voice_ime.py | 1 |
| T-08 | 更新 .env.example 配置模板 | ✅ 完成 | .env.example | 1 |
| T-09 | 集成测试验证 | ✅ 完成 | 端到端测试 | 1 |
| T-10 | 修复 factory 参数名称 bug | ✅ 完成 | voice_ime.py | 1 |

### 📋 后续任务（外星组件化）

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| T-11 | 声纹识别功能 | ⏳ 待开发 | 注册声纹 → 识别说话人身份 |
| T-12 | 封装为外星组件 | ⏳ 待开发 | 模块化重构，作为外星系统组件 |
| T-13 | 说话人分离优化 | ⏳ 待开发 | 更好的输出格式和后处理 |

### Phase 4: 重构与 TTS 正式模块

| ID | 任务 | 状态 | 输出 | 优先级 |
|----|------|------|------|--------|
| T-10 | 创建 tts/ 目录结构 | ✅ 完成 | tts/__init__.py, base.py | P0 |
| T-10.1 | 设计 TTS 模块架构 Spec | ✅ 完成 | specs/002-tts-architecture.md | P0 |
| T-10.2 | 实现 TTSClient 抽象基类 | ✅ 完成 | tts/base.py | P0 |
| T-10.3 | 实现 TTSClientFactory | ✅ 完成 | tts/factory.py | P0 |
| T-10.4 | 实现 SherpaTTSClient | ✅ 完成 | tts/sherpa_client.py | P0 |
| T-10.5 | 单元测试 | ✅ 完成 | tests/test_tts.py (17 passed) | P0 |
| T-10.6 | 集成测试 | ✅ 完成 | tests/test_tts_integration.py (5/5) | P0 |
| T-11 | 配置管理集中化 | ✅ 完成 | config.yaml, config/ | P0 |
| T-11.1 | 实现 ConfigLoader | ✅ 完成 | config/config.py | P0 |
| T-11.2 | 创建 config.yaml | ✅ 完成 | 默认配置文件 | P0 |
| T-11.3 | 单元测试 | ✅ 完成 | tests/test_config.py (16 passed) | P0 |
| T-11.4 | 集成测试 | ✅ 完成 | tests/test_config_integration.py (5/5) | P0 |
| T-12 | 日志系统结构化 | ✅ 完成 | structlog 集成 | P1 |
| T-13 | 声纹识别功能 | ✅ 完成 | 说话人注册/识别 | P2 |
| T-14 | 说话人分离优化 | ✅ 完成 | FunASR+Diarization | P2 |

### 迭代 5
- **任务**: T-13 (声纹识别功能)
- **状态**: ✅ 完成
- **开始时间**: 2026-01-29
- **完成时间**: 2026-01-29
- **成果**:
  - ✅ CAM++ 声纹识别实现
  - ✅ specs/spec-005-speaker-recognition.md 架构规范
  - ✅ speaker/ 模块 (base.py, factory.py, camplus_client.py)
  - ✅ 单元测试 (18 passed)
  - ✅ 集成测试 (全部 93 passed, 3 skipped)

### 迭代 6 (当前)
- **任务**: T-14 (说话人分离优化)
- **状态**: ✅ 完成
- **开始时间**: 2026-01-29
- **完成时间**: 2026-01-29
- **成果**:
  - ✅ FunASR + CAM++ 说话人分离集成
  - ✅ specs/spec-006-asr-diarization.md 架构规范
  - ✅ asr/result.py (SpeakerSegment, ASRResult)
  - ✅ FunASRClient.recognize() 方法增强
  - ✅ 单元测试 (15 passed, 新增)
  - ✅ 全部测试 (108 passed, +15)

### 后续规划
| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| T-15 | 实时流式 ASR | ⏳ 待开发 | 支持流式输入 |
| T-16 | 多引擎智能选择 | ⏳ 待开发 | 根据场景自动选择引擎 |
| T-17 | 输出格式增强 | ✅ 完成 | JSON/SRT/VTT/LRC/TXT |

### 迭代 7 (当前)
- **任务**: T-17 (输出格式增强)
- **状态**: ✅ 完成
- **开始时间**: 2026-01-29
- **完成时间**: 2026-01-29
- **成果**:
  - ✅ 多格式输出支持 (JSON, SRT, VTT, TXT, LRC)
  - ✅ specs/spec-007-asr-output-formats.md 架构规范
  - ✅ asr/result.py 增强 (export 方法)
  - ✅ 单元测试 (31 passed, 新增)
  - ✅ 全部测试 (139 passed, +31)

### 后续规划

| ID | 任务 | 状态 | 说明 |
|----|------|------|------|
| T-18 | 实时流式 ASR | ✅ 完成 | 支持流式输入 |
| T-19 | 多引擎智能选择 | ✅ 完成 | 根据场景自动选择引擎 |
| T-20 | CLI 智能选择集成 | ✅ 完成 | --smart, --explain, --scenario, --priority 参数 |

### 迭代 10 (当前)
- **任务**: T-20 (CLI 智能选择集成)
- **状态**: ✅ 完成
- **开始时间**: 2026-01-29
- **完成时间**: 2026-01-29
- **成果**:
  - ✅ voice_ime.py 智能选择模式支持
  - ✅ specs/spec-010-cli-smart.md CLI 增强规范
  - ✅ 新增参数: --smart, --explain, --scenario, --priority
  - ✅ ASRClientFactory.create_smart() 集成
  - ✅ 集成测试 (19 passed, 新增)
  - ✅ 全部测试 (186 passed, +19)

### 迭代 11 (当前)
- **任务**: SenseVoiceSmall 输出清理支持
- **状态**: ✅ 完成
- **开始时间**: 2026-01-29
- **完成时间**: 2026-01-29
- **成果**:
  - ✅ specs/spec-011-sensevoice.md 架构规范
  - ✅ asr/funasr_client.py 输出清理方法
  - ✅ _clean_sensevoice_output() 静态方法实现
  - ✅ transcribe() 和 _parse_result() 集成清理
  - ✅ tests/test_sensevoice_cleaning.py (24 passed, 新增)
  - ✅ 全部测试 (220 passed, +24)

### 迭代 9
- **任务**: T-19 (多引擎智能选择)
- **状态**: ✅ 完成
- **开始时间**: 2026-01-29
- **完成时间**: 2026-01-29
- **成果**:
  - ✅ EngineSelector 智能引擎选择器实现
  - ✅ specs/spec-009-engine-selector.md 架构规范
  - ✅ asr/selector.py 模块 (Scenario, AudioContext, EngineScore, SelectionResult, EngineSelector)
  - ✅ ASRClientFactory.create_smart() 智能创建方法
  - ✅ asr/__init__.py 导出新类
  - ✅ 单元测试 (28 passed, 新增)
  - ✅ 全部测试 (167 passed, +18)

### 迭代 8
- **任务**: T-18 (实时流式 ASR)
- **状态**: ✅ 完成
- **开始时间**: 2026-01-29
- **完成时间**: 2026-01-29
- **成果**:
  - ✅ StreamingState 枚举和 StreamingResult 数据类
  - ✅ ASRClient 基类增强（transcribe_streaming, transcribe_chunk）
  - ✅ FunASRNanoClient 流式方法实现
  - ✅ specs/spec-008-asr-streaming.md 架构规范
  - ✅ 单元测试 (10 passed, 新增)
  - ✅ 全部测试 (149 passed, +10)

---

## 决策点记录

### D-01: 架构模式选择
- **决策**: 工厂模式 (Factory Pattern)
- **日期**: 2026-01-27
- **理由**: 扩展性最强，符合开闭原则
- **备选**: 策略模式（扩展性较差）

### D-02: 默认引擎
- **决策**: FunASR 本地优先
- **日期**: 2026-01-27
- **理由**: 零配置，无网络依赖
- **影响**: 新用户无需 API Key 即可使用

### D-03: 回退策略
- **决策**: FunASR 失败 → MOSS 自动回退
- **日期**: 2026-01-27
- **理由**: 用户体验优先
- **限制**: MOSS 失败无可回退

---

## 风险登记

| 风险 | 可能性 | 影响 | 状态 | 缓解措施 |
|------|--------|------|------|---------|
| FunASR 模型加载慢 | 中 | 中 | 监控 | 添加加载提示 |
| AMD GPU 不兼容 | 高 | 低 | 已识别 | 默认 CPU |
| MOSS API 变更 | 低 | 高 | 监控 | 接口抽象隔离 |

---

## 迭代记录

### 迭代 1 (当前)
- **任务**: T-01 ~ T-09 (全部)
- **状态**: 完成
- **开始时间**: 2026-01-27 13:09
- **完成时间**: 2026-01-27 13:40
- **成果**:
  - ✅ 创建 ASR 引擎架构（工厂模式）
  - ✅ 实现 FunASR 本地引擎
  - ✅ 重构 MOSS 云端引擎
  - ✅ 6/6 单元测试通过
  - ✅ FunASR 真实转写测试通过

### 迭代历史
- 无历史迭代

---

## 验收标准

- [x] FunASR 可正常转写（paraformer-zh）
- [x] FunASR 可正常转写（sensevoice）
- [x] MOSS 可正常转写
- [x] 引擎切换生效 (--asr moss|funasr)
- [x] 回退机制生效
- [x] 现有 MOSS 用户无感知

---

> **最后更新**: 2026-01-27 16:00
> **更新人**: 小荷 (添加 FunASR 模型清单)

---

## 📦 FunASR 支持的模型清单

> 数据来源: [FunASR GitHub README](https://github.com/modelscope/FunASR/blob/main/README_zh.md)
> 更新日期: 2026-01-27

### 🎯 语音识别模型 (ASR)

| 模型名称 | 参数 | 语言 | 特点 | 适用场景 |
|---------|------|------|------|---------|
| **Fun-ASR-Nano-2512** | 800M | 31种语言 | 低延迟实时转写，支持方言口音 | 实时会议、多语言场景 |
| **SenseVoiceSmall** | 330M | 中文为主 | 多功能语音理解：ASR+LID+SER+AED | 高精度转写、情感识别 |
| **paraformer-zh** | 220M | 中文 | 带时间戳输出、非实时 | 离线转写、字幕生成 |
| **paraformer-zh-streaming** | 220M | 中文 | 实时流式识别 | 实时语音输入 |
| **paraformer-en** | 220M | 英文 | 英文专用模型 | 英文内容转写 |
| **conformer-en** | 220M | 英文 | 非实时英文识别 | 英文文件转写 |
| **Whisper-large-v3** | 1550M | 多语言 | OpenAI 经典模型，带时间戳 | 高精度多语言 |
| **Whisper-large-v3-turbo** | 809M | 多语言 | 轻量版 Whisper | 资源受限场景 |

### 🔧 辅助模型

| 模型名称 | 参数量 | 功能 |
|---------|--------|------|
| **fsmn-vad** | 0.4M | 语音端点检测 (VAD) |
| **fsmn-kws** | 0.7M | 语音唤醒 (Keyword Spotting) |
| **ct-punc** | 290M | 标点恢复 |
| **fa-zh** | 38M | 字级别时间戳预测 |

### 👤 说话人相关

| 模型名称 | 参数量 | 功能 |
|---------|--------|------|
| **cam++** | 7.2M | 说话人确认/分离 (Speaker Diarization) |

### 💡 情感识别 (SER)

| 模型名称 | 参数量 | 语言 |
|---------|--------|------|
| **emotion2vec+large** | 300M | 4种情感类别 (angry/happy/neutral/sad) |

### 🎵 音频多模态 (未来探索)

| 模型名称 | 参数量 | 功能 |
|---------|--------|------|
| **Qwen-Audio** | 8B | 音频文本多模态大模型 (预训练) |
| **Qwen-Audio-Chat** | 8B | 音频文本对话 (Chat版本) |

> **💡 模型选择建议**:
> - 日常中文转写 → `paraformer-zh` (默认)
> - 高精度/带情感 → `SenseVoiceSmall`
> - 实时场景 → `paraformer-zh-streaming` 或 `Fun-ASR-Nano-2512`
> - 说话人分离 → `paraformer-zh` + `cam++`

---

## 🎯 Ralph Loop 完成承诺

> **承诺**: 'exomind-model FunASR and MOSS integration complete and usable'
>
> **状态**: ✅ 已交付
> **交付时间**: 2026-01-27 13:55

---

## 记忆与状态管理

本 Agent 遵循 `life-os/core/memory-workflow.md` 通用流程。

### 文件结构

```
pm/
├── tasks_plan.md         # 任务计划
├── memory/               # 记忆系统
│   ├── long-term.md      # 长期记忆（技术决策、踩坑记录）
│   └── patches/          # 记忆补丁（增量更新）
├── vitals/               # 生命体征
│   ├── ledger.md         # 资源账本（Token消耗、执行时长）
│   └── health.md         # 健康状态（成功率、技能状态）
└── .logs/                # 会话日志
```

### 文件职责

| 文件/目录 | 职责 | 更新频率 |
|-----------|------|----------|
| `tasks_plan.md` | 任务队列、决策记录、验收标准 | 每任务 |
| `memory/long-term.md` | 技术决策、踩坑记录、引擎特性 | 有新发现时 |
| `memory/patches/` | 记忆增量更新 | 有新发现时 |
| `vitals/ledger.md` | 资源消耗统计、任务记录 | 每任务 |
| `vitals/health.md` | 运行状态、健康指标 | 每任务 |
| `.logs/` | 会话历史 | 每任务 |

### 更新流程

1. **任务开始前**: 读取 tasks_plan.md, memory/long-term.md
2. **任务执行中**: 写入 .logs/, scratch/
3. **任务完成后**: 更新 tasks_plan.md, vitals/, memory/

### 补丁格式

```markdown
# 记忆补丁 - YYYY-MM-DD

## 修改类型
**新增 / 修正 / 删除**

## 修改内容
### 原内容
```
[原有内容]
```

### 新内容
```
[新内容]
```

## 修改原因
[简要说明]

## 关联任务
- 任务ID: xxx

## 创建时间
YYYY-MM-DD HH:MM
```

---

## 📚 参考文档

- **PRD.md**: 产品需求文档（整合架构、功能、重构计划）
- **memory/long-term.md**: 技术决策与踩坑记录

---

*本文档遵循 life-os/core/memory-workflow.md 更新规范*

