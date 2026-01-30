# exomind-model Input Tasks

> 更新日期: 2026-01-29 15:00
> 来源: 日记 2026-01-29 + Ralph Loop 迭代
> 端口配置: **1921**

---

## 核心定位

**语音输入输出引擎**：提供 ASR/TTS API 接口，让其他工具通过 HTTP API 调用

```
用户/Agent
    ↓ HTTP API (1921)
exomind-model (1921)
    ├── ASR 语音识别 → 文字
    └── TTS 语音合成 ← 文字
```

**项目归属**: github exomind-meam/exomind-model 私有

---

## 功能优先级

### P0 - 基础框架

| 任务 | 状态 | 说明 |
|------|------|------|
| systemd 部署 | ✅ | 用户级服务，端口 1921 |
| 健康检查端点 | ✅ | `/health` 正常工作 |
| 项目 README | ✅ | v2.0.0 完成 |

### P1 - 核心功能（按优先级排序）

| 序号 | 任务 | 状态 | 说明 |
|------|------|------|------|
| **1** | FastAPI 服务 | ✅ | 1921 端口正常运行 |
| **2** | ASR 端点 | ✅ | `/v1/asr/transcribe` |
| **3** | TTS 端点 | ✅ | `/v1/tts/synthesize` |
| **4** | Agent 文档端点 | ✅ | `/v1/docs/agent` |


### P2 - 增强功能

| 任务 | 状态 | 说明 |
|------|------|------|
| 流式 ASR | ✅ | 实时转写 |
| 说话人分离 | ✅ | CAM++ diarization API |
| 多引擎支持 | ⏳ | FunASR / Sherpa-ONNX |
| 音色扩展 | ⏳ | 更多 TTS 音色 |


### 待办（远期，不耗时间）

| 任务 | 状态 | 说明 |
|------|------|------|
| WebSocket 实时推送 | ⏸️ | 流式响应 |
| 插件系统 | ⏸️ | 动态引擎加载 |
| 隐私保护网关 |⏸️| MVP 开发中  |

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                  exomind-model (1921)                       │
├─────────────────────────────────────────────────────────┤
│  服务层                                                │
│  ├── /health (健康检查)                                │
│  ├── /v1/asr/* (语音识别)                              │
│  ├── /v1/tts/* (语音合成)                              │
│  ├── /v1/speaker/* (说话人分离)                        │
│  └── /v1/docs/* (Agent 文档)                           │
├─────────────────────────────────────────────────────────┤
│  引擎层                                                │
│  ├── ASR: FunASR paraformer-zh, SenseVoiceSmall        │
│  ├── TTS: VITS zh-fanchen, Kokoro                      │
│  └── Speaker: CAM++ (说话人分离)                       │
├─────────────────────────────────────────────────────────┤
│  集成层                                                │
│  ├── exomind-web (1949) - 集成调用                     │
│  └── Claude Code CLI - 本地 Agent                      │
└─────────────────────────────────────────────────────────┘
```

---

## Ralph Loop 迭代状态

### 迭代12（已完成 ✅）

| 任务 | 状态 | 说明 |
|------|------|------|
| FastAPI 服务 | ✅ | 端口 1921 |
| ASR/TTS 端点 | ✅ | 28/28 测试通过 |
| systemd 部署 | ✅ | 用户级服务 |
| PR #7 | ✅ | 已合并 |

### 迭代13（已完成 ✅）

| 任务 | 状态 | 说明 |
|------|------|------|
| 流式 ASR | ✅ | Fun-ASR-Nano-2512 实时转写 + API 集成 |
| 说话人分离 | ✅ | CAM++ 引擎 + API 端点 `/v1/speaker/diarize` |
| 代码重构 | ✅ | 文档同步更新 |

---

## 模型支持状态

| 类型 | 模型 | 状态 |
|------|------|------|
| **ASR** | FunASR paraformer-zh | ✅ 完成 |
| **ASR** | Fun-ASR-Nano-2512 | ✅ 完成（实时流式） |
| **ASR** | SenseVoiceSmall | ✅ 完成（输出清理） |
| **ASR** | MOSS 云端 | ✅ 完成 |
| **TTS** | VITS zh-fanchen-C (187音色) | ✅ 完成 |
| **TTS** | Kokoro multi-lang (103音色) | ⚠️ API待修复 |

---

## MVP API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/v1/asr/transcribe` | POST | ASR 转写 |
| `/v1/tts/synthesize` | POST | TTS 合成 |
| `/v1/speaker/diarize` | POST | 说话人分离 |
| `/v1/speaker/engines` | GET | 列出引擎 |
| `/v1/speaker/health/{engine}` | GET | 引擎健康检查 |
| `/v1/docs/agent` | GET | Agent 专用文档 ⭐ |
| `/docs` | GET | Swagger UI |

---

## 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| exomind-model | **1921** | 主服务端口 |
| exomind-web | 1949 | 网页入口 |

---

## 日记更新要求

每次迭代完成后，需在用户日记中追加记录：

| 项目 | 内容 |
|------|------|
| **时间戳** | `## HH:MM [小荷] exomind-model 迭代总结` |
| **字数限制** | 100字以内 |
| **记录内容** | 本轮完成的任务、变更的文件、核心产出 |
| **日记路径** | `~/ExoMind-Obsidian-HailayLin/2-个人状态与历史记录/日记/YYYY-MM-DD.md` |

**示例**：
```markdown
## 14:30 [小荷] exomind-model 迭代总结

完成 FastAPI 服务开发（1921端口），28/28 测试通过。实现 ASR/TTS 端点。启动隐私保护网关 MVP 开发。
```

---

## 参考项目（集成参考）

| 项目 | 路径 | 参考价值 |
|------|------|----------|
| **exomind-web** | `~/Project/telegram-bot/` | 网页集成入口 |
| **ExoMind** | `ExoMind-Team/modules/Projects/exomind/` | 外心核心项目 |
| **ExoBuffer** | `ExoMind-Team/modules/Projects/ExoBuffer/` | 隐私处理逻辑 |
| **Microsoft Presidio** | GitHub | PII 检测框架 |
| **MiniRBT** | HFL/Chinese-BERT-wwm | 中文 NER 模型 |

---

## README.md 模板（每次更新）

每个项目必须包含 README.md，确保用户能快速跑起来：

```markdown
# exomind-model

> 语音输入输出引擎，提供 ASR/TTS API 接口

## 快速开始

### 环境要求
- Python 3.9+
- uv（包管理）
- CUDA（可选，GPU 加速）

### 安装依赖
```bash
uv sync
```

### 启动开发服务器
```bash
uv run python -m service.main
```

### 运行测试
```bash
uv run pytest
```

### 部署（systemd 服务）
```bash
systemctl --user enable exomind-model
systemctl --user start exomind-model
```

## API 文档

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/v1/asr/transcribe` | POST | ASR 转写 |
| `/v1/tts/synthesize` | POST | TTS 合成 |

## 项目结构

```
exomind-model/
├── service/          # FastAPI 服务
├── asr/              # ASR 引擎
├── tts/              # TTS 引擎
├── deploy/           # 部署配置
├── tests/            # 测试
├── pm/               # 项目管理
│   ├── input.md      # 任务队列
│   └── agent.md      # Agent 配置
└── README.md         # 本文件
```
```

---

*最后更新：2026-01-29 14:10*
