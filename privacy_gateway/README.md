# 隐私网关模块 - DEPRECATED

> **状态**: 已归档
> **日期**: 2026-01-29
> **原因**: 当前优先级为 ASR/TTS 核心功能，隐私网关暂不集成

## 保留说明

此目录代码保留作为技术参考，可独立复用：

### 核心模块

| 模块 | 功能 | 状态 |
|------|------|------|
| `pii/patterns.py` | PII 正则模式定义 | ✅ 可复用 |
| `pii/detector.py` | PII 检测器 | ✅ 可复用 |
| `pii/tokenizer.py` | Token 化处理器 | ✅ 可复用 |
| `storage/token_store.py` | Token 存储 | ✅ 可复用 |
| `api/routes.py` | API 路由 | ✅ 可复用 |

### 未来可能

隐私网关可作为独立项目开发：
- 独立仓库: `exomind-privacy-gateway`
- 依赖: Presidio + MiniRBT
- 部署: 独立服务 (端口 1922)

### 相关文档

- 技术规格: `specs/spec-020c-privacy-gateway.md`
- 测试文件: `tests/test_privacy_gateway.py`
