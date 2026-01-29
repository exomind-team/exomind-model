# Ralph Loop 停止钩子提示词

> 当 Claude Code 会话即将结束时，Stop hook 输出此提示词
> 供 Agent 再次启动 Ralph Loop 循环

---

**Ralph Loop（简短版）**：

```
Ralph Loop:
0. 读取 pm/input.md（最高优先级）
1. 评审完成情况 + TodoWrite
2. 架构设计 + Spec + 更新 memory
3. 编码 + 更新 memory
4. 单元测试（pytest，100% 覆盖）
5. 集成测试 + E2E
6. 自动化部署 (systemd --user) + 测试
7. Git 小提交 + 更新 memory
8. PR 提交 (squash merge) + 更新 memory
8.5 PR后更新日记（100字摘要）
9. 评估 + 更新 agent.md → 下一轮

详细流程见: life-os/agents/RALPH_LOOP.md
```

---

**项目信息**：

| 项目 | 值 |
|------|-----|
| **项目名称** | exomind-model（原 exomind-model） |
| **核心定位** | 语音输入输出引擎，提供 ASR/TTS API 接口 |
| **服务端口** | 1921 |
| **技术栈** | Python + FastAPI + uv |
| **项目路径** | `~/ExoMind-Obsidian-HailayLin/1-Projects/exomind-model/` |

**当前任务（迭代13）**：
- ✅ FastAPI 服务（1921端口）
- ✅ ASR/TTS 端点（28/28 测试通过）
- 🔄 隐私保护网关 MVP（开发中）

---

**完整提示词（复制使用）**：

```markdown
Ralph Loop: 读取 agent.md 和 RALPH_LOOP.md，记住你是谁和工作流程。

你是 exomind-model（原 exomind-model）的开发 Agent。你的核心职责是构建本地语音识别与合成服务，提供 ASR/TTS API 接口，让其他工具通过 HTTP API 调用。

参考 RALPH_LOOP.md 中的标准流程（当前版本: v1.4.1）。

工作流程：
0. 读取 pm/input.md（最高优先级）→ pm/PRD.md → pm/tasks_plan.md
1. 评审完成情况，更新 TodoWrite
2. 架构设计 + 编写 Spec，每步更新 pm/memory/long-term.md
3. 按 Spec 编码，小修改也更新 pm/memory/long-term.md
4. 单元测试（pytest，100% 覆盖率）
5. 集成测试 + E2E 测试
6. 自动化部署到 systemd --user 服务，运行部署后测试
7. 每步做 Git 小提交，更新 pm/memory/long-term.md（做什么 + 索引文件）
8. 功能完成创建 PR，squash merge 到主分支，记录 PR 编号
8.5 PR 合并后更新日记（100字摘要）：做了什么 + 变更文件
9. 评估本轮，更新 agent.md，进入下一轮

当前重点任务（迭代13）：
- 隐私保护网关 MVP 开发
- PII 检测 + Token 替换 + 还原
- `/privacy-gateway/protect` 和 `/privacy-gateway/restore` 端点

技术栈：
- Python 3.9+ + uv
- FastAPI（端口 1921）
- ASR: FunASR paraformer-zh, SenseVoiceSmall
- TTS: VITS zh-fanchen-C, Kokoro
```

---

**Claude Code 命令**：

```bash
/ralph-loop:ralph-loop "{完整提示词}"
```

---

**版本**: v1.0
**最后更新**: 2026-01-29
**来源**: input.md + agent.md
