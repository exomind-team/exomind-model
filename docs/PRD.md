# VoiceIME ASR 引擎重构 PRD

> **文档版本**: v1.0.0
> **创建日期**: 2026-01-27
> **作者**: 小荷
> **状态**: 待评审

---

## 1. 项目概述

### 1.1 产品名称
VoiceIME - 语音输入工具

### 1.2 项目简介
一个基于全局快捷键触发的语音输入工具，支持录音→云端/本地识别→自动输入。当前仅支持 MOSS 云端 API，计划重构为支持多 ASR 引擎的可扩展架构。

### 1.3 当前状态
| 维度 | 现状 |
|------|------|
| **支持引擎** | 仅 MOSS 云端 API |
| **本地模型** | 无 |
| **扩展性** | 差（硬编码） |
| **配置方式** | 仅环境变量 |
| **故障处理** | 无回退机制 |

---

## 2. 背景与动机

### 2.1 问题陈述

**痛点 1：缺少本地 ASR 选项**
- 用户需要网络才能使用语音识别
- MOSS API 有调用频率限制
- 隐私敏感场景不适合云端识别

**痛点 2：架构无法扩展**
- 当前 MOSSClient 硬编码在主程序中
- 新增引擎需要修改多处代码
- 不符合开闭原则

**痛点 3：没有故障回退**
- 云端服务不可用时，整个工具瘫痪
- 用户体验差

### 2.2 解决方案

重构为**可扩展的 ASR 引擎架构**，支持：
- 本地 FunASR（paraformer-zh, sensevoice 等）
- 云端 MOSS API
- 未来可扩展其他引擎（Whisper, Azure, 阿里云等）
- 自动故障回退

---

## 3. 目标与非目标

### 3.1 目标 (Objectives)

| 目标 | 衡量指标 |
|------|---------|
| 支持多 ASR 引擎 | FunASR + MOSS 双引擎 |
| 引擎热切换 | 命令行参数实时切换 |
| 零配置启动 | FunASR 默认本地优先 |
| 故障自动回退 | FunASR 失败 → MOSS |
| 可扩展架构 | 新引擎只需实现接口 |

### 3.2 非目标 (Out of Scope)

| 排除项 | 原因 |
|--------|------|
| GPU 加速 | 当前 AMD GPU 不支持，暂缓 |
| 实时流式识别 | 当前场景不需要 |
| 多引擎并行调用 | 暂不需要，复杂度高 |
| 引擎性能对比 | 后续版本考虑 |

---

## 4. 功能需求

### 4.1 核心功能

#### FR-01: ASR 引擎选择

**用户故事**: 作为用户，我希望能够选择使用本地还是云端的 ASR 引擎

**验收标准**:
- ✅ 支持命令行参数 `--asr moss|funasr`
- ✅ 支持环境变量 `ASR_ENGINE`
- ✅ 支持配置文件 `.env`
- ✅ 优先级：命令行 > 环境变量 > 配置文件

**使用示例**:
```bash
# 使用本地 FunASR
voice_ime.py --asr funasr

# 使用云端 MOSS
voice_ime.py --asr moss --api-key YOUR_KEY

# 默认使用本地
voice_ime.py
```

#### FR-02: FunASR 多模型支持

**用户故事**: 作为用户，我希望选择不同的 FunASR 模型

**验收标准**:
- ✅ 支持 `paraformer-zh`（中文通用）
- ✅ 支持 `sensevoice`（高精度中文）
- ✅ 支持 `paraformer-en`（英文）
- ✅ 支持命令行参数 `--funasr-model`

**使用示例**:
```bash
# 使用高精度中文模型
voice_ime.py --asr funasr --funasr-model sensevoice

# 使用英文模型
voice_ime.py --asr funasr --funasr-model paraformer-en
```

#### FR-03: 设备选择

**用户故事**: 作为用户，我希望指定 ASR 引擎运行的设备

**验收标准**:
- ✅ 支持 `cpu`（默认）
- ✅ 支持 `cuda`（预留）
- ✅ 支持命令行参数 `--funasr-device`

**使用示例**:
```bash
# 使用 CPU
voice_ime.py --asr funasr --funasr-device cpu
```

#### FR-04: 自动故障回退

**用户故事**: 当本地引擎失败时，自动切换到云端引擎

**验收标准**:
- ✅ FunASR 加载失败时自动回退到 MOSS
- ✅ 回退时打印警告信息
- ✅ 用户可感知回退行为

**行为示例**:
```
⚠️  FunASR 初始化失败: 模型加载超时
🔄 自动回退到 MOSS Cloud API...
✅ 已切换到 MOSS Cloud API
```

#### FR-05: 配置管理

**用户故事**: 我希望所有配置都能通过配置文件管理

**验收标准**:
- ✅ 支持 `.env` 文件配置
- ✅ 支持所有命令行参数的环境变量映射
- ✅ 配置项有合理默认值

**.env 配置示例**:
```bash
# ASR 引擎选择
ASR_ENGINE=funasr

# FunASR 配置
FUNASR_MODEL=paraformer-zh
FUNASR_DEVICE=cpu

# MOSS 配置
MOSS_API_KEY=sk-xxx
```

---

### 4.2 非功能性需求

| 需求ID | 需求描述 | 衡量指标 |
|--------|---------|---------|
| NFR-01 | 可扩展性 | 新引擎只需实现 3 个方法 |
| NFR-02 | 可测试性 | 每个引擎可独立测试 |
| NFR-03 | 向后兼容 | 现有 MOSS 用户无感知 |
| NFR-04 | 启动速度 | FunASR 加载 < 10秒 |

---

## 5. 技术设计

### 5.1 整体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        VoiceIME 主程序                           │
│  • 快捷键监听 (keyboard)                                         │
│  • 录音模块 (sounddevice)                                        │
│  • 自动输入 (pyperclip + pyautogui)                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     ASR Client Factory                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    ASRClient (抽象基类)                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│            │                    │                    │          │
│            ▼                    ▼                    ▼          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ MossClient   │    │FunASRClient  │    │ FutureClient │     │
│  │ (云端 API)   │    │ (本地模型)   │    │ (预留扩展)   │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

### 5.2 目录结构

```
1-Projects/voice-ime/
├── voice_ime.py          # 主程序（精简，调用引擎）
├── test_voice_ime.py     # 主测试文件
├── test_funasr.py        # FunASR 专项测试
├── pyproject.toml        # 项目配置
├── .env                  # 环境变量配置
├── .env.example          # 配置模板
├── README.md             # 项目文档
├── agent.md              # 设计文档
│
├── asr/                  # ASR 引擎目录（新增）
│   ├── __init__.py       # 导出公开接口
│   ├── base.py           # ASRClient 抽象基类
│   ├── factory.py        # ASRClientFactory 工厂类
│   ├── moss_client.py    # MOSS 云端引擎实现
│   └── funasr_client.py  # FunASR 本地引擎实现
│
└── docs/                 # 文档目录（新增）
    └── PRD.md            # 本文档
```

### 5.3 核心类设计

#### 5.3.1 ASRClient (抽象基类)

```python
# asr/base.py
from abc import ABC, abstractmethod
from typing import Optional

class ASRClient(ABC):
    """ASR 引擎抽象基类"""

    @property
    @abstractmethod
    def name(self) -> str:
        """引擎名称"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """引擎是否可用"""
        pass

    @abstractmethod
    def transcribe(self, audio_path: str) -> str:
        """
        转写音频文件为文本

        Args:
            audio_path: 音频文件路径 (WAV)

        Returns:
            识别后的文本
        """
        pass

    @abstractmethod
    def transcribe_audio_data(self, audio_data) -> str:
        """
        转写音频数据为文本

        Args:
            audio_data: numpy 音频数组

        Returns:
            识别后的文本
        """
        pass
```

#### 5.3.2 ASRClientFactory (工厂类)

```python
# asr/factory.py
from typing import Optional
from .base import ASRClient
from .moss_client import MossClient
from .funasr_client import FunASRClient

class ASRClientFactory:
    """ASR 客户端工厂"""

    _engines = {
        'moss': MossClient,
        'funasr': FunASRClient,
    }

    @classmethod
    def create(cls, engine: str, **kwargs) -> ASRClient:
        """
        创建 ASR 客户端

        Args:
            engine: 引擎名称 ('moss' | 'funasr')
            **kwargs: 引擎特定配置

        Returns:
            ASRClient 实例
        """
        if engine not in cls._engines:
            raise ValueError(f"Unknown ASR engine: {engine}")

        return cls._engines[engine](**kwargs)

    @classmethod
    def register(cls, name: str, client_class: type):
        """注册新的 ASR 引擎"""
        cls._engines[name] = client_class

    @classmethod
    def get_available_engines(cls) -> list[str]:
        """获取可用的引擎列表"""
        return list(cls._engines.keys())
```

#### 5.3.3 MossClient (MOSS 引擎)

```python
# asr/moss_client.py
import base64
import requests
from .base import ASRClient

class MossClient(ASRClient):
    """MOSS 云端 ASR 引擎"""

    API_ENDPOINT = "https://studio.mosi.cn/v1/audio/transcriptions"

    def __init__(self, api_key: str, model: str = "moss-transcribe-diarize"):
        self._api_key = api_key
        self._model = model
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    @property
    def name(self) -> str:
        return "MOSS Cloud API"

    @property
    def is_available(self) -> bool:
        return bool(self._api_key)

    def transcribe(self, audio_path: str) -> str:
        """转写音频文件"""
        # 读取音频并转为 Base64
        with open(audio_path, 'rb') as f:
            audio_content = f.read()

        b64_str = base64.b64encode(audio_content).decode('utf-8')
        audio_data = f"data:audio/wav;base64,{b64_str}"

        payload = {
            "model": self._model,
            "audio_data": audio_data,
            "sampling_params": {
                "max_new_tokens": 1024,
                "temperature": 0.0
            },
            "meta_info": True
        }

        response = requests.post(
            self.API_ENDPOINT,
            json=payload,
            headers=self._headers,
            timeout=600
        )
        response.raise_for_status()

        result = response.json()
        asr_result = result.get('asr_transcription_result', {})
        return asr_result.get('full_text', '')

    def transcribe_audio_data(self, audio_data) -> str:
        """转写音频数据（保存为临时文件）"""
        import tempfile
        import wave
        import numpy as np

        # 保存为临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name

        # 写入 WAV
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data.astype('int16').tobytes())

        try:
            return self.transcribe(temp_path)
        finally:
            import os
            os.unlink(temp_path)
```

#### 5.3.4 FunASRClient (FunASR 引擎)

```python
# asr/funasr_client.py
from .base import ASRClient

class FunASRClient(ASRClient):
    """FunASR 本地 ASR 引擎"""

    SUPPORTED_MODELS = {
        'paraformer-zh': '中文通用模型（默认）',
        'sensevoice': '高精度中文模型',
        'paraformer-en': '英文模型',
        'telephone': '电话语音模型',
    }

    def __init__(self, model: str = 'paraformer-zh', device: str = 'cpu'):
        self._model_name = model
        self._device = device
        self._model_instance = None
        self._load_model()

    def _load_model(self):
        """加载 FunASR 模型"""
        try:
            from funasr import AutoModel
            self._model_instance = AutoModel(model=self._model_name)
        except ImportError:
            raise RuntimeError("FunASR 未安装，请运行: pip install funasr")
        except Exception as e:
            raise RuntimeError(f"FunASR 模型加载失败: {e}")

    @property
    def name(self) -> str:
        return f"FunASR ({self._model_name})"

    @property
    def is_available(self) -> bool:
        return self._model_instance is not None

    def transcribe(self, audio_path: str) -> str:
        """转写音频文件"""
        if not self._model_instance:
            raise RuntimeError("FunASR 模型未加载")

        result = self._model_instance.generate(audio_path)
        return result[0]['text']

    def transcribe_audio_data(self, audio_data) -> str:
        """转写音频数据（保存为临时文件）"""
        import tempfile
        import wave
        import numpy as np
        import os

        # 保存为临时 WAV 文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            temp_path = f.name

        # 写入 WAV
        with wave.open(temp_path, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_data.astype('int16').tobytes())

        try:
            return self.transcribe(temp_path)
        finally:
            os.unlink(temp_path)
```

---

## 6. API 设计

### 6.1 命令行参数

#### 基础参数

| 参数 | 短选项 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--asr` | `-a` | ❌ | `funasr` | ASR 引擎选择 |
| `--api-key` | `-k` | ❌ | 环境变量 | API Key |
| `--help` | `-h` | ❌ | - | 显示帮助 |

#### FunASR 参数组

| 参数 | 短选项 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--funasr-model` | ❌ | ❌ | `paraformer-zh` | 模型选择 |
| `--funasr-device` | ❌ | ❌ | `cpu` | 设备选择 |

#### MOSS 参数组

| 参数 | 短选项 | 必填 | 默认值 | 说明 |
|------|--------|------|--------|------|
| `--moss-model` | ❌ | ❌ | `moss-transcribe-diarize` | 模型选择 |

#### 示例

```bash
# 默认（本地 FunASR）
voice_ime.py

# 指定引擎
voice_ime.py --asr moss
voice_ime.py --asr funasr

# 指定模型
voice_ime.py --asr funasr --funasr-model sensevoice
voice_ime.py --asr moss --moss-model moss-transcribe-diarize

# 完整参数
voice_ime.py \
    --asr moss \
    --api-key sk-xxx \
    --moss-model moss-transcribe-diarize
```

### 6.2 环境变量

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `ASR_ENGINE` | `funasr` | 引擎选择 |
| `FUNASR_MODEL` | `paraformer-zh` | FunASR 模型 |
| `FUNASR_DEVICE` | `cpu` | 设备选择 |
| `MOSS_API_KEY` | - | MOSS API Key |

### 6.3 配置文件 (.env)

```bash
# ASR 引擎选择 (moss | funasr)
ASR_ENGINE=funasr

# FunASR 配置
FUNASR_MODEL=paraformer-zh
FUNASR_DEVICE=cpu

# MOSS 配置
MOSS_API_KEY=sk-xxx
MOSS_MODEL=moss-transcribe-diarize
```

---

## 7. 回退策略

### 7.1 回退触发条件

| 触发条件 | 回退动作 |
|----------|---------|
| FunASR 导入失败 | 回退到 MOSS |
| FunASR 模型加载失败 | 回退到 MOSS |
| FunASR 转写超时 | 回退到 MOSS |
| MOSS API 调用失败 | 报错（无可回退） |

### 7.2 回退流程

```python
def create_asr_client(engine: str, **kwargs) -> ASRClient:
    """创建 ASR 客户端，失败自动回退"""

    # 首选引擎
    try:
        client = ASRClientFactory.create(engine, **kwargs)
        if client.is_available:
            return client
    except Exception as e:
        print(f"⚠️  {engine} 初始化失败: {e}")

    # 自动回退
    if engine == 'funasr':
        print("🔄 自动回退到 MOSS Cloud API...")
        return ASRClientFactory.create('moss', **kwargs)

    # 无可回退
    raise RuntimeError(f"无法初始化 {engine}，且无回退选项")
```

---

## 8. 实施计划

### 8.1 开发阶段

#### Phase 1: 基础设施 (20 分钟)

| 任务 | 时间 | 输出 |
|------|------|------|
| 创建 asr/ 目录结构 | 5 分钟 | asr/__init__.py, asr/base.py |
| 实现 ASRClient 抽象基类 | 10 分钟 | asr/base.py |
| 实现 ASRClientFactory 工厂 | 5 分钟 | asr/factory.py |

#### Phase 2: 引擎实现 (30 分钟)

| 任务 | 时间 | 输出 |
|------|------|------|
| 重构 MossClient | 10 分钟 | asr/moss_client.py |
| 实现 FunASRClient | 15 分钟 | asr/funasr_client.py |
| 单元测试 | 5 分钟 | test_*.py |

#### Phase 3: 主程序集成 (15 分钟)

| 任务 | 时间 | 输出 |
|------|------|------|
| 修改 voice_ime.py | 10 分钟 | 命令行参数 + 引擎选择 |
| 更新 .env.example | 5 分钟 | 配置模板 |

### 8.2 验收标准

- [ ] FunASR 可正常转写（paraformer-zh）
- [ ] FunASR 可正常转写（sensevoice）
- [ ] MOSS 可正常转写
- [ ] 引擎切换生效
- [ ] 回退机制生效
- [ ] 现有 MOSS 用户无感知

---

## 9. 测试计划

### 9.1 测试类型

| 测试类型 | 覆盖率 | 工具 |
|----------|--------|------|
| 单元测试 | 核心类 100% | pytest |
| 集成测试 | API 调用 100% | pytest |
| E2E 测试 | 完整流程 | pytest + 真实音频 |

### 9.2 测试用例

#### TC-01: FunASR paraformer-zh 模型

```python
def test_funasr_paraformer_zh():
    """测试 FunASR paraformer-zh 模型"""
    client = FunASRClient(model='paraformer-zh')
    assert client.is_available

    result = client.transcribe('test.wav')
    assert isinstance(result, str)
    assert len(result) > 0
```

#### TC-02: FunASR sensevoice 模型

```python
def test_funasr_sensevoice():
    """测试 FunASR sensevoice 模型"""
    client = FunASRClient(model='sensevoice')
    assert client.is_available

    result = client.transcribe('test.wav')
    assert isinstance(result, str)
```

#### TC-03: MOSS 云端引擎

```python
def test_moss_cloud():
    """测试 MOSS 云端引擎"""
    client = MossClient(api_key='test-key')
    assert client.is_available

    result = client.transcribe('test.wav')
    assert isinstance(result, str)
```

#### TC-04: 引擎切换

```python
def test_engine_switching():
    """测试引擎切换"""
    moss = ASRClientFactory.create('moss', api_key='test')
    funasr = ASRClientFactory.create('funasr')

    assert moss.name == "MOSS Cloud API"
    assert "FunASR" in funasr.name
```

#### TC-05: 自动回退

```python
def test_fallback_to_moss():
    """测试自动回退逻辑"""
    # 模拟 FunASR 失败
    with patch('asr.funasr_client.AutoModel') as mock:
        mock.side_effect = Exception("加载失败")

        client = create_asr_client('funasr', api_key='test')
        assert client.name == "MOSS Cloud API"
```

---

## 10. 风险评估

### 10.1 已识别风险

| 风险ID | 风险描述 | 可能性 | 影响 | 缓解措施 |
|--------|---------|--------|------|---------|
| R-01 | FunASR 模型加载慢 | 中 | 中 | 添加加载提示，预加载 |
| R-02 | AMD GPU 不兼容 | 高 | 低 | 默认 CPU，GPU 可配置 |
| R-03 | MOSS API 变更 | 低 | 高 | 接口抽象，变更隔离 |

### 10.2 缓解计划

**R-01 缓解**: FunASR 模型加载时打印提示
```python
print("📦 加载 FunASR 模型 (paraformer-zh)...")
print("   首次加载可能需要 30-60 秒...")
```

**R-02 缓解**: 默认 CPU，GPU 作为可选项
```python
device = kwargs.get('device', 'cpu')
if device == 'cuda' and not has_cuda():
    print("⚠️  CUDA 不可用，回退到 CPU")
    device = 'cpu'
```

---

## 11. 附录

### 11.1 FunASR 模型说明

| 模型名称 | 语言 | 场景 | 模型大小 |
|----------|------|------|---------|
| paraformer-zh | 中文 | 通用 | ~400MB |
| sensevoice | 中文 | 高精度 | ~800MB |
| paraformer-en | 英文 | 通用 | ~400MB |
| telephone | 中/英 | 电话 | ~400MB |

### 11.2 参考资料

- [FunASR GitHub](https://github.com/alibaba-damo-academy/FunASR)
- [MOSS API 文档](https://studio.mosi.cn/docs/moss-transcribe-diarize)
- [Python 抽象基类](https://docs.python.org/3/library/abc.html)

---

> **评审状态**: 待评审
> **评审人**:
> **评审日期**:
> **评审结论**: ☐ 通过 ☐ 有条件通过 ☐ 不通过

---

**文档版本历史**

| 版本 | 日期 | 作者 | 变更说明 |
|------|------|------|---------|
| v1.0.0 | 2026-01-27 | 小荷 | 初始版本 |
