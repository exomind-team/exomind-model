"""CLI 智能选择集成测试

测试 voice_ime.py 的智能选择参数功能。
"""

import pytest
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TestCLIHelp:
    """测试命令行帮助"""

    def test_help_shows_smart_option(self):
        """测试帮助显示 --smart 选项"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert "--smart" in result.stdout or "-s" in result.stdout
        assert "智能选择模式" in result.stdout

    def test_help_shows_explain_option(self):
        """测试帮助显示 --explain 选项"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert "--explain" in result.stdout or "-e" in result.stdout
        assert "选择解释" in result.stdout

    def test_help_shows_scenario_option(self):
        """测试帮助显示 --scenario 选项"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert "--scenario" in result.stdout
        assert "realtime" in result.stdout

    def test_help_shows_priority_option(self):
        """测试帮助显示 --priority 选项"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        assert "--priority" in result.stdout
        assert "latency" in result.stdout
        assert "accuracy" in result.stdout
        assert "balanced" in result.stdout


class TestSmartMode:
    """测试智能选择模式"""

    def test_smart_mode_parses_without_error(self):
        """测试 --smart 参数能正常解析"""
        # 使用 --help 快速验证参数解析
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--smart", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        # 如果参数解析失败会返回非 0 状态码
        assert result.returncode == 0

    def test_smart_explain_mode(self):
        """测试 --smart --explain 参数组合"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--smart", "--explain", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        assert result.returncode == 0

    def test_smart_scenario_mode(self):
        """测试 --smart --scenario 参数组合"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--smart", "--scenario", "meeting", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        assert result.returncode == 0

    def test_smart_priority_mode(self):
        """测试 --smart --priority 参数组合"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--smart", "--priority", "accuracy", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        assert result.returncode == 0


class TestScenarioValues:
    """测试场景参数值"""

    @pytest.mark.parametrize("scenario", [
        "realtime",
        "transcription",
        "meeting",
        "multilingual",
        "command",
        "general",
    ])
    def test_valid_scenarios(self, scenario):
        """测试有效的场景值"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--smart", "--scenario", scenario, "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        assert result.returncode == 0


class TestPriorityValues:
    """测试优先级参数值"""

    @pytest.mark.parametrize("priority", [
        "latency",
        "accuracy",
        "balanced",
    ])
    def test_valid_priorities(self, priority):
        """测试有效的优先级值"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--smart", "--priority", priority, "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        assert result.returncode == 0


class TestBackwardCompatibility:
    """测试向后兼容性"""

    def test_traditional_mode_still_works(self):
        """测试传统模式（指定引擎）仍然工作"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--asr", "funasr", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        assert result.returncode == 0
        assert "funasr" in result.stdout.lower()

    def test_nano_engine_still_works(self):
        """测试 nano-2512 引擎仍然可用"""
        result = subprocess.run(
            [sys.executable, "voice_ime.py", "--asr", "nano-2512", "--help"],
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=10
        )
        assert result.returncode == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
