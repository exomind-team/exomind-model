# Voice-IME 日志系统架构规范

> **Spec ID**: spec-004-logging-architecture
> **版本**: 1.0.0
> **状态**: Draft
> **创建日期**: 2026-01-29
> **依赖**: spec-001-config

## 1. 概述

本文档定义 Voice-IME 项目的结构化日志规范，使用 `structlog` 实现统一日志输出。

## 2. 设计目标

- **结构化输出**：JSON 格式，便于机器解析
- **多目标输出**：控制台 + 文件 + 旋转日志
- **上下文关联**：自动绑定请求 ID、模块名
- **性能优化**：异步写入，批量处理

## 3. 日志格式

### 3.1 控制台输出（人类可读）

```
2026-01-29 10:30:45 [INFO] asr.funasr_client: FunASR initialized (model: paraformer-zh)
2026-01-29 10:30:46 [DEBUG] tts.sherpa_client: Generating audio (text: "你好", sid: 77)
2026-01-29 10:30:47 [WARNING] recorder: Low volume detected (threshold: 0.02)
```

### 3.2 文件输出（JSON 结构化）

```json
{
  "timestamp": "2026-01-29T10:30:45.123456",
  "level": "INFO",
  "logger": "asr.funasr_client",
  "event": "FunASR initialized",
  "model": "paraformer-zh",
  "device": "cpu"
}
```

## 4. 日志级别

| 级别 | 说明 | 使用场景 |
|------|------|----------|
| DEBUG | 调试信息 | 开发时详细追踪 |
| INFO | 正常操作 | 关键操作确认 |
| WARNING | 警告 | 潜在问题，不影响功能 |
| ERROR | 错误 | 操作失败，需要关注 |
| CRITICAL | 严重 | 系统级故障 |

## 5. 模块命名规范

```
asr.funasr_client     # ASR FunASR 客户端
asr.moss_client       # ASR MOSS 客户端
asr.nano_client       # ASR Nano-2512 客户端
tts.sherpa_client     # TTS Sherpa 客户端
recorder              # 录音模块
config                # 配置模块
main                  # 主程序
```

## 6. Logger 接口设计

### 6.1 获取 Logger

```python
from log import get_logger, configure_logger

# 获取模块 Logger
logger = get_logger(__name__)

# 或配置后使用全局 logger
configure_logger(
    level="INFO",
    log_file="logs/exomind-model.log",
    json_format=True,
)
logger = get_logger()
```

### 6.2 日志方法

```python
# 基本日志
logger.info("operation completed")
logger.error("operation failed", error=str(e))

# 带上下文
logger.info("ASR result", text="你好", duration=2.5)

# 绑定上下文
logger = logger.bind(request_id="req-123", user_id="user-456")
logger.info("Processing request")
```

## 7. 日志处理器配置

```python
# processors.py
import structlog
from structlog.processors import (
    TimeStamper,
    StackInfoRenderer,
    format_exc_info,
)
from structlog.stdlib import (
    add_log_level,
    filter_by_level,
    LoggerFactory,
)
from structlog鬼差鬼差鬼差鬼差.gy import JSONRenderer, ConsoleRenderer

def setup_logging(
    level: str = "INFO",
    log_file: str = "logs/exomind-model.log",
    json_format: bool = True,
):
    """配置日志系统"""

    # 处理器链
    processors = [
        filter_by_level,
        add_log_level,
        TimeStamper(fmt="iso"),
        StackInfoRenderer(),
        format_exc_info,
    ]

    if json_format:
        processors.append(JSONRenderer())
    else:
        processors.append(ConsoleRenderer())

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
```

## 8. 配置文件集成

### 8.1 config.yaml

```yaml
logging:
  level: "INFO"
  format: "json"  # json | console
  file: "logs/exomind-model.log"
  max_size: "10MB"  # 最大文件大小
  backup_count: 5    # 备份文件数量
  async_write: true  # 异步写入
```

### 8.2 配置加载

```python
from config import get_config

config = get_config()

# 根据配置设置日志
setup_logging(
    level=config.global_settings.log_level,
    log_file=config.global_settings.log_file,
)
```

## 9. 文件轮转

```python
from logging.handlers import RotatingFileHandler
import structlog

def setup_rotating_log(log_file: str, max_size: str, backup_count: int):
    """配置轮转日志"""

    # 转换大小
    size_map = {"10MB": 10 * 1024 * 1024, "100MB": 100 * 1024 * 1024}
    max_bytes = size_map.get(max_size, 10 * 1024 * 1024)

    handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )

    # 配置 structlog 使用处理器
    structlog.configure(
        ...
        logger_factory=LoggerFactory(handler=handler),
    )
```

## 10. 使用示例

### 10.1 ASR 模块日志

```python
from log import get_logger

logger = get_logger(__name__)

class FunASRClient:
    def __init__(self, config):
        logger.info("Initializing FunASR", model=config.model, device=config.device)
        self.model = load_model(config.model, device=config.device)
        logger.info("FunASR initialized", model=config.model)

    def recognize(self, audio_path: str) -> str:
        logger.debug("Starting recognition", audio=audio_path)
        try:
            result = self.model.transcribe(audio_path)
            logger.info("Recognition complete", duration=result.duration)
            return result.text
        except Exception as e:
            logger.error("Recognition failed", error=str(e))
            raise
```

### 10.2 TTS 模块日志

```python
from log import get_logger

logger = get_logger(__name__)

class SherpaTTSClient:
    def generate(self, text: str, speaker_id: int) -> bytes:
        logger.info(
            "Generating audio",
            text=text[:50],  # 截断长文本
            speaker_id=speaker_id,
        )
        start = time.time()
        audio = self._tts.generate(text, sid=speaker_id)
        duration = time.time() - start

        logger.debug(
            "Audio generated",
            duration=duration,
            rtf=duration / (len(audio) / self.sample_rate),
        )
        return audio
```

### 10.3 主程序日志

```python
from log import get_logger, configure_logger

logger = get_logger(__name__)

def main():
    configure_logger(level="INFO", log_file="logs/exomind-model.log")

    logger.info("Starting VoiceIME", version="1.0.0")

    try:
        app = VoiceIME()
        app.run()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.critical("Fatal error", error=str(e))
        raise
```

## 11. 验收标准

- [ ] 支持 JSON 和控制台两种输出格式
- [ ] 支持日志文件轮转（大小限制）
- [ ] 自动绑定模块名和行号
- [ ] 支持日志级别动态配置
- [ ] 与 config.yaml 配置集成
- [ ] 单元测试覆盖 > 80%

## 12. 性能基准

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 同步写入延迟 | < 1ms | 单条日志 |
| 异步写入延迟 | < 0.1ms | 单条日志 |
| 内存占用 | < 50MB | 运行时峰值 |

---

*本文档遵循 Voice-IME Spec 规范*
