"""
Docs API Endpoints
==================

文档 API 端点。

提供多层次 API 文档：
1. Swagger UI - GET /docs (由 FastAPI 自动提供)
2. OpenAPI Schema - GET /openapi.json (由 FastAPI 自动提供)
3. Agent 文档 - GET /v1/docs/agent (自定义)
"""

from fastapi import APIRouter
from service.models.response import HealthResponse

router = APIRouter(prefix="/v1/docs", tags=["Docs"])

# Agent 文档内容
AGENT_DOCUMENTATION = {
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
        "asr_transcribe": {
            "method": "POST",
            "path": "/v1/asr/transcribe",
            "description": "将音频转写为文本",
            "use_cases": [
                "语音输入处理",
                "会议录音转写",
                "语音命令识别"
            ],
            "request": {
                "content_type": "multipart/form-data",
                "fields": {
                    "audio": {"type": "binary", "required": True, "description": "音频文件 (wav/mp3/m4a)"},
                    "model": {"type": "string", "required": False, "default": "paraformer-zh", "description": "ASR 模型"},
                    "language": {"type": "string", "required": False, "default": "zh", "description": "语言代码"}
                }
            },
            "response": {
                "success": {"type": "boolean", "description": "是否成功"},
                "text": {"type": "string", "description": "转写文本"},
                "confidence": {"type": "number", "description": "置信度 0-1"},
                "duration_seconds": {"type": "number", "description": "音频时长"},
                "processing_time_ms": {"type": "integer", "description": "处理耗时"}
            },
            "example": {
                "curl": 'curl -X POST http://localhost:1921/v1/asr/transcribe \\\n  -F "audio=@test.wav" \\\n  -F "model=paraformer-zh"',
                "response": {
                    "success": True,
                    "text": "这是转写结果",
                    "confidence": 0.95,
                    "duration_seconds": 5.2,
                    "processing_time_ms": 342
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
            "request": {
                "content_type": "application/json",
                "fields": {
                    "text": {"type": "string", "required": True, "description": "合成文本 (1-5000字符)"},
                    "model": {"type": "string", "required": False, "default": "vits-zh-hf-fanchen-C", "description": "TTS 模型"},
                    "voice_id": {"type": "integer", "required": False, "default": 77, "description": "音色 ID"},
                    "speed": {"type": "number", "required": False, "default": 1.0, "description": "语速 (0.5-2.0)"},
                    "volume_db": {"type": "number", "required": False, "default": 25, "description": "音量 (dB)"}
                }
            },
            "response": {
                "success": {"type": "boolean", "description": "是否成功"},
                "audio_url": {"type": "string", "description": "音频 URL"},
                "duration_seconds": {"type": "number", "description": "音频时长"},
                "processing_time_ms": {"type": "integer", "description": "处理耗时"}
            },
            "example": {
                "curl": 'curl -X POST http://localhost:1921/v1/tts/synthesize \\\n  -H "Content-Type: application/json" \\\n  -d \'{"text":"你好","voice_id":77}\'',
                "response": {
                    "success": True,
                    "audio_url": "/v1/tts/audio/xxx.wav",
                    "duration_seconds": 3.2,
                    "processing_time_ms": 1250
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
                "latency": "中",
                "default": True
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
                "recommended_voices": [77, 99],
                "voices": [
                    {"id": 77, "name": "沉稳 温暖", "tags": ["推荐", "默认"]},
                    {"id": 99, "name": "沉稳 成熟", "tags": ["专业"]}
                ]
            }
        }
    },
    "best_practices": {
        "audio_preprocessing": "使用 16kHz 采样率、16bit、WAV 格式",
        "error_handling": "检查 response.success 字段，处理 fallback",
        "model_selection": "根据延迟和准确率需求选择"
    },
    "code_examples": {
        "python": '''
```python
import httpx
import asyncio

class VoiceIMEClient:
    def __init__(self, base_url="http://localhost:1921"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=300.0)

    async def transcribe(self, audio_path, model="paraformer-zh"):
        with open(audio_path, "rb") as f:
            files = {"audio": f}
            data = {"model": model}
            response = await self.client.post(
                f"{self.base_url}/v1/asr/transcribe",
                files=files,
                data=data
            )
        return response.json()

    async def synthesize(self, text, voice_id=77):
        response = await self.client.post(
            f"{self.base_url}/v1/tts/synthesize",
            json={"text": text, "voice_id": voice_id}
        )
        return response.json()

    async def close(self):
        await self.client.aclose()

# 使用示例
async def main():
    client = VoiceIMEClient()

    # ASR
    result = await client.transcribe("audio.wav")
    print(f"转写: {result['text']}")

    # TTS
    tts_result = await client.synthesize("你好，世界！", voice_id=77)
    print(f"音频: {tts_result['audio_url']}")

    await client.close()

asyncio.run(main())
```
'''
    }
}


@router.get("/agent")
async def get_agent_docs():
    """
    获取 Agent 专用文档

    返回专为 AI Agent 设计的提示词文档，包含：
    - 服务信息
    - 快速开始指南
    - 端点详细说明
    - 使用示例
    - 最佳实践
    """
    return AGENT_DOCUMENTATION
