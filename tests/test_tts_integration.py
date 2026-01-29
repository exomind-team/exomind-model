"""TTS 集成测试

使用真实的 Sherpa-ONNX 模型进行端到端测试。
"""

import sys
from pathlib import Path
import time

# 添加项目根目录
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tts import (
    TTSClientFactory,
    TTSResult,
    create_tts_client,
)


def test_sherpa_vits_integration():
    """测试 Sherpa VITS 模型集成"""
    print("\n" + "=" * 60)
    print("测试 1: Sherpa VITS 模型集成")
    print("=" * 60)

    try:
        # 创建客户端
        client = create_tts_client(
            engine="sherpa-vits",
            model="vits-zh-hf-fanchen-C",
            speaker_id=77,
            volume_db=25.0,
        )

        print(f"引擎名称: {client.name}")
        print(f"采样率: {client.sample_rate}")
        print(f"说话人数: {client.num_speakers}")
        print(f"可用状态: {client.is_available()}")

        # 生成测试
        test_texts = [
            "你好，我是语音助手！",
            "今天天气真好。",
            "很高兴认识你。",
        ]

        for text in test_texts:
            print(f"\n生成文本: {text}")
            start = time.time()
            result = client.generate(text)
            elapsed = time.time() - start

            print(f"  时长: {result.duration:.2f}秒")
            print(f"  采样率: {result.sample_rate}Hz")
            print(f"  生成时间: {elapsed:.3f}秒")
            print(f"  RTF: {elapsed / result.duration:.3f}x")

        client.close()
        print("\n[通过] VITS 模型集成测试成功")
        return True

    except Exception as e:
        print(f"\n[失败] {e}")
        return False


def test_factory_features():
    """测试工厂功能"""
    print("\n" + "=" * 60)
    print("测试 2: 工厂功能测试")
    print("=" * 60)

    # 列出可用引擎
    engines = TTSClientFactory.available_engines()
    print(f"可用引擎: {engines}")

    # 检查引擎可用性
    for engine in engines:
        available = TTSClientFactory.is_available(engine)
        print(f"  {engine}: {'可用' if available else '不可用'}")

    # 获取引擎信息
    info = TTSClientFactory.get_engine_info("sherpa-vits")
    print(f"\n引擎信息: {info}")

    print("\n[通过] 工厂功能测试成功")
    return True


def test_volume_gain():
    """测试音量增益效果"""
    print("\n" + "=" * 60)
    print("测试 3: 音量增益测试")
    print("=" * 60)

    try:
        # 无增益
        client_no_gain = create_tts_client(
            engine="sherpa-vits",
            model="vits-zh-hf-fanchen-C",
            speaker_id=77,
            volume_db=0,
        )
        result_no_gain = client_no_gain.generate("测试音量")
        max_no_gain = result_no_gain.audio.max()
        client_no_gain.close()

        # 有增益
        client_with_gain = create_tts_client(
            engine="sherpa-vits",
            model="vits-zh-hf-fanchen-C",
            speaker_id=77,
            volume_db=25.0,
        )
        result_with_gain = client_with_gain.generate("测试音量")
        max_with_gain = result_with_gain.audio.max()
        client_with_gain.close()

        print(f"无增益最大振幅: {max_no_gain:.6f}")
        print(f"+25dB增益最大振幅: {max_with_gain:.6f}")
        print(f"增益倍数: {max_with_gain / max_no_gain:.1f}x")

        # 增益后振幅应该明显更大
        assert max_with_gain > max_no_gain, "音量增益未生效"
        print("\n[通过] 音量增益测试成功")
        return True

    except Exception as e:
        print(f"\n[失败] {e}")
        return False


def test_context_manager():
    """测试上下文管理器"""
    print("\n" + "=" * 60)
    print("测试 4: 上下文管理器测试")
    print("=" * 60)

    try:
        with create_tts_client(
            engine="sherpa-vits",
            model="vits-zh-hf-fanchen-C",
            speaker_id=77,
        ) as client:
            result = client.generate("上下文管理器测试")
            print(f"生成成功: {result.duration:.2f}秒")

        print("\n[通过] 上下文管理器测试成功")
        return True

    except Exception as e:
        print(f"\n[失败] {e}")
        return False


def test_multiple_speakers():
    """测试多说话人切换"""
    print("\n" + "=" * 60)
    print("测试 5: 多说话人切换测试")
    print("=" * 60)

    speaker_ids = [77, 99, 1, 6]

    try:
        for sid in speaker_ids:
            client = create_tts_client(
                engine="sherpa-vits",
                model="vits-zh-hf-fanchen-C",
                speaker_id=sid,
            )
            result = client.generate("切换说话人测试")
            print(f"  说话人 {sid}: {result.duration:.2f}秒")
            client.close()

        print("\n[通过] 多说话人切换测试成功")
        return True

    except Exception as e:
        print(f"\n[失败] {e}")
        return False


def main():
    """运行所有集成测试"""
    print("\n" + "#" * 60)
    print("# Voice-IME TTS 集成测试")
    print("#" * 60)

    results = []

    # 运行测试
    results.append(("工厂功能", test_factory_features()))
    results.append(("VITS 集成", test_sherpa_vits_integration()))
    results.append(("音量增益", test_volume_gain()))
    results.append(("上下文管理器", test_context_manager()))
    results.append(("多说话人", test_multiple_speakers()))

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
