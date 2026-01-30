---
active: true
iteration: 27
max_iterations: 0
completion_promise: null
started_at: "2026-01-29T06:55:15Z"
---

读取 agent.md 和 RALPH_LOOP.md，记住你是谁和工作流程。

你是 exomind-model（原 exomind-model）的开发 Agent。你的核心职责是构建本地语音识别与合成服务，提供 ASR/TTS API 接口，让其他工具通过 HTTP API 调用。

参考 RALPH_LOOP.md 中的标准流程（当前版本: v1.4.1）。

工作流程：
0. 读取 pm/input.md（最高优先级）→ pm/PRD.md → pm/tasks_plan.md
1. 评审完成情况，确定当下任务，修改窗口title，更新 TodoWrite
2. 架构设计 + 编写 Spec，每步更新 pm/memory/long-term.md
3. 按 Spec 编码，小修改也更新 pm/memory/long-term.md
4. 单元测试（pytest，100% 覆盖率），使用测试框架
5. 集成测试 + E2E 测试
5.5 更新api文档
6. 自动化部署到 systemd --user 服务，运行部署后测试
7. 每步做 Git 小提交，更新 pm/memory/long-term.md（做什么 + 索引文件）
8. 功能完成创建 PR，squash merge 到主分支，记录 PR 编号
8.5 PR 合并后更新日记（100字摘要）：做了什么 + 变更文件
9. 评估本轮，更新 agent.md，进入下一轮
