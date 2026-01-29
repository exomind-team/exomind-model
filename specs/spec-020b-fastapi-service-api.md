# Spec-020b: Voice-ime FastAPI Service API

> 版本：v1.0
> 创建时间：2026-01-29
> 作者：voice-ime Agent
> 状态：已实现

## 概述

本规格文档定义 Voice-ime FastAPI 服务的 API 接口规范，包括 RESTful 端点、数据模型、错误处理和使用示例。

## 架构

```
客户端 ──HTTP──> Voice-ime Service (:1921) ──内部调用──> asr/ + tts/ 模块
                          │
                     asr/ (FunASR, nano-2512, MOSS)
                     tts/ (Sherpa-ONNX VITS)
```

## 端口配置

| 环境 | 端口 | 说明 |
|------|------|------|
| 开发 | 1921 | 本地服务 |
| 测试 | 1921 | CI/CD 测试 |

## 端点列表

### 基础端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 服务信息 |
| GET | /health | 健康检查 |
| GET | /docs | Swagger UI |
| GET | /openapi.json | OpenAPI Schema |

### ASR 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /v1/asr/transcribe | 音频转写 |
| GET | /v1/asr/models | 列出 ASR 模型 |

### TTS 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /v1/tts/synthesize | 文本合成 |
| GET | /v1/tts/voices | 列出音色 |
| GET | /v1/tts/samples/{voice_id}.wav | 音色样例 |

### Admin 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /v1/admin/status | 服务状态 |

### 文档端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /v1/docs/agent | Agent 专用文档 |

---

## API 详细规格

### POST /v1/asr/transcribe

音频转写端点。

#### 请求

**Content-Type**: `multipart/form-data`

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| audio | File | ✅ | - | 音频文件 (wav/mp3/m4a) |
| model | string | ❌ | paraformer-zh | ASR 模型 |
| enable_diarization | boolean | ❌ | false | 说话人分离 |
| language | string | ❌ | zh | 语言代码 |
| response_format | string | ❌ | json | 输出格式 |

**支持的音频格式**:
- `audio/wav`
- `audio/mp3`
- `audio/m4a`

**支持的模型**:
- `paraformer-zh` - 中文通用模型 (默认)
- `nano-2512` - 实时流式模型
- `sensevoice` - 高精度多语言模型
- `moss` - MOSS 云端引擎

#### 响应 (200 OK)

```json
{
  "success": true,
  "text": "转写的文本内容",
  "model": "paraformer-zh",
  "confidence": 0.95,
  "duration_seconds": 5.2,
  "processing_time_ms": 342,
  "language": "zh",
  "format": "json",
  "segments": [
    {
      "text": "转写的文本内容",
      "start_time": 0.0,
      "end_time": 5.2,
      "confidence": 0.95
    }
  ],
  "metadata": {
    "model_load_time_ms": 1250,
    "rtf": 0.066,
    "engine": "funasr"
  }
}
```

#### 错误响应 (400)

```json
{
  "detail": "不支持的音频格式。支持: wav, mp3, m4a。当前: test.txt"
}
```

---

### POST /v1/tts/synthesize

文本合成端点。

#### 请求

**Content-Type**: `application/json`

```json
{
  "text": "你好，这是测试文本",
  "model": "vits-zh-hf-fanchen-C",
  "voice_id": 77,
  "speed": 1.0,
  "volume_db": 25.0,
  "format": "wav",
  "sample_rate": 44100
}
```

| 参数 | 类型 | 必填 | 默认值 | 范围 | 说明 |
|------|------|------|--------|------|------|
| text | string | ✅ | - | 1-5000 | 合成文本 |
| model | string | ❌ | vits-zh-hf-fanchen-C | - | TTS 模型 |
| voice_id | int | ❌ | 77 | - | 音色 ID |
| speed | float | ❌ | 1.0 | 0.5-2.0 | 语速 |
| volume_db | float | ❌ | 25.0 | -60~60 | 音量 (dB) |
| format | string | ❌ | wav | - | 音频格式 |
| sample_rate | int | ❌ | 44100 | 8000-96000 | 采样率 |

#### 响应 (200 OK)

```json
{
  "success": true,
  "audio_url": "/v1/tts/audio/xxx.wav",
  "model": "vits-zh-hf-fanchen-C",
  "voice_id": 77,
  "voice_name": "沉稳 温暖",
  "duration_seconds": 3.2,
  "processing_time_ms": 1250
}
```

---

### GET /v1/docs/agent

Agent 专用文档端点，返回可供大模型理解的结构化文档。

#### 响应 (200 OK)

```json
{
  "service": {
    "name": "Voice-ime",
    "version": "2.0.0",
    "description": "本地语音识别与合成服务",
    "capabilities": ["asr", "tts", "voice_comparison"]
  },
  "quick_start": {
    "installation": "pip install voice-ime",
    "import": "from voiceime import VoiceIMEClient",
    "minimal_example": "await client.transcribe('audio.wav')"
  },
  "endpoints": {
    "asr_transcribe": {...},
    "tts_synthesize": {...}
  },
  "models": {
    "asr": {...},
    "tts": {...}
  },
  "best_practices": {...},
  "code_examples": {...}
}
```

---

### GET /health

健康检查端点。

#### 响应 (200 OK)

```json
{
  "status": "healthy",
  "timestamp": "2026-01-29T05:38:16.158905",
  "version": "2.0.0"
}
```

---

## 数据模型

### ASRRequest

```python
class ASRTranscribeRequest(BaseModel):
    model: ASRModel = ASRModel.PARAFORMER_ZH
    enable_diarization: bool = False
    language: str = "zh"
    response_format: str = "json"
```

### TTSRequest

```python
class TTSSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    model: TTSModel = TTSModel.VITS_ZH_FANCHEN_C
    voice_id: int = 77
    speed: float = Field(default=1.0, ge=0.5, le=2.0)
    volume_db: float = Field(default=25.0, ge=-60.0, le=60.0)
    format: AudioFormat = AudioFormat.WAV
    sample_rate: int = Field(default=44100, ge=8000, le=96000)
```

### Response Models

```python
class ASRResult(BaseModel):
    success: bool
    text: Optional[str]
    model: str
    confidence: Optional[float]
    duration_seconds: Optional[float]
    processing_time_ms: Optional[int]
    language: str = "zh"
    format: str = "json"
    segments: Optional[List[dict]]
    metadata: Optional[dict]
    error: Optional[str]

class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str
```

---

## 错误处理

| HTTP 状态码 | 错误类型 | 说明 |
|-------------|----------|------|
| 400 | Bad Request | 请求参数错误 |
| 404 | Not Found | 资源不存在 |
| 500 | Internal Error | 服务内部错误 |

---

## 测试覆盖

| 类别 | 测试数 | 通过 |
|------|--------|------|
| API 端点测试 | 15 | 100% |
| 模型验证测试 | 13 | 100% |
| **总计** | **28** | **100%** |

---

## 依赖

```toml
fastapi >= 0.109.0
uvicorn[standard] >= 0.27.0
pydantic >= 2.5.0
pydantic-settings >= 2.1.0
httpx >= 0.28.1
pytest-asyncio >= 0.23.0
```

---

*本规格文档由 Ralph Loop Agent 生成*
*创建时间: 2026-01-29*
