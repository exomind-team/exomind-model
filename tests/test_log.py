"""Voice-IME 日志模块单元测试

测试 structlog 集成、LogManager 和便捷函数。
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入日志模块
from log import (
    get_logger,
    configure_logger,
    setup_logging,
    get_log_manager,
    LogManager,
    log_error,
    log_info,
    log_warning,
    log_debug,
    DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_FILE,
    DEFAULT_FORMAT,
)


class TestDefaultConfig:
    """测试默认配置"""

    def test_default_log_level(self):
        """测试默认日志级别"""
        assert DEFAULT_LOG_LEVEL == "INFO"

    def test_default_log_file(self):
        """测试默认日志文件"""
        assert DEFAULT_LOG_FILE == "logs/exomind-model.log"

    def test_default_format(self):
        """测试默认格式"""
        assert DEFAULT_FORMAT == "json"


class TestGetLogger:
    """测试 get_logger 函数"""

    def test_get_logger_no_name(self):
        """测试获取无名称 logger"""
        logger = get_logger()
        assert logger is not None

    def test_get_logger_with_name(self):
        """测试获取带名称 logger"""
        logger = get_logger("test_module")
        assert logger is not None

    def test_get_logger_name_consistency(self):
        """测试 logger 名称一致性"""
        logger1 = get_logger("test")
        logger2 = get_logger("test")
        # 两次调用应返回相同类型的 logger
        assert type(logger1) == type(logger2)


class TestConfigureLogger:
    """测试 configure_logger 函数"""

    def test_configure_json_format(self):
        """测试 JSON 格式配置"""
        configure_logger(level="DEBUG", format="json")
        logger = get_logger("test_json")
        logger.debug("Test message", key="value")

    def test_configure_console_format(self):
        """测试控制台格式配置"""
        configure_logger(level="INFO", format="console")
        logger = get_logger("test_console")
        logger.info("Console test")

    def test_configure_with_log_file(self):
        """测试带日志文件配置"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.log', delete=False) as f:
            log_path = f.name

        try:
            configure_logger(level="INFO", log_file=log_path)
            logger = get_logger("test_file")
            logger.info("File test")

            # 验证文件存在且有内容
            assert os.path.exists(log_path)
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                assert "File test" in content
        finally:
            if os.path.exists(log_path):
                os.unlink(log_path)

    def test_configure_invalid_level(self):
        """测试无效日志级别会抛出异常"""
        # 无效级别会抛出 ValueError，这是预期行为
        with pytest.raises(ValueError):
            configure_logger(level="INVALID")


class TestLogManager:
    """测试 LogManager 类"""

    def test_init_empty_config(self):
        """测试空配置初始化"""
        manager = LogManager()
        assert manager._config == {}

    def test_init_with_config(self):
        """测试带配置初始化"""
        config = {
            "level": "DEBUG",
            "file": "test.log",
            "format": "console"
        }
        manager = LogManager(config)
        assert manager._config == config

    def test_setup(self):
        """测试 setup 方法"""
        manager = LogManager({
            "level": "DEBUG",
            "format": "console"
        })
        manager.setup()
        logger = manager.get_logger("test")
        logger.debug("Setup test")

    def test_get_logger_caching(self):
        """测试 logger 缓存"""
        manager = LogManager()
        logger1 = manager.get_logger("cache_test")
        logger2 = manager.get_logger("cache_test")
        # 相同名称应返回相同实例
        assert logger1 is logger2

    def test_get_logger_different_names(self):
        """测试不同名称的 logger"""
        manager = LogManager()
        logger1 = manager.get_logger("name1")
        logger2 = manager.get_logger("name2")
        # 不同名称应返回不同实例
        assert logger1 is not logger2


class TestSetupLogging:
    """测试 setup_logging 函数"""

    def test_setup_logging_returns_manager(self):
        """测试返回 LogManager 实例"""
        manager = setup_logging(level="INFO")
        assert isinstance(manager, LogManager)

    def test_setup_logging_with_config(self):
        """测试带配置设置"""
        config = {
            "level": "DEBUG",
            "file": None,
            "format": "json"
        }
        manager = setup_logging(config=config)
        assert isinstance(manager, LogManager)

    def test_global_log_manager_updated(self):
        """测试全局 log manager 更新"""
        old_manager = get_log_manager()
        new_manager = setup_logging(level="WARNING")
        assert get_log_manager() is new_manager
        assert new_manager is not old_manager


class TestConvenienceFunctions:
    """测试便捷日志函数"""

    def test_log_info(self):
        """测试 log_info 函数"""
        configure_logger(level="INFO", format="console")
        # 不应抛出异常
        log_info("Test info message")

    def test_log_warning(self):
        """测试 log_warning 函数"""
        configure_logger(level="WARNING", format="console")
        log_warning("Test warning message")

    def test_log_error(self):
        """测试 log_error 函数"""
        configure_logger(level="ERROR", format="console")
        log_error("Test error message")

    def test_log_debug(self):
        """测试 log_debug 函数"""
        configure_logger(level="DEBUG", format="console")
        log_debug("Test debug message")

    def test_log_with_kwargs(self):
        """测试带关键字参数的日志"""
        configure_logger(level="INFO", format="console")
        log_info("Test with kwargs", key1="value1", key2=123)


class TestLogLevels:
    """测试日志级别"""

    @pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    def test_all_log_levels(self, level):
        """测试所有日志级别"""
        configure_logger(level=level, format="console")
        logger = get_logger(f"test_{level.lower()}")

        # 调用对应级别的方法
        method = getattr(logger, level.lower())
        method(f"Test {level} message")


class TestModuleExports:
    """测试模块导出"""

    def test_import_all(self):
        """测试导入所有公共 API"""
        from log import (
            get_logger,
            configure_logger,
            setup_logging,
            get_log_manager,
            LogManager,
            log_error,
            log_info,
            log_warning,
            log_debug,
        )

        assert get_logger is not None
        assert configure_logger is not None
        assert setup_logging is not None
        assert get_log_manager is not None
        assert LogManager is not None
        assert log_error is not None
        assert log_info is not None
        assert log_warning is not None
        assert log_debug is not None

    def test_all_defined(self):
        """测试 __all__ 定义"""
        import log

        expected = [
            "get_logger",
            "configure_logger",
            "setup_logging",
            "get_log_manager",
            "LogManager",
            "log_error",
            "log_info",
            "log_warning",
            "log_debug",
        ]

        for name in expected:
            assert name in log.__all__


class TestJsonOutput:
    """测试 JSON 输出格式"""

    def test_json_renderer_exists(self):
        """测试 JSONRenderer 可用"""
        from structlog.processors import JSONRenderer

        renderer = JSONRenderer(indent=2)
        assert renderer is not None


class TestConsoleOutput:
    """测试控制台输出格式"""

    def test_console_renderer_exists(self):
        """测试 ConsoleRenderer 可用"""
        from structlog.dev import ConsoleRenderer

        renderer = ConsoleRenderer()
        assert renderer is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
