# Voice-ime Service 技术方案（定稿）

> **状态**: ✅ 已确认
> **技术栈**: Python FastAPI
> **日期**: 2026-01-29

---

## 1. 架构决策

### 最终方案: Python FastAPI (MVP)

```
┌─────────────────────────────────────────────────────────────┐
│                    Voice-ime Service (Python)               │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   复用现有代码:                                              │
│   ├── asr/                    ⭐ 直接导入                    │
│   │   ├── funasr_client.py                                     │
│   │   ├── moss_client.py                                       │
│   │   └── nano_client.py                                       │
│   │                                                          │
│   └── tts/                    ⭐ 直接导入                    │
│       └── sherpa_client.py                                    │
│                                                              │
│   新增服务层:                                                │
│   └── service/                                               │
│       ├── main.py              FastAPI 应用                  │
│       ├── api/                 API 端点                      │
│       │   ├── asr.py                                         │
│       │   ├── tts.py                                         │
│       │   └── admin.py                                       │
│       ├── models/              Pydantic 数据模型             │
│       ├── config.py            配置管理                     │
│       └── websocket.py         实时状态推送                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼ HTTP/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      客户端                                  │
│                                                              │
│   • curl / HTTP 请求                                        │
│   • Python SDK (后续生成)                                   │
│   • TypeScript 前端 (独立项目)                              │
│   • 大模型 / Agent (通过 OpenAPI 文档)                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 为什么选择此方案

| 维度 | 评估 | 说明 |
|------|------|------|
| **开发速度** | ⭐⭐⭐⭐⭐ | 复用现有代码，无跨语言开销 |
| **模型集成** | ⭐⭐⭐⭐⭐ | 本进程推理，零通信开销 |
| **快速迭代** | ⭐⭐⭐⭐⭐ | 专注于 API，不折腾前端 |
| **技术风险** | ⭐⭐⭐⭐⭐ | FastAPI 成熟稳定 |

---

## 2. 前端策略（分离部署）

```
Voice-ime 项目结构

voice-ime/                          # 后端服务 (当前项目)
├── asr/
├── tts/
├── service/                        # 新增 FastAPI 服务
└── voice_ime.py                    # CLI 保持兼容

voice-ime-web/                      # 前端项目 (独立仓库，后续创建)
├── src/
│   ├── components/
│   ├── pages/
│   └── api/
└── ...
```

**策略**：
- 后端：Python FastAPI，提供 HTTP API
- 前端：TypeScript + Vue3，独立项目
- 通信：REST API + WebSocket

---

## 3. API 文档增强（核心需求）

### 3.1 多层次文档体系

```
┌─────────────────────────────────────────────────────────────────┐
│                     Voice-ime API 文档层                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  层级 1: Swagger UI (人类阅读)                                   │
│  ═══════════════════════════════════════════════════════════    │
│  GET /docs                                                     │
│  • 交互式 API 调试                                              │
│  • 人类可读的参数说明                                           │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  层级 2: OpenAPI Schema (机器可读)                              │
│  ═══════════════════════════════════════════════════════════    │
│  GET /openapi.json                                             │
│  • 完整的 API 结构定义 (JSON)                                   │
│  • 大模型/Agent 可解析                                         │
│  • SDK 自动生成基础                                            │
│                                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  层级 3: Agent 文档 (大模型专用) ⭐ 核心需求                     │
│  ═══════════════════════════════════════════════════════════    │
│  GET /v1/docs/agent                                            │
│  • 专为 AI Agent 设计的提示词文档                               │
│  • 包含使用示例、错误处理、模型选择建议                         │
│  • 可被其他 Agent 实时读取                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Agent 文档 API 设计

**GET /v1/docs/agent**

```json
{
  "service": {
    "name": "Voice-ime",
    "version": "2.0.0",
    "description": "本地语音识别与合成服务",
    "capabilities": ["asr", "tts", "voice_comparison"]
  },
  "quick_start": {
    "installation": "pip install voiceime",
    "import": "from voiceime import VoiceIMEClient",
    "minimal_example": "await client.transcribe('audio.wav')"
  },
  "endpoints": {
    "asr_transcribe": {
      "method": "POST",
      "path": "/v1/asr/transcribe",
      "description": "将音频转写为文本",
      "use_cases": [
        "语音输入处理",
        "会议录音转写",
        "语音命令识别"
      ],
      "example": {
        "request": {
          "audio": "<binary: audio/wav>",
          "model": "paraformer-zh"
        },
        "response": {
          "text": "这是识别结果",
          "confidence": 0.95
        }
      },
      "tips": [
        "推荐使用 paraformer-zh 日常中文转写",
        "需要低延迟时使用 nano-2512",
        "高精度场景使用 sensevoice"
      ]
    },
    "tts_synthesize": {
      "method": "POST",
      "path": "/v1/tts/synthesize",
      "description": "将文本合成为语音",
      "use_cases": [
        "语音播报回复",
        "有声内容生成",
        "语音反馈"
      ],
      "example": {
        "request": {
          "text": "你好，这是语音合成",
          "voice_id": 77
        },
        "response": {
          "audio_url": "/v1/tts/audio/xxx.wav",
          "duration": 3.2
        }
      },
      "tips": [
        "voice_id=77 推荐用于日常对话",
        "voice_id=99 适合正式场合",
        "speed=1.0 为标准语速"
      ]
    }
  },
  "models": {
    "asr": {
      "paraformer-zh": {
        "description": "中文通用模型，准确率高",
        "use_for": ["日常转写", "字幕生成"],
        "latency": "中"
      },
      "nano-2512": {
        "description": "实时流式模型，延迟最低",
        "use_for": ["实时语音输入"],
        "latency": "低 (<600ms)"
      },
      "sensevoice": {
        "description": "高精度多语言模型",
        "use_for": ["高精度转写", "多语言"],
        "latency": "高"
      }
    },
    "tts": {
      "vits-zh-hf-fanchen-C": {
        "description": "中文高质量音色",
        "recommended_voices": [77, 99]
      }
    }
  },
  "best_practices": {
    "audio_preprocessing": "使用 16kHz 采样率、16bit、WAV 格式",
    "error_handling": "检查 response.success 字段，处理 fallback",
    "model_selection": "根据延迟和准确率需求选择"
  }
}
```

### 3.3 Agent 集成示例

```markdown
## Voice-ime Agent 集成提示词

你是一个集成了 Voice-ime 语音服务的智能助手。

### 可用操作

1. **语音识别 (ASR)**
   - 端点: `POST /v1/asr/transcribe`
   - 输入: 音频文件 (wav/mp3/m4a)
   - 输出: 文本结果 + 置信度

2. **语音合成 (TTS)**
   - 端点: `POST /v1/tts/synthesize`
   - 输入: 文本 + 音色 ID
   - 输出: 音频文件 URL

### 使用示例

```python
# 1. 录音并转写
audio = await record_audio()
result = await client.transcribe(audio)
user_text = result["text"]

# 2. LLM 处理
response = await llm.chat(user_text)

# 3. 语音播报
await client.synthesize(response, voice_id=77)
```

### 错误处理

```python
if result["success"]:
    text = result["text"]
else:
    # 自动回退处理
    fallback = result.get("fallback_used")
    print(f"使用备用方案: {fallback}")
```
```

---

## 4. MVP 范围（迭代 12）

### 4.1 必须完成 (MVP)

```
├── ASR API
│   ├── POST /v1/asr/transcribe    # 核心转写
│   └── GET /v1/asr/models         # 模型列表
│
├── TTS API
│   ├── POST /v1/tts/synthesize    # 核心合成
│   └── GET /v1/tts/voices         # 音色列表
│
├── Admin API
│   └── GET /v1/admin/status       # 服务状态
│
├── 文档 API (核心需求)
│   ├── GET /docs                  # Swagger UI
│   ├── GET /openapi.json          # OpenAPI Schema
│   └── GET /v1/docs/agent         # Agent 专用文档 ⭐
│
└── 基础设施
    ├── 配置管理 (config.yaml)
    └── 日志系统
```

### 4.2 延后功能

```
⏳ WebSocket 实时状态
⏳ POST /v1/tts/compare (音色对比)
⏳ 模型热加载/卸载
⏳ 性能基准测试 API
```

---

## 5. 文件结构

```
voice-ime/
├── asr/                      # 现有 (复用)
│   ├── __init__.py
│   ├── base.py
│   ├── factory.py
│   ├── funasr_client.py
│   ├── moss_client.py
│   └── nano_client.py
│
├── tts/                      # 现有 (复用)
│   └── sherpa_client.py
│
├── service/                  # 新增
│   ├── __init__.py
│   ├── main.py               # FastAPI 应用入口
│   ├── config.py             # 配置管理
│   ├── api/
│   │   ├── __init__.py
│   │   ├── asr.py            # ASR 端点
│   │   ├── tts.py            # TTS 端点
│   │   ├── admin.py          # Admin 端点
│   │   └── docs.py           # 文档端点 ⭐
│   ├── models/
│   │   ├── __init__.py
│   │   ├── request.py        # 请求模型
│   │   └── response.py       # 响应模型
│   └── websocket.py          # WebSocket (预留)
│
├── tests/
│   └── test_service/         # 服务测试
│
├── pyproject.toml            # 更新依赖
├── config.yaml               # 配置文件
└── voice_ime.py              # CLI 保持兼容
```

---

## 6. 依赖添加

```toml
# pyproject.toml 新增

[project.dependencies]
fastapi = ">=0.109.0"
uvicorn = {extras = ["standard"], version = ">=0.27.0"}
pydantic = ">=2.5.0"
python-multipart = ">=0.0.6"

# 可选
sse-starlette = ">=2.0.0"  # Server-Sent Events
```

---

## 7. 启动方式

```bash
# 开发模式 (热重载)
uv run python -m voiceime.service --reload

# 生产模式
uv run uvicorn voiceime.service.main:app --host 0.0.0.0 --port 1921 --workers 4

# 使用配置文件
uv run python -m voiceime.service --config config.yaml
```

---

## 8. 验证步骤

```bash
# 1. 启动服务
uv run python -m voiceime.service

# 2. 验证 API 文档
curl http://localhost:1921/v1/docs/agent | jq .

# 3. 测试转写
curl -X POST http://localhost:1921/v1/asr/transcribe \
  -F "audio=@test.wav" \
  -F "model=paraformer-zh"

# 4. 测试合成
curl -X POST http://localhost:1921/v1/tts/synthesize \
  -H "Content-Type: application/json" \
  -d '{"text":"测试文本","voice_id":77}'
```

---

## 9. NGINX 配置示例

```nginx
# /etc/nginx/sites-available/voice-ime
server {
    listen 80;
    server_name voice-ime.local;

    location / {
        proxy_pass http://127.0.0.1:1921;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Swagger UI
    location /docs {
        proxy_pass http://127.0.0.1:1921/docs;
    }

    # Agent 专用文档
    location /v1/docs/agent {
        proxy_pass http://127.0.0.1:1921/v1/docs/agent;
    }
}
```

**启用配置**：
```bash
sudo ln -s /etc/nginx/sites-available/voice-ime /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

## 10. 下一步

1. 创建 `service/` 目录结构
2. 实现 `main.py` FastAPI 应用
3. 实现 `api/asr.py` 和 `api/tts.py`
4. 实现 `api/docs.py` Agent 专用文档
5. 编写单元测试
6. 验证 API 可用性

---

*本文档为最终方案，迭代 12 将按此执行*

