# Voice-ime 产品需求文档 (PRD)

> **项目**: Voice-ime 语音输入引擎
> **版本**: v2.1
> **创建日期**: 2026-01-29
> **最后更新**: 2026-01-29
> **状态**: 本地服务开发阶段
> **目标**: 提供 HTTP API 服务，支持 Web 集成和 Agent 调用

**相关文档**: [PRODUCT.md](../PRODUCT.md) - 产品定义（愿景、架构、价值）

---

## 1. 技术决策

### 1.1 架构模式

| 决策 | 说明 |
|------|------|
| **模式** | 工厂模式 (Factory Pattern) |
| **日期** | 2026-01-27 |
| **理由** | 扩展性最强，符合开闭原则 |
| **备选** | 策略模式（扩展性较差） |

### 1.2 默认引擎配置

| 类型 | 默认引擎 | 备选引擎 |
|------|---------|---------|
| **ASR** | FunASR paraformer-zh | MOSS |
| **TTS** | vits-zh-hf-fanchen-C (ID 77, 99) | kokoro |

### 1.3 回退策略

| 场景 | 策略 |
|------|------|
| **ASR** | FunASR 失败 → MOSS 自动回退 |
| **TTS** | vits-zh-hf-fanchen-C 失败 → kokoro 回退 |

### 1.4 TTS 音色选择

| ID | 评语 | RTF |
|----|------|-----|
| **77** | 沉稳 温暖 | 0.49x |
| **99** | 沉稳 成熟 | 0.48x |
| **音量增益** | +25dB | - |

---

## 2. 任务清单

### Phase 1: 基础设施 ✅ 已完成

| ID | 任务 | 状态 | 输出 |
|----|------|------|------|
| T-01 | 创建 asr/ 目录结构 | ✅ | asr/__init__.py, base.py |
| T-02 | 实现 ASRClient 抽象基类 | ✅ | asr/base.py |
| T-03 | 实现 ASRClientFactory | ✅ | asr/factory.py |

### Phase 2: 引擎实现 ✅ 已完成

| ID | 任务 | 状态 | 输出 |
|----|------|------|------|
| T-04 | 重构 MossClient | ✅ | asr/moss_client.py |
| T-05 | 实现 FunASRClient | ✅ | asr/funasr_client.py |
| T-06 | 实现 FunASRNanoClient | ✅ | asr/nano_client.py |

### Phase 3: TTS 引擎 ✅ 已完成

| ID | 任务 | 状态 | 输出 |
|----|------|------|------|
| T-07 | Sherpa-ONNX 集成 | ✅ | sherpa_tts_demo.py |
| T-08 | 音色筛选 (187 → 2) | ✅ | voice_selector.py, voice_selector_final.py |
| T-09 | 音量增益 (+25dB) | ✅ | test_final_speakers.py |

### Phase 4: 重构规划 ✅ 已完成

| ID | 任务 | 状态 | 优先级 | 说明 |
|----|------|------|--------|------|
| T-10 | 模块化重构 | ✅ | P0 | 清晰目录结构 |
| T-11 | 配置管理 | ✅ | P0 | YAML/JSON 配置 |
| T-12 | 日志系统 | ✅ | P1 | 结构化日志 |
| T-13 | 声纹识别 | ✅ | P2 | 注册/识别说话人 |
| T-14 | 说话人分离 | ✅ | P2 | 多说话人场景 |

### Phase 5: 输出增强 ✅ 已完成

| ID | 任务 | 状态 | 优先级 | 说明 |
|----|------|------|--------|------|
| T-15 | 实时流式 ASR | ✅ | P1 | <600ms 延迟流式识别 |
| T-16 | 多引擎智能选择 | ✅ | P2 | 根据场景自动选择 |
| T-17 | 输出格式增强 | ✅ | P2 | JSON/SRT/VTT 导出 |

### Phase 6: 本地服务 ⏳ 进行中

| ID | 任务 | 状态 | 优先级 | 说明 |
|----|------|------|--------|------|
| T-18 | FastAPI 服务架构 | ⏳ | P0 | Python FastAPI 服务 |
| T-19 | ASR API 端点 | ⏳ | P0 | POST /v1/asr/transcribe |
| T-20 | TTS API 端点 | ⏳ | P0 | POST /v1/tts/synthesize |
| T-21 | Agent 文档 API | ⏳ | P0 | GET /v1/docs/agent ⭐ |
| T-22 | 前端集成 (独立项目) | ⏳ | P1 | voice-ime-web TypeScript |

---

## 3. 踩坑记录

### Bug-01: factory 参数名称错误
- **日期**: 2026-01-27
- **问题**: `engine` vs `primary_engine` 参数名称不一致
- **解决**: 统一使用 `primary_engine` 和 `fallback_engine`

### Bug-02: FunASR 模型名称变更
- **日期**: 2026-01-27
- **问题**: `SenseVoiceSmall` 模型名称变更
- **解决**: 添加 `MODEL_REPO_MAP` 映射表

### Bug-03: Fun-ASR-Nano-2512 依赖缺失
- **日期**: 2026-01-27
- **解决**: 安装 `transformers>=4.51.3`, `openai-whisper`

### Bug-04: sherpa-onnx 说话人参数
- **日期**: 2026-01-28
- **问题**: 使用 `speaker_id` 报错
- **解决**: 使用 `sid=speaker_id`

### Bug-05: sherpa-onnx 音量过小
- **日期**: 2026-01-28
- **解决**: +25dB 增益放大

---

## 4. 性能测试

### 4.1 ASR 性能

| 引擎 | RTF | 延迟 | 状态 |
|------|-----|------|------|
| Fun-ASR-Nano-2512 | 0.776x | <600ms | ✅ 优秀 |
| FunASR paraformer-zh | 0.261x | - | ✅ 优秀 |

### 4.2 TTS 性能

| 引擎 | RTF | 实时率 | 状态 |
|------|-----|--------|------|
| vits-zh-hf-fanchen-C | 0.47x | 100% | ✅ 优秀 |
| vits-zh-aishell3 | 0.24x | 100% | ✅ 优秀 |

### 4.3 推荐配置

```python
# ASR 推荐配置
asr_engine = "funasr"  # 默认
fallback_engine = "moss"

# TTS 推荐配置
tts_model = "vits-zh-hf-fanchen-C"
speaker_id = 77  # 或 99
volume_db = 25
```

---

## 5. 本地服务架构 (v2.0)

### 5.1 架构决策

| 维度 | 评估 | 说明 |
|------|------|------|
| **技术栈** | Python FastAPI | 复用现有代码，快速迭代 |
| **模型集成** | 本进程推理 | 零网络通信开销 |
| **API 文档** | 多层次文档 | Swagger + OpenAPI + Agent 专用 |
| **前端策略** | 分离部署 | TypeScript + Vue3 独立项目 |

### 5.2 服务架构

```
voice-ime/
├── asr/                            # ASR 引擎模块
├── tts/                            # TTS 引擎模块
├── speaker/                        # 说话人识别模块
├── service/                        # ⭐ FastAPI 服务
│   ├── main.py                     # FastAPI 应用入口
│   ├── api/                        # API 端点
│   │   ├── asr.py                  # ASR 端点
│   │   ├── tts.py                  # TTS 端点
│   │   ├── admin.py                # Admin 端点
│   │   └── docs.py                 # 文档端点 ⭐
│   ├── models/                     # Pydantic 数据模型
│   ├── config.py                   # 配置管理
│   └── websocket.py                # WebSocket (预留)
├── voice_ime.py                    # CLI 保持兼容
├── pyproject.toml                  # 项目配置
└── config.yaml                     # 配置文件
```

### 5.3 API 端点

| 端点 | 方法 | 描述 |
|------|------|------|
| `/v1/asr/transcribe` | POST | ASR 转写 |
| `/v1/asr/models` | GET | ASR 模型列表 |
| `/v1/tts/synthesize` | POST | TTS 合成 |
| `/v1/tts/voices` | GET | TTS 音色列表 |
| `/v1/admin/status` | GET | 服务状态 |
| `/docs` | GET | Swagger UI |
| `/openapi.json` | GET | OpenAPI Schema |
| `/v1/docs/agent` | GET | Agent 专用文档 ⭐ |

---

## 6. ExoMind 整合

### 6.1 四项核心任务

| # | 任务 | 说明 | voice-ime 关联 |
|---|------|------|----------------|
| 1 | **全部集成到一个网页** | 语音输入 → Agent → 小荷 → 执行 → 输出 | 提供 ASR/TTS API |
| 2 | **有生命的Agent** | 能量额度反馈，参考 MiniMax Agent | API 文档 + 资源监控 |
| 3 | **最优先实现资源监控** | 实时查看个人/集体资源 | `/v1/admin/status` 端点 |
| 4 | **代码库集体贡献上传** | GH 命令行上传到集体库 | Git submodule 管理 |

### 6.2 关联项目

| 项目 | 路径 | 说明 |
|------|------|------|
| **VoiceIME** | `voice-ime/` | 语音输入项目（当前） |
| **ExoMind** | `ExoMind-Team/modules/Projects/exomind/` | 外心核心项目 |
| **ExoBuffer** | `ExoMind-Team/modules/Projects/ExoBuffer/` | 外部缓冲区 |

---

## 7. 附录

### 7.1 相关文档

| 文档 | 说明 |
|------|------|
| [PRODUCT.md](../PRODUCT.md) | 产品定义（愿景、架构、价值） |
| `tasks_plan.md` | 详细任务计划 |
| `memory/long-term.md` | 技术决策与踩坑记录 |
| `specs/spec-020a-tech-discussion.md` | 本地服务技术方案 |
| `input.md` | 从日记提取的任务列表 |

### 7.2 外部资源

- FunASR: https://github.com/modelscope/FunASR
- Sherpa-ONNX: https://k2-fsa.github.io/sherpa/onnx/
- VITS Models: https://huggingface.co/ffmpeg/vits-zh-hf-fanchen
- FastAPI: https://fastapi.tiangolo.com/

---

*本文档遵循 life-os/core/memory-workflow.md 更新规范*
*最后更新: 2026-01-29*
