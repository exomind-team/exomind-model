# Fun-CosyVoice3 TTS 调试日志

**创建日期**: 2026-01-28
**作者**: 小荷 (Claude Code)

---

## 1. 环境配置

### 当前环境
| 组件 | 版本 | 说明 |
|------|------|------|
| Python | 3.11 | |
| PyTorch | 2.10.0+cpu | voice-ime 虚拟环境 (CPU only) |
| Fun-CosyVoice3 | 0.5B | 模型路径: `/home/hailay/rocm-install/CosyVoice/pretrained_models/Fun-CosyVoice3-0.5B` |

### 另一个 ROCm 环境
| 组件 | 版本 | 目标 GPU |
|------|------|----------|
| PyTorch ROCm | 7.11 | GFX 1031 (RX 6750 GRE) |

---

## 2. 遇到的问题

### 问题 1: `ModuleNotFoundError: No module named 'cosyvoice.cli'`
**原因**: 路径设置错误
**解决**: 添加 `sys.path` 和 `os.chdir()`

### 问题 2: `CosyVoice3.__init__() got an unexpected keyword argument 'device'`
**原因**: CosyVoice3 不接受 device 参数
**解决**: 移除 device 参数

### 问题 3: `ModuleNotFoundError: No module named 'matcha.models'`
**原因**: Matcha-TTS 未安装
**解决**: `uv pip install -e third_party/Matcha-TTS`

### 问题 4: `ImportError: cannot import name 'cached_download'`
**原因**: huggingface_hub 0.24+ 移除了 cached_download
**解决**: 添加兼容性补丁
```python
import huggingface_hub
from huggingface_hub import hf_hub_download
huggingface_hub.cached_download = hf_hub_download
```

### 问题 5: `std::bad_alloc` (ROCm PyTorch)
**原因**: ROCm PyTorch 在 GPU 推理模式下崩溃
**解决**: 创建单独的 CPU 虚拟环境

### 问题 6: ROCm GPU 推理失败
**当前状态**: ❌ **官方不支持 ROCm**
**现象**: PyTorch 显示 `ROCm available: False`
**搜索结果**:
- GitHub Issues: 无 ROCm 相关讨论
- README.md: 仅支持 CUDA，无 ROCm 说明
- **结论**: Fun-CosyVoice3 官方不直接支持 AMD ROCm GPU

---

## 3. ROCm 实验性分支调查结果 (2026-01-28)

### 搜索结果
| 来源 | ROCm 支持 | 实验性分支 |
|------|-----------|-----------|
| GitHub Issues | ❌ 无相关讨论 | ❌ 未发现 |
| README.md | ❌ 无官方说明 | ❌ 未提及 |
| 官方文档 | ❌ 仅支持 CUDA | ❌ 无 |

### 结论
**Fun-CosyVoice3 官方不支持 AMD ROCm**，没有任何实验性分支修复此问题。

### 替代方案
- **NVIDIA GPU**: TensorRT-LLM 加速 (~4x)
- **CPU**: 使用 CPU 版本但速度慢 (RTF 4x)
- **AMD GPU**: 需等待官方 ROCm 支持或换 NVIDIA 显卡

---

## 4. 当前配置 (tts.py)

```python
def synthesize(self, text, ..., volume=2.0, speed=1.1):
    # 默认 prompt
    prompt_text = "A gentle female voice, soft and warm.<|endofprompt|>小荷 在说话。"
```

### 参数说明
| 参数 | 当前值 | 说明 |
|------|--------|------|
| volume | 2.0 | 音量放大 2 倍 (+6dB) |
| speed | 1.1 | 语速正常偏快 |
| prompt | A gentle female voice, soft and warm. | 音色引导 |

---

## 5. 性能测试结果

### CPU 模式 (PyTorch 2.10.0+cpu)
| 指标 | 数值 |
|------|------|
| 模型加载 | 5.75s |
| 短句 (3s 音频) | 12.38s |
| 中句 (6s 音频) | 25.83s |
| 平均 RTF | **4.06x** |

### 结论
- 生成 1 秒音频需要 ~4 秒 (CPU)
- **RTF 4x** 意味着无法实时交互
- 需要 GPU 加速才能实现实时 TTS

---

## 6. TTS 方案对比

### 🎯 当前最佳方案: **Piper TTS**
| 指标 | Piper | Fun-CosyVoice3 (CPU) |
|------|-------|---------------------|
| RTF | **0.03x** (33x 加速) | 4x |
| 质量 | ⭐⭐ (偏低) | ⭐⭐⭐⭐ |
| 离线 | ✅ | ✅ |
| 免费 | ✅ | ✅ |
| GPU | 不需要 | ROCm 不支持 |

### 为什么不选 Fun-CosyVoice3
- ❌ 官方不支持 AMD ROCm
- ❌ CPU 推理太慢 (RTF 4x)
- ❌ 无法实时交互
- ❌ 没有实验性分支修复

### 推荐策略
1. **日常使用**: Piper TTS (快，省资源)
2. **高质量需求**: Edge-TTS (云端，付费)
3. **等 AMD GPU**: 等待官方 ROCm 支持或换 NVIDIA 显卡

---

## 7. 关键技术原理

### Fun-CosyVoice3 架构
```
文本 → [LLM 0.5B] → Token → [Flow Decoder] → 梅尔频谱 → [HiFi-GAN] → 音频
        ↓
    CPU 耗时占比 ~60%
```

### 加速方案对比
| 方案 | 加速比 | 要求 |
|------|--------|------|
| CPU 当前 | 1x | 无 |
| ROCm GPU | 5~10x | AMD GPU + ROCm (官方不支持) |
| vLLM | 2~5x | GPU |
| TensorRT | 3~10x | NVIDIA GPU |

---

## 8. 生成的样本文件

位置: `/home/hailay/rocm-install/CosyVoice/`

| 文件 | 内容 |
|------|------|
| `小荷_v2_早安问候.wav` | "早安呀，今天也要元气满满哦" |
| `小荷_v2_关心提醒.wav` | "别太累了，记得多喝水休息一下" |
| `小荷_v2_鼓励打气.wav` | "你已经很棒了，继续加油，我相信你" |
| `小荷_v2_晚安祝福.wav` | "晚安，做个好梦，明天见" |
| `小荷_v2_日常闲聊.wav` | "今天过得怎么样呀？有什么开心的事吗" |
| `小荷_v2_温柔提醒.wav` | "别忘了早点睡哦，晚睡对皮肤不好" |

---

*最后更新: 2026-01-28 18:57*
