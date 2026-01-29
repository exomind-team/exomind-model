# VoiceIME - 语音输入工具

> 一个基于全局快捷键触发的语音输入工具，支持多 ASR 引擎本地/云端识别。同时提供 FastAPI REST API 服务。

## 双模式使用

### 模式 1: CLI 模式（全局快捷键）

按 F2 录音，自动识别并输入到目标应用。

### 模式 2: API 服务模式（推荐）

启动 FastAPI 服务，通过 HTTP API 调用 ASR/TTS 功能。

## 快速开始

### 环境要求

- Python 3.9+
- [uv](https://github.com/astral-sh/uv)（包管理）
- Linux: `libportaudio2`

### 安装依赖

```bash
cd voice-ime
uv sync
```

### 启动 API 服务（开发模式）

```bash
uv run python -m service.main
```

服务运行在 `http://localhost:1921`

### 运行测试

```bash
uv run pytest
```

### 部署（systemd 服务）

```bash
# 复制服务配置
cp deploy/voice-ime.service ~/.config/systemd/user/

# 启用并启动服务
systemctl --user enable voice-ime
systemctl --user start voice-ime

# 查看日志
journalctl --user -u voice-ime -f
```

## API 文档

| 端点 | 方法 | 描述 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/v1/asr/transcribe` | POST | ASR 音频转写 |
| `/v1/asr/models` | GET | 列出 ASR 模型 |
| `/v1/tts/synthesize` | POST | TTS 文本合成 |
| `/v1/tts/voices` | GET | 列出 TTS 音色 |
| `/v1/docs/agent` | GET | Agent 专用文档 ⭐ |
| `/docs` | GET | Swagger UI |

### 示例请求

```bash
# 健康检查
curl http://localhost:1921/health

# 音频转写
curl -X POST http://localhost:1921/v1/asr/transcribe \
  -F "audio=@test.wav" \
  -F "model=paraformer-zh"

# 文本合成
curl -X POST http://localhost:1921/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"你好世界","voice_id":77}'
```

## 功能特性

- 🎯 **全局快捷键** - 按 F2 开始/停止录音（CLI 模式）
- 🎤 **多引擎支持** - FunASR 本地引擎 / MOSS 云端引擎 / Fun-ASR-Nano-2512 实时引擎
- 👥 **说话人分离** - 支持多说话人识别
- 📋 **自动输入** - 自动复制到剪贴板并粘贴（CLI 模式）
- 🔧 **配置灵活** - 支持 .env 配置文件
- ⚡ **实时转写** - Fun-ASR-Nano-2512 实现 <600ms 延迟
- 🌐 **API 服务** - FastAPI REST API，支持 Agent 调用

## ASR 引擎对比

| 引擎 | 延迟 | 实时率 | 语言 | 特点 |
|------|------|--------|------|------|
| **Fun-ASR-Nano-2512** | <600ms | ≥1x | 31种 | 实时转写，新一代模型 |
| **FunASR (paraformer-zh)** | 2-3s | ~4x | 中文 | 成熟稳定，高精度 |
| **MOSS 云端** | 1-2s | - | 中文 | 说话人分离，需要网络 |

## 项目结构

```
voice-ime/
├── service/              # FastAPI 服务
│   ├── main.py           # 服务入口
│   ├── config.py         # 配置
│   ├── api/              # API 端点
│   │   ├── asr.py        # ASR 端点
│   │   ├── tts.py        # TTS 端点
│   │   ├── docs.py       # Agent 文档
│   │   └── admin.py      # 服务状态
│   └── models/           # 数据模型
├── asr/                  # ASR 引擎模块
├── tts/                  # TTS 引擎模块
├── tests/                # 测试文件
├── specs/                # 技术规格文档
├── deploy/               # 部署配置
│   └── voice-ime.service # systemd 服务
├── pm/                   # 项目管理
│   ├── agent.md          # Agent 配置
│   ├── input.md          # 任务队列
│   ├── PRD.md            # 产品需求文档
│   └── memory/           # 技术决策沉淀
├── voice_ime.py          # CLI 主程序
├── pyproject.toml        # 项目配置
├── CLAUDE.md             # 项目级提示词
└── README.md             # 本文档
```

## 技术栈

| 依赖 | 用途 |
|------|------|
| FastAPI | Web 框架 |
| pydantic | 数据验证 |
| pydantic-settings | 配置管理 |
| httpx | HTTP 客户端 |
| pytest-asyncio | 异步测试 |
| keyboard | 全局快捷键（CLI） |
| sounddevice | 音频录制（CLI） |
| pyperclip | 剪贴板操作（CLI） |
| pyautogui | 键盘模拟（CLI） |

## 相关文档

- [API 规格文档](specs/spec-020b-fastapi-service-api.md)
- [Agent 配置](pm/agent.md)
- [长期记忆](pm/memory/long-term.md)

---

**作者**: 小荷
**版本**: 2.0.0
