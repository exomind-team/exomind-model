# CLAUDE.md

This file provides guidance to Claude Code when working with code in this repository.

## Project: VoiceIME (Voice Input Method Editor)

**项目简述**：提供 ASR/TTS API 接口的语音输入输出引擎，让其他工具通过 HTTP API 调用

### 项目角色定位

| 角色 | 描述 |
|------|------|
| **主 Agent** | `pm/agent.md` - Ralph Loop 执行者，负责迭代开发 |
| **协调者** | 小荷 (XiaoHe) - 从日记分发任务，协调 Agent |
| **用户** | 最终用户，通过日记或直接交互 |

### 目录结构

```
exomind-model/
├── pm/                    # 项目管理目录
│   ├── agent.md           # Agent 身份 + Ralph Loop 流程 ⭐
│   ├── input.md           # 任务队列（最高优先级）
│   ├── PRODUCT.md         # 产品愿景 + 架构设计（季度更新）
│   └── memory/
│       └── long-term.md   # 技术决策沉淀
├── asr/                   # ASR 引擎模块
├── tts/                   # TTS 引擎模块
├── speaker/               # 说话人识别模块
├── service/               # FastAPI 服务层
├── tests/                 # 测试文件
├── specs/                 # 技术规格文档
├── CLAUDE.md              # 本文件（项目级提示词）
├── voice_ime.py           # CLI 主程序
└── README.md              # 项目说明文档
```

### 技术栈

| 类别 | 技术选择 | 说明 |
|------|----------|------|
| 语言 | Python 3.9+ | 主要开发语言 |
| 包管理 | uv | Python 虚拟环境和包管理 |
| 测试 | pytest | 单元测试框架 |
| ASR 引擎 | FunASR, MOSS, Sherpa-ONNX | 多引擎支持 |
| TTS 引擎 | Sherpa-ONNX, Kokoro | 本地推理 |
| Web 框架 | FastAPI | HTTP API 服务 |

### 代码规范

- **Python 版本**: 3.9+
- **包管理**: uv
- **测试框架**: pytest
- **代码风格**: PEP 8 + 类型注解
- **提交规范**: Conventional Commits

### Ralph Loop 集成

本项目使用 Ralph Loop 进行迭代开发：

```
1. 读取 pm/input.md（最高优先级）
2. 评审任务完成情况，更新 TodoWrite
3. 架构设计 + 编写 Spec
4. 按 Spec 编码
5. 单元测试
6. 集成测试 + E2E
7. 自动化部署（systemd --user）
8. Git 小提交 + 更新 memory/long-term.md
9. PR 提交（squash merge） + 记录 PR 编号
9.5 PR 合并后更新日记（100字摘要）
10. 评估 + 更新 agent.md → 下一轮
```

**启动 Ralph Loop**：
```bash
cd exomind-model && /ralph-loop
```

### 核心文件索引

| 文件 | 优先级 | 说明 |
|------|--------|------|
| `pm/agent.md` | P0 | Agent 身份定义 |
| `pm/input.md` | P1 | 任务队列 |
| `CLAUDE.md` | P2 | 项目级提示词 |

### 与 Life OS 集成

本项目是 Life OS 的一部分：

- **任务来源**：小荷从日记中提取任务，写入 `pm/input.md`
- **执行结果**：Agent 完成任务后，小荷将结果摘要写回日记
- **协作方式**：独立运行 Ralph Loop 循环

### 常用命令

```bash
# 运行测试
uv run pytest

# 开发模式（CLI）
uv run python voice_ime.py --help

# 服务模式（API）
uv run python -m service.main

# 服务管理
systemctl --user start exomind-model
systemctl --user enable exomind-model
systemctl --user status exomind-model
journalctl --user -u exomind-model -f

# API 测试
curl http://localhost:1921/health
curl http://localhost:1921/v1/docs/agent
```

### ExoMind 整合

| 项目 | 路径 | 说明 |
|------|------|------|
| VoiceIME | `exomind-model/` | 当前项目 |
| ExoMind | `ExoMind-Team/modules/Projects/exomind/` | 主项目 |
| ExoBuffer | `ExoMind-Team/modules/Projects/ExoBuffer/` | 消息队列 |

---

## 与全局 CLAUDE.md 的关系

本文件继承自 `~/.claude/CLAUDE.md`（全局提示词），添加了项目特定的信息。

## 相关文档

- [Life OS 入口](life-os/README.md)
- [多 Agent 协作规范](life-os/agents/MULTI_AGENT_COLLABORATION.md)
- [Ralph Loop 提示词](life-os/agents/RALPH_LOOP_PROMPT.md)
- [Agent 模板](life-os/agents/AGENT_TEMPLATE.md)

---

*创建时间: 2026-01-29*
*来源: 日记 2026-01-29*
