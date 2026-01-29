#!/usr/bin/env python3
"""
Qwen3-TTS CPU 测试脚本

支持三种模式：
1. CustomVoice - 预设音色生成
2. VoiceDesign - 自然语言描述生成
3. Base - 3秒音频克隆

使用方法:
    python test_qwen3_tts.py --mode custom   # 预设音色
    python test_qwen3_tts.py --mode design   # 语音设计
    python test_qwen3_tts.py --mode clone    # 语音克隆
"""

import argparse
import os
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
import soundfile as sf


def get_default_device():
    """检测可用设备"""
    if torch.cuda.is_available():
        return "cuda", torch.float16
    elif hasattr(torch, 'xla') and hasattr(torch.xla, 'device'):
        return "xla", torch.float32  # TPU
    else:
        return "cpu", torch.float32  # CPU


def load_model(model_name: str):
    """加载模型（自动检测设备）"""
    from qwen_tts import Qwen3TTSModel

    device, dtype = get_default_device()
    print(f"\n🎯 检测到设备: {device}")
    print(f"📦 数据类型: {dtype}")

    # 尝试加载 FlashAttention（GPU only）
    attn_impl = None
    if device == "cuda":
        try:
            attn_impl = "flash_attention_2"
            print(f"✨ 启用 FlashAttention 2")
        except:
            pass

    print(f"\n⏳ 正在加载模型: {model_name}")
    print(f"   (首次运行会自动下载模型，约 3-4GB)")

    model = Qwen3TTSModel.from_pretrained(
        model_name,
        device_map=device,
        dtype=dtype,
        attn_implementation=attn_impl,
    )

    print(f"✅ 模型加载完成！")
    return model


def test_custom_voice(model):
    """测试 CustomVoice 模式 - 预设音色"""
    print("\n" + "=" * 60)
    print("🎤 CustomVoice 模式 - 预设音色生成")
    print("=" * 60)

    # 获取支持的音色
    try:
        speakers = model.get_supported_speakers()
        languages = model.get_supported_languages()
        print(f"\n📋 支持的音色: {speakers}")
        print(f"🌐 支持的语言: {languages}")
    except:
        print("\n⚠️ 无法获取支持的音色列表，使用默认音色")

    # 测试文本
    test_texts = [
        ("你好，我是小荷！今天有什么可以帮你的吗？", "Chinese", "Vivian", ""),
        ("Hello, this is a test of the text to speech system.", "English", "Ryan", ""),
    ]

    for text, lang, speaker, instruct in test_texts:
        print(f"\n🔊 生成语音:")
        print(f"   文本: {text[:50]}...")
        print(f"   语言: {lang}")
        print(f"   音色: {speaker}")

        wavs, sr = model.generate_custom_voice(
            text=text,
            language=lang,
            speaker=speaker,
            instruct=instruct,
        )

        output_path = f"output_custom_{speaker}.wav"
        sf.write(output_path, wavs[0], sr)
        print(f"✅ 已保存: {output_path}")


def test_voice_design(model):
    """测试 VoiceDesign 模式 - 自然语言描述生成"""
    print("\n" + "=" * 60)
    print("🎨 VoiceDesign 模式 - 自然语言语音设计")
    print("=" * 60)

    test_cases = [
        (
            "哥哥，你回来啦，人家等了你好久好久了！",
            "Chinese",
            "体现撒娇稚嫩的萝莉女声，音调偏高且起伏明显，营造出黏人、做作又刻意卖萌的听觉效果。"
        ),
        (
            "今天的工作终于完成了，好累啊...",
            "Chinese",
            "成熟女性的疲惫声音，语调低沉，带有一点无奈"
        ),
    ]

    for text, lang, instruct in test_cases:
        print(f"\n🔊 生成语音:")
        print(f"   文本: {text}")
        print(f"   描述: {instruct[:30]}...")

        wavs, sr = model.generate_voice_design(
            text=text,
            language=lang,
            instruct=instruct,
        )

        output_path = "output_voice_design.wav"
        sf.write(output_path, wavs[0], sr)
        print(f"✅ 已保存: {output_path}")


def test_voice_clone(model):
    """测试 Base 模式 - 语音克隆"""
    print("\n" + "=" * 60)
    print("🎭 Base 模式 - 语音克隆（3秒参考音频）")
    print("=" * 60)

    # 使用官方示例音频
    ref_audio = "https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen3-TTS-Repo/clone.wav"
    ref_text = "Okay. Yeah. I resent you. I love you. I respect you. But you know what? You blew it!"

    print(f"\n📎 参考音频: {ref_audio}")
    print(f"📝 参考文本: {ref_text}")

    test_texts = [
        ("Hello, this is a test of voice cloning.", "English"),
        ("你好，这是语音克隆的测试。", "Chinese"),
    ]

    for text, lang in test_texts:
        print(f"\n🔊 克隆语音:")
        print(f"   文本: {text}")

        wavs, sr = model.generate_voice_clone(
            text=text,
            language=lang,
            ref_audio=ref_audio,
            ref_text=ref_text,
        )

        output_path = "output_voice_clone.wav"
        sf.write(output_path, wavs[0], sr)
        print(f"✅ 已保存: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Qwen3-TTS CPU 测试")
    parser.add_argument(
        "--mode",
        choices=["custom", "design", "clone", "all"],
        default="custom",
        help="测试模式: custom(预设音色), design(语音设计), clone(语音克隆), all(全部)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        help="模型名称"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("🎯 Qwen3-TTS 本地测试")
    print("=" * 60)

    # 创建输出目录
    os.makedirs("tts_output", exist_ok=True)
    os.chdir("tts_output")

    # 根据模式选择模型
    model_map = {
        "custom": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
        "design": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
        "clone": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
        "all": "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
    }

    model_name = model_map.get(args.mode, args.model)

    try:
        # 加载模型
        model = load_model(model_name)

        # 运行测试
        if args.mode == "custom":
            test_custom_voice(model)
        elif args.mode == "design":
            test_voice_design(model)
        elif args.mode == "clone":
            test_voice_clone(model)
        elif args.mode == "all":
            # 依次测试所有模式
            test_custom_voice(model)

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
