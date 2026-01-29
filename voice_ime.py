#!/usr/bin/env python3
"""
VoiceIME 语音输入工具
=====================
全局快捷键触发 → 录音 → ASR 识别 → 自动输入到目标应用

支持引擎:
  - funasr: 本地 FunASR 模型 (默认)
  - moss:   MOSS 云端 API
  - nano-2512: Fun-ASR-Nano-2512 实时引擎 (31种语言，低延迟)

快捷键: F2 (可自定义)
  - 第一次按下: 开始录音
  - 第二次按下: 停止录音并自动输入

使用方法:
  # 使用本地 FunASR (默认)
  python voice_ime.py

  # 使用 MOSS 云端
  python voice_ime.py --asr moss --api-key YOUR_KEY

  # 指定 FunASR 模型
  python voice_ime.py --asr funasr --funasr-model sensevoice

作者: 小荷
"""

from typing import Optional
import argparse
import os
import sys
import time
from pathlib import Path
from datetime import datetime

# 加载 .env 环境变量
from dotenv import load_dotenv
load_dotenv()

import keyboard
import sounddevice as sd
import numpy as np
import pyperclip  # 剪贴板操作

# 导入 ASR 引擎模块
from asr import ASRClientFactory, AudioContext, Scenario


# ==================== 配置 ====================
DEFAULT_HOTKEY = 'f2'  # 默认快捷键

# 录音配置
SAMPLE_RATE = 16000  # 16kHz 采样率
CHANNELS = 1         # 单声道
DTYPE = 'int16'      # 16位深度


# ==================== 录音模块 ====================
class Recorder:
    """录音管理器"""

    def __init__(self, sample_rate=SAMPLE_RATE, channels=CHANNELS):
        self.sample_rate = sample_rate
        self.channels = channels
        self.audio_data = []
        self.is_recording = False
        self.stream = None

    def callback(self, indata, frames, time, status):
        """录音回调函数"""
        if self.is_recording:
            self.audio_data.append(indata.copy())

    def start(self):
        """开始录音"""
        if self.is_recording:
            return False

        self.audio_data = []
        self.is_recording = True

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=DTYPE,
                callback=self.callback,
                blocksize=1024
            )
            self.stream.start()
            return True
        except Exception as e:
            print(f"❌ 启动录音失败: {e}")
            self.is_recording = False
            return False

    def stop(self):
        """停止录音"""
        if not self.is_recording:
            return None

        self.is_recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        if self.audio_data:
            audio_array = np.concatenate(self.audio_data)
            return audio_array
        return None

    def save_to_wav(self, audio_array: np.ndarray, filepath: str):
        """保存为 WAV 文件"""
        import wave
        with wave.open(filepath, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16位 = 2字节
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_array.tobytes())


# ==================== LLM 润色接口（预留）================
class LLMPolish:
    """LLM 润色接口 - 预留功能"""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.enabled = False

    def polish(self, text: str, style: str = "normal") -> str:
        """
        润色文本
        """
        # TODO: 接入 LLM API 实现润色功能
        return text


# ==================== 主程序 ====================
class VoiceIME:
    """语音输入法主程序"""

    def __init__(self, asr_engine: str = 'funasr',
                 hotkey: str = DEFAULT_HOTKEY,
                 auto_paste: bool = True,
                 auto_copy: bool = True,
                 smart_mode: bool = False,
                 explain: bool = False,
                 scenario: Optional[str] = None,
                 priority: str = 'balanced',
                 **kwargs):
        self.hotkey = hotkey
        self.auto_paste = auto_paste  # 自动粘贴
        self.auto_copy = auto_copy    # 自动复制
        self.smart_mode = smart_mode
        self.explain = explain
        self.scenario = scenario
        self.priority = priority

        self.recorder = Recorder()
        self.llm = LLMPolish()  # 预留 LLM 润色

        # 创建 ASR 客户端
        if smart_mode:
            # 智能选择模式
            print(f"🧠 智能选择模式已启用")
            context = AudioContext(
                duration_seconds=0.0,  # 实时录音未知时长
                estimated_speakers=1,
                language_hint="auto",
                is_streaming=True,
                priority=priority,
            )

            # 强制指定场景
            if scenario:
                scenario_map = {
                    'realtime': Scenario.REALTIME,
                    'transcription': Scenario.TRANSCRIPTION,
                    'meeting': Scenario.MEETING,
                    'multilingual': Scenario.MULTILINGUAL,
                    'command': Scenario.COMMAND,
                    'general': Scenario.GENERAL,
                }
                if scenario in scenario_map:
                    context.language_hint = scenario  # 临时复用字段传递场景
                    # 使用选择器时会根据场景参数处理

            client, selection_result = ASRClientFactory.create_smart(
                context=context,
                explain=explain,
                **kwargs
            )
            self.client = client
            self.selection_result = selection_result
            print(f"✅ 使用引擎: {self.client.name}")

            if explain and selection_result:
                print(f"📊 置信度: {selection_result.confidence:.1%}")
        else:
            # 传统模式（指定引擎）
            print(f"🔧 初始化 ASR 引擎: {asr_engine}")
            self.client = ASRClientFactory.create_with_fallback(
                primary_engine=asr_engine,
                fallback_engine='moss',
                **kwargs
            )
            print(f"✅ 使用引擎: {self.client.name}")
            self.selection_result = None

        self.state = 'idle'
        self.status_messages = {
            'idle': '🛋️  等待录音 (按 {hotkey} 开始)',
            'recording': '🔴 录音中... (按 {hotkey} 停止)',
            'processing': '⏳ 正在识别...',
            'error': '❌ 发生错误'
        }

        # 临时目录
        self.temp_dir = Path.home() / '.voice_ime' / 'temp'
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        # 尝试导入 pyautogui 用于自动粘贴
        self.pyautogui = None
        if self.auto_paste:
            try:
                import pyautogui
                self.pyautogui = pyautogui
                self.pyautogui.FAILSAFE = False
            except ImportError:
                print("⚠️  pyautogui 未安装，自动粘贴功能不可用")
                print("   安装: pip install pyautogui")

    def print_status(self):
        """打印当前状态"""
        msg = self.status_messages.get(self.state, '').format(hotkey=self.hotkey)
        print(f"\r{msg}", end='', flush=True)

    def beep(self, frequency: int = 880, duration: float = 0.1):
        """播放提示音"""
        try:
            import pyaudio
            p = pyaudio.PyAudio()
            stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100,
                          output=True)
            samples = (np.sin(2 * np.pi * np.arange(44100 * duration)
                            * frequency / 44100) * 32767).astype(np.int16)
            stream.write(samples.tobytes())
            stream.close()
            p.terminate()
        except:
            pass

    def process_audio(self, audio_array: np.ndarray):
        """处理录音并识别"""
        self.state = 'processing'
        self.print_status()

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        audio_path = self.temp_dir / f'recording_{timestamp}.wav'

        # 保存音频
        print(f"\n💾 正在保存音频...")
        self.recorder.save_to_wav(audio_array, str(audio_path))

        # 调用 ASR 引擎
        try:
            start_time = time.time()
            text = self.client.transcribe(str(audio_path))
            elapsed = time.time() - start_time

            # 清理文本（去除多余空白和字间空格）
            text = text.strip()
            # FunASR paraformer 模型会输出"字+空格"格式，去除字间空格
            text = text.replace(' ', '')
            # SenseVoice 模型会输出特殊标记，清理它们
            import re
            text = re.sub(r'<\|[^|]+\|>', '', text)

            # TODO: 可以在这里调用 LLM 润色
            # text = self.llm.polish(text, style="concise")

            # 简化输出：只打印纯文本
            print("\n" + "="*60)
            print("📝 识别结果")
            print("="*60)
            print(f"\n{text}\n")
            print("-"*60)

            # 复制到剪贴板
            if self.auto_copy:
                pyperclip.copy(text)
                print("✅ 已复制到剪贴板")

            # 自动粘贴
            if self.auto_paste and self.pyautogui:
                time.sleep(0.3)  # 等待用户切换窗口
                self.pyautogui.hotkey('ctrl', 'v')
                print("✅ 已自动粘贴")

            print(f"⏱️  耗时: {elapsed:.2f}秒 | 🏭 引擎: {self.client.name}")
            print("="*60)

        except Exception as e:
            print(f"\n❌ 识别失败: {e}")
            import traceback
            traceback.print_exc()
            self.state = 'error'
        finally:
            # 清理临时文件
            try:
                audio_path.unlink()
            except:
                pass

    def on_hotkey(self):
        """快捷键处理函数"""
        if self.state == 'idle':
            print("\n" + "="*60)
            print("🎙️  语音输入")
            print("="*60)

            if self.recorder.start():
                self.state = 'recording'
                self.beep(frequency=880, duration=0.15)
            else:
                print("❌ 无法启动录音")

        elif self.state == 'recording':
            self.beep(frequency=660, duration=0.15)
            print("\n⏹️  停止录音，开始识别...")

            audio_array = self.recorder.stop()
            if audio_array is not None and len(audio_array) > 0:
                self.process_audio(audio_array)
            else:
                print("❌ 录音数据为空")

            self.state = 'idle'
            self.print_status()

    def run(self):
        """运行语音输入法"""
        print("\n" + "="*60)
        print("🎤 VoiceIME 语音输入工具")
        print("="*60)

        # 智能模式提示
        if self.smart_mode:
            print(f"\n🧠 智能选择模式")
            if self.scenario:
                print(f"   场景: {self.scenario}")
            print(f"   优先级: {self.priority}")

        print(f"\n📌 快捷键: {self.hotkey.upper()}")
        print("   - 第一次按下: 开始录音")
        print("   - 第二次按下: 自动识别并输入")
        print(f"\n🏭 ASR 引擎: {self.client.name}")
        print(f"\n📁 临时文件目录: {self.temp_dir}")
        print("\n💡 提示: 按 ESC 可退出程序")

        self.print_status()

        # 注册热键
        keyboard.add_hotkey(self.hotkey, self.on_hotkey)
        keyboard.add_hotkey('esc', lambda: sys.exit(0))

        try:
            keyboard.wait()
        except KeyboardInterrupt:
            print("\n👋 退出程序")
            sys.exit(0)


def main():
    parser = argparse.ArgumentParser(
        description="VoiceIME 语音输入工具",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # ASR 引擎选择
    parser.add_argument(
        '--asr', '-a',
        choices=['moss', 'funasr', 'nano-2512', 'nano-mlt'],
        default='funasr',
        help='ASR 引擎选择 (默认: funasr)'
    )

    # MOSS 参数
    parser.add_argument(
        '--api-key', '-k',
        help='MOSS API Key (可选，优先使用环境变量 MOSS_API_KEY)'
    )
    parser.add_argument(
        '--moss-model',
        default='moss-transcribe-diarize',
        help='MOSS 模型名称 (默认: moss-transcribe-diarize)'
    )

    # FunASR 参数
    parser.add_argument(
        '--funasr-model',
        choices=['paraformer-zh', 'sensevoice', 'paraformer-en', 'telephone'],
        default='paraformer-zh',
        help='FunASR 模型选择 (默认: paraformer-zh)'
    )
    parser.add_argument(
        '--funasr-device',
        choices=['cpu', 'cuda'],
        default='cpu',
        help='FunASR 设备选择 (默认: cpu)'
    )
    parser.add_argument(
        '--enable-diarization',
        action='store_true',
        help='启用说话人分离功能（需要更多内存，仅 funasr 支持）'
    )

    # Fun-ASR-Nano-2512 参数
    parser.add_argument(
        '--nano-model',
        choices=['nano-2512', 'nano-mlt'],
        default='nano-2512',
        help='Fun-ASR-Nano 模型选择 (默认: nano-2512)'
    )
    parser.add_argument(
        '--nano-device',
        choices=['cpu', 'cuda'],
        default='cpu',
        help='Fun-ASR-Nano 设备选择 (默认: cpu)'
    )

    # 其他参数
    parser.add_argument(
        '--hotkey', '-x',
        default=DEFAULT_HOTKEY,
        help=f'快捷键 (默认: {DEFAULT_HOTKEY})'
    )
    parser.add_argument(
        '--no-auto-paste',
        action='store_true',
        help='禁用自动粘贴功能'
    )
    parser.add_argument(
        '--no-auto-copy',
        action='store_true',
        help='禁用自动复制到剪贴板功能'
    )

    # 智能选择参数
    parser.add_argument(
        '--smart', '-s',
        action='store_true',
        help='启用智能选择模式（自动选择最佳引擎）'
    )
    parser.add_argument(
        '--explain', '-e',
        action='store_true',
        help='显示引擎选择解释（需要 --smart 参数）'
    )
    parser.add_argument(
        '--scenario',
        choices=['realtime', 'transcription', 'meeting',
                 'multilingual', 'command', 'general'],
        help='强制指定场景类型（需要 --smart 参数）'
    )
    parser.add_argument(
        '--priority',
        choices=['latency', 'accuracy', 'balanced'],
        default='balanced',
        help='优先考虑因素: latency(延迟), accuracy(准确率), balanced(平衡) (默认: balanced)'
    )

    args = parser.parse_args()

    # 确定引擎
    asr_engine = args.asr

    # 确定引擎特定配置
    engine_kwargs = {}
    if asr_engine == 'moss':
        api_key = args.api_key or os.environ.get('MOSS_API_KEY', '')
        engine_kwargs['api_key'] = api_key
        engine_kwargs['model'] = args.moss_model

        if not api_key:
            print("❌ 错误: 使用 MOSS 需要提供 API Key")
            print("   使用方式:")
            print("   1. 在 .env 文件中设置 MOSS_API_KEY")
            print("   2. python voice_ime.py --asr moss --api-key YOUR_KEY")
            sys.exit(1)

    elif asr_engine == 'funasr':
        engine_kwargs['model'] = args.funasr_model
        engine_kwargs['device'] = args.funasr_device
        engine_kwargs['enable_diarization'] = args.enable_diarization

    elif asr_engine in ('nano-2512', 'nano-mlt'):
        engine_kwargs['model'] = args.nano_model
        engine_kwargs['device'] = args.nano_device

    # 确保 api_key 始终传递（用于回退到 MOSS）
    api_key = args.api_key or os.environ.get('MOSS_API_KEY', '')
    engine_kwargs['api_key'] = api_key

    # 确定快捷键
    hotkey = args.hotkey
    env_hotkey = os.environ.get('VOICE_IME_HOTKEY', '')
    if env_hotkey:
        hotkey = env_hotkey

    # 检查依赖
    try:
        import sounddevice
    except ImportError:
        print("❌ 缺少依赖: sounddevice")
        print("   请运行: pip install sounddevice")
        sys.exit(1)

    try:
        import keyboard
    except ImportError:
        print("❌ 缺少依赖: keyboard")
        print("   请运行: pip install keyboard")
        sys.exit(1)

    try:
        import pyperclip
    except ImportError:
        print("❌ 缺少依赖: pyperclip")
        print("   请运行: pip install pyperclip")
        sys.exit(1)

    # 检查 FunASR 依赖（非智能选择模式）
    if not args.smart and asr_engine == 'funasr':
        try:
            import funasr
        except ImportError:
            print("❌ 缺少依赖: funasr")
            print("   请运行: pip install funasr")
            sys.exit(1)

    # 启动程序
    print("\n✅ 配置完成，启动语音输入工具...")
    print("   按 ESC 可随时退出\n")

    app = VoiceIME(
        asr_engine=asr_engine,
        hotkey=hotkey,
        auto_paste=not args.no_auto_paste,
        auto_copy=not args.no_auto_copy,
        smart_mode=args.smart,
        explain=args.explain,
        scenario=args.scenario,
        priority=args.priority,
        **engine_kwargs
    )
    app.run()


if __name__ == "__main__":
    main()
