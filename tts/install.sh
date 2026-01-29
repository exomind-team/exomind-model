#!/bin/bash
# Qwen3-TTS 安装脚本 (CPU 版本)

echo "========================================"
echo "Qwen3-TTS 本地安装 (CPU)"
echo "========================================"

# 检查 Python 版本
python_version=$(python3 --version 2>&1)
echo "当前 Python 版本: $python_version"

if [[ ! "$python_version" =~ "3.1[0-9]" ]]; then
    echo "⚠️  建议使用 Python 3.10-3.12"
fi

# 创建虚拟环境
echo ""
echo "📦 创建虚拟环境..."
conda create -n qwen3-tts python=3.12 -y 2>/dev/null || \
    python3 -m venv qwen3-tts-venv

# 激活环境
echo ""
echo "🔄 激活虚拟环境..."
if command -v conda &> /dev/null; then
    eval "$(conda shell.bash hook)"
    conda activate qwen3-tts
else
    source qwen3-tts-venv/bin/activate
fi

# 安装依赖
echo ""
echo "⬇️  安装 qwen-tts..."
pip install -U qwen-tts

# 安装 soundfile（用于保存音频）
pip install soundfile

# 安装测试依赖
pip install scipy numpy

echo ""
echo "========================================"
echo "✅ 安装完成！"
echo "========================================"
echo ""
echo "使用方法:"
echo "  1. 激活环境: conda activate qwen3-tts"
echo "  2. 运行测试: python tts/test_qwen3_tts.py --mode custom"
echo ""
echo "支持的测试模式:"
echo "  --mode custom   # 预设音色（推荐新手）"
echo "  --mode design   # 自然语言设计音色"
echo "  --mode clone    # 3秒音频克隆"
echo "  --mode all      # 全部测试"
echo ""
