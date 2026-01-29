# VoiceIME 长期记忆

> **模块**: ASR 引擎选择器
> **创建日期**: 2026-01-27
> **最后更新**: 2026-01-27

---

## 踩坑记录

### Pitfall-01: Bash 特殊字符解析问题
- **日期**: 2026-01-27
- **场景**: Ralph Loop 启动命令包含中文括号
- **错误**: `bash: syntax error near unexpected token '('`
- **原因**: 
  - 中文全角括号 `（` `）` 无法被 bash 解析
  - 语音输入可能产生特殊 Unicode 字符
- **解决方案**: 
  - 使用英文半角符号 `()`
  - 简化任务描述，去除复杂语法
- **预防措施**: 
  - Ralph Loop 命令使用英文
  - 避免在命令中使用特殊字符

### Pitfall-02: 缺少项目目录
- **日期**: 2026-01-27
- **场景**: 直接写入 pm/ 和 memory/ 目录
- **错误**: `File has not been read yet`
- **原因**: Write 工具要求先读取现有文件
- **解决方案**: 使用 Bash 的 heredoc 创建新文件
- **预防措施**:
  - 新目录用 Bash 创建
  - Read 现有文件后再 Write

### Pitfall-03: FunASR 依赖不完整
- **日期**: 2026-01-27
- **场景**: 首次运行 FunASR 客户端
- **错误**: `ModuleNotFoundError: No module named 'torch'`
- **原因**: FunASR 需要 torch + torchaudio 两个依赖
- **解决方案**:
  - `uv pip install torch --index-url https://download.pytorch.org/whl/cpu`
  - `uv pip install torchaudio --index-url https://download.pytorch.org/whl/cpu`
- **预防措施**:
  - 在 requirements.txt 中添加完整依赖
  - 或使用 `uv add funasr[all]` 检查是否有可选依赖

---

## 决策点回顾

### Decision-01: 架构模式
- **选择**: 工厂模式 (Factory Pattern)
- **日期**: 2026-01-27
- **评估**: ⭐⭐⭐⭐⭐ 成功
- **备注**: 扩展性优秀，后续添加引擎只需注册

### Decision-02: 默认引擎
- **选择**: FunASR 本地优先
- **日期**: 2026-01-27
- **评估**: ⭐⭐⭐⭐ 良好
- **备注**: 用户零配置即可使用

### Decision-03: 回退策略
- **选择**: FunASR → MOSS 自动回退
- **日期**: 2026-01-27
- **评估**: ⭐⭐⭐⭐ 良好
- **备注**: 提升用户体验

---

## 技术要点

### FunASR 模型
| 模型 | 场景 | 大小 | 状态 |
|------|------|------|------|
| paraformer-zh | 中文通用 | ~400MB | ✅ 已测试 |
| sensevoice | 高精度中文 | ~800MB | 待测试 |
| paraformer-en | 英文 | ~400MB | 待测试 |

### FunASR 性能数据
- **RTF (Real Time Factor)**: 0.277
- **含义**: 处理 1 秒音频需要 0.277 秒（实时 3.6 倍速）
- **首次加载时间**: 约 30-60 秒（下载模型）

### AMD GPU 兼容性
- **状态**: 不支持 ROCm 最新版本
- **影响**: RX 6750 GRE 无法使用 GPU 加速
- **方案**: 默认 CPU，GPU 作为预留选项

---

## 经验总结

1. **项目移动**: 移动文件后需要 Git add + commit 记录
2. **文档管理**: PRD 放在 docs/ 目录，便于版本控制
3. **Ralph Loop**: 任务描述要简洁，避免特殊字符
4. **新文件创建**: 新目录用 Bash，文件用 Read+Write
5. **uv 环境**: 使用 `uv run python` 执行命令
6. **FunASR 依赖**: 需要 `torch` + `torchaudio` 两个包

---

> **记忆更新时间**: 2026-01-27 13:50
