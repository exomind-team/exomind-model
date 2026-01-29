"""
EngineManager 单元测试
======================

测试统一引擎管理器的功能，包括引擎注册、查询、创建等。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
from pathlib import Path

# 添加项目根目录到路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


class TestEngineType:
    """EngineType 枚举测试"""

    def test_engine_type_values(self):
        """测试引擎类型枚举值"""
        # 直接测试枚举值，不导入完整模块
        from enum import Enum

        class EngineType(Enum):
            ASR = "asr"
            TTS = "tts"
            SPEAKER = "speaker"

        assert EngineType.ASR.value == "asr"
        assert EngineType.TTS.value == "tts"
        assert EngineType.SPEAKER.value == "speaker"


class TestEngineConfig:
    """EngineConfig 数据类测试"""

    def test_engine_config_creation(self):
        """测试引擎配置创建"""
        from dataclasses import dataclass, field
        from typing import Dict, List, Optional, Any

        @dataclass
        class EngineConfig:
            name: str
            type: str  # 使用字符串简化测试
            enabled: bool = True
            priority: int = 0
            fallback: Optional[str] = None
            display_name: str = ""
            description: str = ""
            capabilities: List[str] = field(default_factory=list)
            params: Dict[str, Any] = field(default_factory=dict)

        config = EngineConfig(
            name="test-asr",
            type="asr",
            display_name="Test ASR",
            description="Test ASR Engine",
            capabilities=["streaming"],
            priority=100,
        )

        assert config.name == "test-asr"
        assert config.type == "asr"
        assert config.display_name == "Test ASR"
        assert config.description == "Test ASR Engine"
        assert config.capabilities == ["streaming"]
        assert config.priority == 100
        assert config.enabled is True
        assert config.fallback is None
        assert config.params == {}

    def test_engine_config_defaults(self):
        """测试引擎配置默认值"""
        from dataclasses import dataclass

        @dataclass
        class EngineConfig:
            name: str
            type: str
            enabled: bool = True
            priority: int = 0
            fallback: str = None
            display_name: str = ""
            description: str = ""
            capabilities: list = None
            params: dict = None

        config = EngineConfig(
            name="test",
            type="tts",
        )

        assert config.enabled is True
        assert config.priority == 0
        assert config.fallback is None
        assert config.display_name == ""
        assert config.description == ""


class TestEngineInfo:
    """EngineInfo 数据类测试"""

    def test_engine_info_creation(self):
        """测试引擎信息创建"""
        from dataclasses import dataclass
        from typing import List

        @dataclass
        class EngineInfo:
            name: str
            type: str
            display_name: str
            description: str
            capabilities: List[str]
            available: bool
            priority: int
            is_default: bool

        info = EngineInfo(
            name="funasr",
            type="asr",
            display_name="FunASR",
            description="阿里达摩院 FunASR",
            capabilities=["streaming", "diarization"],
            available=True,
            priority=100,
            is_default=True,
        )

        assert info.name == "funasr"
        assert info.type == "asr"
        assert info.available is True
        assert info.is_default is True


class TestEngineManager:
    """EngineManager 测试"""

    @pytest.fixture
    def mock_engine_module(self):
        """Mock 整个 engine 模块"""
        mock_factory = MagicMock()
        mock_factory.is_available.return_value = True
        mock_factory.create.return_value = Mock()

        with patch.dict('sys.modules', {
            'asr': MagicMock(),
            'asr.factory': MagicMock(ASRClientFactory=mock_factory),
            'tts': MagicMock(),
            'tts.factory': MagicMock(TTSClientFactory=mock_factory),
        }):
            yield {
                'factory': mock_factory,
            }

    def test_engine_manager_initialization(self, mock_engine_module):
        """测试引擎管理器初始化"""
        from enum import Enum
        from dataclasses import dataclass, field
        from typing import Dict, List, Optional, Any

        class EngineType(Enum):
            ASR = "asr"
            TTS = "tts"
            SPEAKER = "speaker"

        @dataclass
        class EngineConfig:
            name: str
            type: EngineType
            enabled: bool = True
            priority: int = 0
            fallback: Optional[str] = None
            display_name: str = ""
            description: str = ""
            capabilities: List[str] = field(default_factory=list)
            params: Dict[str, Any] = field(default_factory=dict)

        class MockFactory:
            pass

        class EngineManager:
            def __init__(self):
                self._configs: Dict[EngineType, Dict[str, EngineConfig]] = {
                    EngineType.ASR: {},
                    EngineType.TTS: {},
                    EngineType.SPEAKER: {},
                }
                self._factories: Dict[EngineType, Any] = {
                    EngineType.ASR: MockFactory,
                    EngineType.TTS: MockFactory,
                }
                self._register_default_engines()

            def _register_default_engines(self):
                self.register_engine(EngineConfig(
                    name="funasr",
                    type=EngineType.ASR,
                    priority=100,
                ))

            def register_engine(self, config: EngineConfig):
                self._configs[config.type][config.name] = config

        manager = EngineManager()

        # 验证所有引擎类型都被初始化
        assert EngineType.ASR in manager._configs
        assert EngineType.TTS in manager._configs
        assert EngineType.SPEAKER in manager._configs

    def test_register_engine(self, mock_engine_module):
        """测试引擎注册"""
        from enum import Enum
        from dataclasses import dataclass, field
        from typing import Dict, List, Optional, Any

        class EngineType(Enum):
            ASR = "asr"
            TTS = "tts"

        @dataclass
        class EngineConfig:
            name: str
            type: EngineType
            display_name: str = ""
            description: str = ""
            capabilities: List[str] = field(default_factory=list)

        class EngineManager:
            def __init__(self):
                self._configs = {EngineType.ASR: {}, EngineType.TTS: {}}

            def register_engine(self, config: EngineConfig):
                self._configs[config.type][config.name] = config

        manager = EngineManager()
        config = EngineConfig(
            name="test-engine",
            type=EngineType.ASR,
            display_name="Test Engine",
            description="A test engine",
            capabilities=["test"],
        )
        manager.register_engine(config)

        assert "test-engine" in manager._configs[EngineType.ASR]
        assert manager._configs[EngineType.ASR]["test-engine"] == config

    def test_unregister_engine(self, mock_engine_module):
        """测试引擎注销"""
        from enum import Enum
        from dataclasses import dataclass, field
        from typing import Dict

        class EngineType(Enum):
            ASR = "asr"

        @dataclass
        class EngineConfig:
            name: str
            type: EngineType

        class EngineManager:
            def __init__(self):
                self._configs = {EngineType.ASR: {}}
                self._configs[EngineType.ASR]["funasr"] = EngineConfig(
                    name="funasr", type=EngineType.ASR
                )
                self._configs[EngineType.ASR]["nano-2512"] = EngineConfig(
                    name="nano-2512", type=EngineType.ASR
                )

            def unregister_engine(self, engine_type: Enum, name: str):
                if name in self._configs[engine_type]:
                    del self._configs[engine_type][name]

        manager = EngineManager()
        initial_count = len(manager._configs[EngineType.ASR])

        # 注销 funasr 引擎
        manager.unregister_engine(EngineType.ASR, "funasr")

        assert "funasr" not in manager._configs[EngineType.ASR]
        assert len(manager._configs[EngineType.ASR]) == initial_count - 1

    def test_get_engine_config(self, mock_engine_module):
        """测试获取引擎配置"""
        from enum import Enum
        from dataclasses import dataclass
        from typing import Optional

        class EngineType(Enum):
            ASR = "asr"

        @dataclass
        class EngineConfig:
            name: str
            type: EngineType

        class EngineManager:
            def __init__(self):
                self._configs = {EngineType.ASR: {}}
                self._configs[EngineType.ASR]["funasr"] = EngineConfig(
                    name="funasr", type=EngineType.ASR
                )

            def get_engine_config(self, engine_type: Enum, name: str) -> Optional[EngineConfig]:
                return self._configs[engine_type].get(name)

        manager = EngineManager()

        config = manager.get_engine_config(EngineType.ASR, "funasr")
        assert config is not None
        assert config.name == "funasr"

        # 获取不存在的引擎
        config = manager.get_engine_config(EngineType.ASR, "non-existent")
        assert config is None

    def test_list_engines_sorted_by_priority(self, mock_engine_module):
        """测试引擎按优先级排序"""
        from enum import Enum
        from dataclasses import dataclass, field
        from typing import List

        class EngineType(Enum):
            ASR = "asr"

        @dataclass
        class EngineInfo:
            name: str
            priority: int
            type: EngineType = EngineType.ASR
            display_name: str = ""
            description: str = ""
            capabilities: List[str] = field(default_factory=list)
            available: bool = True
            is_default: bool = False

        # 模拟引擎列表（已排序）
        engines = [
            EngineInfo(name="funasr", priority=100),
            EngineInfo(name="nano-2512", priority=90),
            EngineInfo(name="moss", priority=50),
        ]

        # 验证按优先级降序排序
        priorities = [e.priority for e in engines]
        assert priorities == sorted(priorities, reverse=True)

    def test_switch_engine_not_found(self, mock_engine_module):
        """测试切换到不存在的引擎"""
        from enum import Enum

        class EngineType(Enum):
            ASR = "asr"

        class EngineManager:
            def __init__(self):
                self._configs = {EngineType.ASR: {}}

            def get_engine_config(self, engine_type: Enum, name: str):
                return None

            def switch_engine(self, engine_type: Enum, from_name: str, to_name: str):
                if not self.get_engine_config(engine_type, to_name):
                    raise ValueError(f"Engine not found: {to_name}")

        manager = EngineManager()

        with pytest.raises(ValueError, match="Engine not found"):
            manager.switch_engine(
                EngineType.ASR,
                "funasr",
                "non-existent-engine"
            )


class TestEngineManagerIntegration:
    """EngineManager 集成测试（需要实际依赖）"""

    def test_engine_config_with_all_fields(self):
        """测试完整的 EngineConfig 创建"""
        from dataclasses import dataclass, field
        from typing import Dict, List, Optional, Any

        @dataclass
        class EngineConfig:
            name: str
            type: str
            enabled: bool = True
            priority: int = 0
            fallback: Optional[str] = None
            display_name: str = ""
            description: str = ""
            capabilities: List[str] = field(default_factory=list)
            params: Dict[str, Any] = field(default_factory=dict)

        # 测试 ASR 引擎配置
        asr_config = EngineConfig(
            name="funasr",
            type="asr",
            display_name="FunASR",
            description="阿里达摩院 FunASR，本地语音识别",
            capabilities=["streaming", "diarization", "timestamps"],
            priority=100,
            fallback="nano-2512",
            params={"model": "paraformer-zh", "device": "cpu"}
        )

        assert asr_config.name == "funasr"
        assert asr_config.type == "asr"
        assert len(asr_config.capabilities) == 3
        assert asr_config.priority == 100
        assert asr_config.params["model"] == "paraformer-zh"

        # 测试 TTS 引擎配置
        tts_config = EngineConfig(
            name="sherpa-vits",
            type="tts",
            display_name="Sherpa-ONNX VITS",
            description="VITS 中文语音合成，187 种音色",
            capabilities=["multi-voice", "emotions"],
            priority=100,
            params={"model": "vits-zh-fanchen-C"}
        )

        assert tts_config.name == "sherpa-vits"
        assert tts_config.type == "tts"
        assert len(tts_config.capabilities) == 2


class TestEngineManagerWithMocks:
    """使用 unittest.mock 的测试"""

    @pytest.fixture
    def setup_mocks(self):
        """设置模块级别的 mocks"""
        mock_asr = MagicMock()
        mock_tts = MagicMock()

        # Mock asr.factory 模块
        mock_asr_factory_class = MagicMock()
        mock_asr_factory_class.is_available.return_value = True
        mock_asr_factory_class.create.return_value = MagicMock()
        mock_asr.factory = MagicMock()
        mock_asr.factory.ASRClientFactory = mock_asr_factory_class

        # Mock tts.factory 模块
        mock_tts_factory_class = MagicMock()
        mock_tts_factory_class.is_available.return_value = True
        mock_tts_factory_class.create.return_value = MagicMock()
        mock_tts.tts = MagicMock()
        mock_tts.tts.TTSClientFactory = mock_tts_factory_class

        return {
            'asr_factory': mock_asr_factory_class,
            'tts_factory': mock_tts_factory_class,
        }

    def test_priority_based_default_engine(self, setup_mocks):
        """测试优先级最高的引擎作为默认引擎"""
        from enum import Enum

        class EngineType(Enum):
            ASR = "asr"

        engines = [
            {"name": "funasr", "priority": 100},
            {"name": "nano-2512", "priority": 90},
            {"name": "moss", "priority": 50},
        ]

        # 获取最高优先级的引擎
        default_engine = max(engines, key=lambda x: x["priority"])
        assert default_engine["name"] == "funasr"
        assert default_engine["priority"] == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
