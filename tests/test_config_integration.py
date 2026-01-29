"""配置模块集成测试

测试配置与 TTS/ASR 模块的集成。
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config import get_config, ConfigLoader


def test_config_with_tts():
    """测试配置与 TTS 模块集成"""
    print("\n" + "=" * 60)
    print("测试 1: 配置与 TTS 模块集成")
    print("=" * 60)

    config = get_config("config.yaml")

    # 验证 TTS 配置
    print(f"TTS 首选引擎: {config.tts.primary_engine}")
    print(f"VITS 模型: {config.tts.vits_model}")
    print(f"VITS 说话人: {config.tts.vits_speaker_id}")
    print(f"VITS 音量增益: {config.tts.vits_volume_db}dB")

    assert config.tts.primary_engine == "sherpa-vits"
    assert config.tts.vits_model == "vits-zh-hf-fanchen-C"
    assert config.tts.vits_speaker_id in [77, 99]

    print("\n[通过] TTS 配置集成测试成功")
    return True


def test_config_with_asr():
    """测试配置与 ASR 模块集成"""
    print("\n" + "=" * 60)
    print("测试 2: 配置与 ASR 模块集成")
    print("=" * 60)

    config = get_config("config.yaml")

    # 验证 ASR 配置
    print(f"ASR 首选引擎: {config.asr.primary_engine}")
    print(f"ASR 回退引擎: {config.asr.fallback_engine}")
    print(f"FunASR 模型: {config.asr.funasr_model}")
    print(f"FunASR 设备: {config.asr.funasr_device}")
    print(f"Nano 模型: {config.asr.nano_model}")

    assert config.asr.primary_engine == "funasr"
    assert config.asr.funasr_model == "paraformer-zh"

    print("\n[通过] ASR 配置集成测试成功")
    return True


def test_recorder_config():
    """测试录音配置"""
    print("\n" + "=" * 60)
    print("测试 3: 录音配置")
    print("=" * 60)

    config = get_config("config.yaml")

    print(f"采样率: {config.recorder.sample_rate}Hz")
    print(f"声道数: {config.recorder.channels}")
    print(f"数据类型: {config.recorder.dtype}")
    print(f"语音检测阈值: {config.recorder.threshold}")
    print(f"静音时长: {config.recorder.silence_duration}s")

    assert config.recorder.sample_rate == 16000
    assert config.recorder.channels == 1
    assert config.recorder.dtype == "int16"

    print("\n[通过] 录音配置测试成功")
    return True


def test_hotkey_config():
    """测试快捷键配置"""
    print("\n" + "=" * 60)
    print("测试 4: 快捷键配置")
    print("=" * 60)

    config = get_config("config.yaml")

    print(f"录音快捷键: {config.hotkey.record}")
    print(f"切换模式: {config.hotkey.toggle_mode}")

    assert config.hotkey.record == "f2"
    assert config.hotkey.toggle_mode in ["hold", "toggle"]

    print("\n[通过] 快捷键配置测试成功")
    return True


def test_global_config():
    """测试全局配置"""
    print("\n" + "=" * 60)
    print("测试 5: 全局配置")
    print("=" * 60)

    config = get_config("config.yaml")

    print(f"日志级别: {config.global_settings.log_level}")
    print(f"日志文件: {config.global_settings.log_file}")
    print(f"临时目录: {config.global_settings.temp_dir}")
    print(f"调试模式: {config.global_settings.debug}")

    assert config.global_settings.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
    assert "voice-ime.log" in config.global_settings.log_file

    print("\n[通过] 全局配置测试成功")
    return True


def main():
    """运行所有集成测试"""
    print("\n" + "#" * 60)
    print("# Voice-IME 配置模块集成测试")
    print("#" * 60)

    results = []

    results.append(("TTS 配置", test_config_with_tts()))
    results.append(("ASR 配置", test_config_with_asr()))
    results.append(("录音配置", test_recorder_config()))
    results.append(("快捷键配置", test_hotkey_config()))
    results.append(("全局配置", test_global_config()))

    # 汇总
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "通过" if result else "失败"
        print(f"  {name}: {status}")

    print(f"\n总计: {passed}/{total} 测试通过")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
