# VoiceIME 用户教程

> **版本**: v1.0.0
> **更新日期**: 2026-01-27
> **适用版本**: VoiceIME v1.0.0+

---

## 目录

1. [简介](#1-简介)
2. [安装](#2-安装)
3. [快速开始](#3-快速开始)
4. [配置选项](#4-配置选项)
5. [使用示例](#5-使用示例)
6. [故障排除](#6-故障排除)
7. [常见问题](#7-常见问题)

---

## 1. 简介

VoiceIME 是一个**全局语音输入工具**，通过快捷键触发语音录制，自动识别并输入到目标应用。

### 核心特性

- ✅ **本地识别**：使用 FunASR，无需联网，保护隐私
- ✅ **云端识别**：支持 MOSS API，更高精度
- ✅ **热切换**：一键切换引擎，无需重启
- ✅ **自动回退**：本地失败自动切换云端
- ✅ **自动输入**：录音完成后自动粘贴到目标应用

### 支持平台

| 平台 | 状态 | 说明 |
|------|------|------|
| Ubuntu 24.04 | ✅ 已测试 | 本次开发环境 |
| Windows | ⚠️ 未测试 | 理论兼容 |
| macOS | ⚠️ 未测试 | 理论兼容 |

---

## 2. 安装

### 2.1 系统依赖

```bash
# Ubuntu/Debian
sudo apt-get install portaudio19-dev python3-pyaudio

# Fedora/RHEL
sudo dnf install portaudio-devel

# Arch Linux
sudo pacman -S portaudio
```

### 2.2 安装 VoiceIME

```bash
# 克隆项目
cd 1-Projects/exomind-model

# 使用 uv 安装依赖
uv pip install -e .

# 或者使用 pip
pip install -e .
```

### 2.3 完整依赖（包含 FunASR）

如果需要使用本地 FunASR 引擎：

```bash
# 安装 PyTorch CPU 版本（必须）
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install torchaudio --index-url https://download.pytorch.org/whl/cpu

# 安装 VoiceIME 和 FunASR
uv pip install -e .
uv pip install funasr>=1.0.0
```

> **注意**：PyTorch 约 2-3GB，首次安装可能需要 5-10 分钟。

---

## 3. 快速开始

### 3.1 首次运行

```bash
uv run python voice_ime.py
```

首次运行时会：
1. 下载 FunASR 模型（约 400MB）
2. 显示快捷键提示
3. 进入监听状态

### 3.2 基本使用

```
┌────────────────────────────────────────────────────┐
│                    使用流程                         │
├────────────────────────────────────────────────────┤
│                                                     │
│  1. 按 F2 键        →  听到 "滴" 一声，开始录音     │
│                                                     │
│  2. 说话...                                       │
│                                                     │
│  3. 再次按 F2 键    →  听到 "滴" 两声，停止录音     │
│                                                     │
│  4. 自动识别        →  结果复制到剪贴板             │
│                                                     │
│  5. 切换到目标应用  →  自动粘贴（可选）             │
│                                                     │
└────────────────────────────────────────────────────┘
```

### 3.3 退出程序

按 `ESC` 键退出程序。

---

## 4. 配置选项

### 4.1 命令行参数

#### 基础参数

| 参数 | 短选项 | 默认值 | 说明 |
|------|--------|--------|------|
| `--asr` | `-a` | `funasr` | ASR 引擎选择 |
| `--api-key` | `-k` | 环境变量 | API Key |
| `--hotkey` | `-x` | `f2` | 快捷键 |

#### FunASR 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--funasr-model` | `paraformer-zh` | 模型选择 |
| `--funasr-device` | `cpu` | 设备选择 |

#### MOSS 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--moss-model` | `moss-transcribe-diarize` | 模型选择 |

#### 其他参数

| 参数 | 说明 |
|------|------|
| `--no-auto-paste` | 禁用自动粘贴 |
| `--no-auto-copy` | 禁用自动复制 |

### 4.2 环境变量

在 `.env` 文件中配置：

```bash
# ASR 引擎选择 (funasr | moss)
ASR_ENGINE=funasr

# FunASR 配置
FUNASR_MODEL=paraformer-zh
FUNASR_DEVICE=cpu

# MOSS 配置
MOSS_API_KEY=your_api_key_here

# 快捷键配置
VOICE_IME_HOTKEY=f2

# 自动操作
VOICE_IME_AUTO_COPY=true
VOICE_IME_AUTO_PASTE=true
```

### 4.3 引擎选择优先级

```
命令行参数 > 环境变量 > 配置文件 > 默认值
```

示例：
```bash
# 命令行参数优先
uv run python voice_ime.py --asr moss --api-key sk-xxx

# 使用环境变量
echo "ASR_ENGINE=funasr" > .env
uv run python voice_ime.py
```

---

## 5. 使用示例

### 5.1 使用本地 FunASR（默认）

```bash
# 使用默认配置
uv run python voice_ime.py

# 指定模型
uv run python voice_ime.py --funasr-model paraformer-zh
uv run python voice_ime.py --funasr-model sensevoice
uv run python voice_ime.py --funasr-model paraformer-en
```

### 5.2 使用 MOSS 云端

```bash
# 需要 API Key
uv run python voice_ime.py --asr moss --api-key YOUR_KEY

# 或在 .env 中配置
echo "MOSS_API_KEY=your_key" >> .env
uv run python voice_ime.py --asr moss
```

### 5.3 自定义快捷键

```bash
# 使用 Alt+Space
uv run python voice_ime.py --hotkey alt+space

# 使用 Ctrl+Alt+S
uv run python voice_ime.py --hotkey ctrl+alt+s
```

### 5.4 禁用自动粘贴

如果只想复制到剪贴板，不自动粘贴：

```bash
uv run python voice_ime.py --no-auto-paste
```

---

## 6. 故障排除

### 6.1 常见错误

#### 错误：ModuleNotFoundError: No module named 'torch'

**原因**：FunASR 依赖未安装

**解决**：
```bash
uv pip install torch --index-url https://download.pytorch.org/whl/cpu
uv pip install torchaudio --index-url https://download.pytorch.org/whl/cpu
```

#### 错误：无法启动录音

**原因**：sounddevice 权限问题

**解决**：
```bash
# Ubuntu 检查音频设备
arecord -l

# 重新安装 sounddevice
uv pip uninstall sounddevice
uv pip install sounddevice
```

#### 错误：FunASR 模型下载失败

**原因**：网络问题或 ModelScope 连接失败

**解决**：
```bash
# 手动下载模型
mkdir -p ~/.cache/modelscope/hub/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch
# 从 https://www.modelscope.cn/models/iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch 下载
```

#### 错误：快捷键无响应

**原因**：keyboard 库权限问题

**解决**：
```bash
# 添加当前用户到 input 组
sudo usermod -aG input $USER

# 或使用 root 权限运行（不推荐）
sudo uv run python voice_ime.py
```

### 6.2 日志查看

运行程序时添加 `-v` 参数查看详细日志：

```bash
uv run python voice_ime.py -v
```

### 6.3 清理缓存

如果模型下载出错，清理缓存后重试：

```bash
# 清理 FunASR 模型缓存
rm -rf ~/.cache/modelscope/hub/models/iic/

# 清理临时文件
rm -rf ~/.voice_ime/temp/
```

---

## 7. 常见问题

### Q1: FunASR 和 MOSS 有什么区别？

| 特性 | FunASR (本地) | MOSS (云端) |
|------|---------------|-------------|
| **网络依赖** | ❌ 无需联网 | ✅ 需要联网 |
| **隐私** | ✅ 本地处理 | ⚠️ 数据上传 |
| **速度** | 快（实时 3.6x） | 取决于网络 |
| **准确度** | 高 | 更高 |
| **API Key** | ❌ 不需要 | ✅ 需要 |
| **费用** | 免费 | 按量计费 |
| **首次加载** | 30-60 秒 | 即时 |

### Q2: 如何选择模型？

| 场景 | 推荐模型 | 说明 |
|------|----------|------|
| 日常中文输入 | `paraformer-zh` | 通用模型，平衡速度和准确度 |
| 高精度需求 | `sensevoice` | 更准确，但模型更大 |
| 英文输入 | `paraformer-en` | 专门优化英文 |
| 电话录音 | `telephone` | 优化电话场景 |

### Q3: AMD GPU 能用吗？

**答案**：暂不支持

原因：
- FunASR GPU 加速依赖 NVIDIA CUDA
- AMD GPU 需要使用 ROCm，但 RX 6750 GRE 不支持 ROCm 5.7+
- 当前版本默认使用 CPU，性能已经很好（实时 3.6x）

### Q4: 如何自定义提示音？

提示音使用 pyaudio 生成，暂不支持自定义。如需禁用：

```python
# 在 voice_ime.py 中注释掉 beep() 调用
# self.beep(frequency=880, duration=0.15)
```

### Q5: 如何在后台运行？

```bash
# 使用 nohup
nohup uv run python voice_ime.py > voice_ime.log 2>&1 &

# 查看日志
tail -f voice_ime.log

# 停止程序
pkill -f voice_ime.py
```

---

## 8. 技术参考

### 8.1 目录结构

```
exomind-model/
├── voice_ime.py        # 主程序
├── asr/                # ASR 引擎模块
│   ├── base.py         # 抽象基类
│   ├── factory.py      # 工厂类
│   ├── moss_client.py  # MOSS 引擎
│   └── funasr_client.py # FunASR 引擎
├── test_funasr.py      # 测试文件
├── .env.example        # 配置模板
├── requirements.txt    # 依赖列表
└── docs/
    ├── README.md       # 教程（本文档）
    └── PRD.md          # 产品需求文档
```

### 8.2 音频格式要求

| 参数 | 值 |
|------|-----|
| 采样率 | 16kHz |
| 声道 | 单声道 (mono) |
| 位深度 | 16-bit |
| 格式 | WAV |

### 8.3 相关链接

- [FunASR GitHub](https://github.com/alibaba-damo-academy/FunASR)
- [MOSS API 文档](https://studio.mosi.cn/docs/moss-transcribe-diarize)
- [ModelScope 模型下载](https://www.modelscope.cn/models/iic/)

---

> **反馈渠道**：如有问题，请在项目 Issue 中反馈
> **更新日志**：见 [CHANGELOG.md](agent.md)
