# MOSS Transcribe-Diarize API 文档

> **来源**: MOSS Studio 官方文档
> **版本**: v1.1
> **创建时间**: 2026-01-27
> **文档地址**: https://studio.mosi.cn/docs/moss-transcribe-diarize

---

## 1. 概述

**MOSS-Transcribe-Diarize** 是摩尔线程提供的云端语音识别接口，支持将音频转写为带时间戳和说话人标识的结构化文本。

### 核心特性

- 支持多种音频输入方式（URL / Base64 / 文件上传）
- 自动识别多说话人并标记 ID
- 精确的时间戳标注（毫秒级）
- 可自定义采样参数优化转写效果

---

## 2. API 信息

### 2.1 基础信息

| 项目 | 值 |
|------|-----|
| **API 端点** | `https://studio.mosi.cn/v1/audio/transcriptions` |
| **认证方式** | Bearer Token |
| **HTTP 方法** | POST |
| **超时时间** | 建议 600 秒 |

### 2.2 请求头

```http
Authorization: Bearer <YOUR_API_KEY>
Content-Type: application/json
```

### 2.3 音频输入方式

| 方式 | 格式 | 说明 |
|------|------|------|
| **URL** | `https://example.com/audio.wav` | 公网可访问的音频文件地址 |
| **Base64** | `data:audio/wav;base64,{base64_encoded}` | Base64 编码的音频数据 |
| **文件上传** | multipart/form-data | 直接上传本地文件 |

---

## 3. 请求参数

### 3.1 请求体参数

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `model` | String | ✅ | 模型名字，固定为 `moss-transcribe-diarize` |
| `audio_data` | String | ✅ | 音频数据源（URL 或 Base64） |
| `sampling_params` | Object | ❌ | 模型采样的高级配置 |
| `meta_info` | Boolean | ❌ | 返回响应带有 meta info，默认 `false` |

### 3.2 sampling_params 采样参数

| 参数名 | 类型 | 默认值 | 描述与建议 |
|--------|------|--------|------------|
| `max_new_tokens` | Int | 128 | 最大生成长度。⚠️ **ASR 建议**：默认值较小，长语音转写请调大（如 4096），否则可能截断 |
| `temperature` | Float | 0 | 采样温度。`0` = 贪婪采样，结果确定且准确；较高值增加随机性和多样性 |
| `top_p` | Float | 1.0 | 核采样概率 (Nucleus Sampling)。控制候选词的累积概率阈值 |
| `top_k` | Int | -1 | Top-K 采样。`-1` 表示禁用（使用整个词表） |
| `min_p` | Float | 0.0 | 最小概率阈值。低于此概率的 Token 将被过滤 |

### 3.3 请求示例

**方式 A: 使用 URL**

```python
import requests

audio_input = "https://example.com/my_audio.wav"

payload = {
    "model": "moss-transcribe-diarize",
    "audio_data": audio_input,
    "sampling_params": {
        "max_new_tokens": 1024,
        "temperature": 0.0
    }
}

response = requests.post(
    "https://studio.mosi.cn/v1/audio/transcriptions",
    json=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_API_KEY"
    }
)

print(response.json())
```

**方式 B: 使用 Base64**

```python
import requests
import base64

with open("local_audio.wav", "rb") as f:
    b64_str = base64.b64encode(f.read()).decode('utf-8')
    audio_input = f"data:audio/wav;base64,{b64_str}"

payload = {
    "model": "moss-transcribe-diarize",
    "audio_data": audio_input,
    "sampling_params": {
        "max_new_tokens": 1024,
        "temperature": 0.0
    }
}

response = requests.post(
    "https://studio.mosi.cn/v1/audio/transcriptions",
    json=payload,
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_API_KEY"
    }
)
```

**方式 C: 文件上传**

```python
import requests

url = "https://studio.mosi.cn/v1/audio/transcriptions"
file_path = "local_audio.wav"

form_data = {
    "model": "moss-transcribe-diarize",
    "meta_info": "true"
}

headers = {
    "Authorization": "Bearer YOUR_API_KEY"
}

with open(file_path, "rb") as f:
    files = {
        "file": ("audio.wav", f, "audio/wav")
    }
    response = requests.post(
        url,
        data=form_data,
        files=files,
        headers=headers
    )

response.raise_for_status()
print(response.json())
```

---

## 4. 响应格式

### 4.1 成功响应

```json
{
  "asr_transcription_result": {
    "segments": [
      {
        "start_s": "0.00",
        "end_s": "2.50",
        "speaker": "S01",
        "text": "你好，请问有什么可以帮助您？"
      },
      {
        "start_s": "2.80",
        "end_s": "5.20",
        "speaker": "S02",
        "text": "我想了解一下你们的产品。"
      }
    ],
    "full_text": "你好，请问有什么可以帮助您？ 我想了解一下你们的产品。"
  },
  "meta_info": {
    "id": "fccd3348e23a447ab0d576f4d6b4f3a4",
    "prompt_tokens": 380,
    "completion_tokens": 120,
    "e2e_latency": 3.25
  },
  "usage": {
    "prompt_tokens": 380,
    "completion_tokens": 120,
    "total_tokens": 500,
    "credit_cost": 500
  }
}
```

### 4.2 响应字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `asr_transcription_result` | Object | 转写结果对象 |
| `asr_transcription_result.segments` | Array | 分段数组 |
| `asr_transcription_result.full_text` | String | 完整转写文本 |
| `meta_info` | Object | 元数据与性能指标 |
| `usage` | Object | 使用量统计 |

### 4.3 分段结果字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `start_s` | String | 开始时间（秒），如 `"0.00"` |
| `end_s` | String | 结束时间（秒），如 `"2.50"` |
| `speaker` | String | 说话人 ID，如 `"S01"`、`"S02"` |
| `text` | String | 转写文本内容，包含标点符号 |

### 4.4 meta_info 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | String | 请求的唯一标识符 (UUID) |
| `prompt_tokens` | Int | 输入消耗的 Token 数 |
| `completion_tokens` | Int | 生成消耗的 Token 数 |
| `e2e_latency` | Float | 端到端总耗时 (秒) |

### 4.5 usage 字段说明

| 字段 | 类型 | 说明 |
|------|------|------|
| `prompt_tokens` | Int | 输入 Token 数 |
| `completion_tokens` | Int | 输出 Token 数 |
| `total_tokens` | Int | 总 Token 数 |
| `credit_cost` | Int | 消耗的积分 |

---

## 5. 错误处理

### 5.1 错误码说明

| 错误码 | 描述 | 处理建议 |
|--------|------|----------|
| 4000 | Invalid Request - 请求格式无效 | 检查请求参数格式是否正确 |
| 4001 | Invalid Prompt - 提示词无效 | 检查提示词内容是否符合要求 |
| 4002 | Invalid Audio - 音频格式无效 | 检查音频格式和编码是否支持 |
| 4010 | Unauthorized - 未授权 | 检查 API Key 是否已添加到请求头 |
| 4011 | Invalid API Key - API Key 无效 | 检查 API Key 是否正确 |
| 4012 | API Key Expired - API Key 已过期 | 创建新的 API Key |
| 4013 | API Key Revoked - API Key 已吊销 | 创建新的 API Key |
| 4020 | Insufficient Credits - 余额不足 | 请充值后再试 |
| 4029 | Rate Limit - 频率超限 | 降低请求频率或实施退避重试 |
| 4030 | Forbidden - 禁止访问 | 检查账号权限 |
| 4031 | User Inactive - 账号已停用 | 联系客服激活账号 |
| 4290 | Concurrency Limit - 并发超限 | 减少并发请求数量 |
| 5000 | Internal Error - 内部异常 | 请记录 `meta_info.id` 并联系客服 |
| 5001 | Model Overloaded - 负载过高 | 建议实施指数退避重试 |
| 5002 | Invalid Audio URL - 音频下载/解码失败 | 检查 URL 可访问性或音频文件完整性 |
| 5003 | Service Unavailable - 服务不可用 | 稍后重试 |
| 5004 | Timeout - 请求超时 | 检查音频时长或网络状况，稍后重试 |

---

## 6. 性能指标与配额

| 指标 | 值 | 说明 |
|------|-----|------|
| **QPS** | 5 | 单账户最大并发请求数 |
| **TPM** | 50000 | 每分钟 Token 吞吐量 |
| **RTF** | < 0.3 | 实时率（处理速度） |
| **MAX** | 10MB | 单次请求音频大小限制 |

**说明**：
- RTF = 处理耗时 / 音频时长。数值越小代表处理速度越快
- 1 小时音频约需 540 秒完成转写
- 长音频转写建议控制并发数，避免触发 TPM 限制
- 大文件建议压缩或切片后调用

---

## 7. 在 exomind-model 中的使用

### 7.1 环境配置

```bash
# .env 文件
MOSS_API_KEY=sk-your-api-key-here
```

### 7.2 客户端初始化

```python
from asr.factory import ASRClientFactory

# 使用 MOSS 引擎
client = ASRClientFactory.create(
    'moss',
    api_key='your-api-key-here'
)

# 或使用回退机制
client = ASRClientFactory.create_with_fallback(
    primary_engine='nano-2512',
    fallback_engine='moss',
    api_key='your-api-key-here'
)
```

### 7.3 推荐采样参数

```python
# 长语音转写建议
payload = {
    "model": "moss-transcribe-diarize",
    "audio_data": audio_input,
    "sampling_params": {
        "max_new_tokens": 4096,  # 长语音需要调大
        "temperature": 0.0       # 确定性采样
    }
}
```

---

## 8. curl 调用示例

```bash
curl -X POST "https://studio.mosi.cn/v1/audio/transcriptions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "moss-transcribe-diarize",
    "audio_data": "https://example.com/audio.wav",
    "sampling_params": {
      "max_new_tokens": 1024,
      "temperature": 0.0
    }
  }'
```

---

## 9. 参考资料

- **MOSS Studio**: https://studio.mosi.cn
- **API 文档**: https://studio.mosi.cn/docs/moss-transcribe-diarize
- **控制台**: https://studio.mosi.cn/console
- **exomind-model 客户端**: `asr/moss_client.py`
- **联系邮箱**: mosi@mosi.cn

---

*文档更新时间: 2026-01-27*
*基于 MOSS Studio 官方文档提取*
