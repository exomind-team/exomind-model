#!/bin/bash
#
# VoiceIME 启动脚本
# 使用 uv 管理 Python 环境
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "============================================================"
echo "🎤 VoiceIME 语音输入工具"
echo "============================================================"
echo ""

# 获取 uv 路径（sudo 时需要完整路径）
UV_BIN=""
if command -v uv &> /dev/null; then
    UV_BIN=$(command -v uv)
elif [ -f "$HOME/.local/bin/uv" ]; then
    UV_BIN="$HOME/.local/bin/uv"
fi

if [ -z "$UV_BIN" ]; then
    echo "❌ 未检测到 uv，请先安装："
    echo "   curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "✅ uv 版本: $("$UV_BIN" --version)"

# 加载 .env 文件（如果存在）
if [ -f ".env" ]; then
    echo "📄 加载 .env 配置文件..."
    set -a  # 自动导出变量
    source .env
    set +a
fi

# 检查并创建虚拟环境
if [ ! -d ".venv" ]; then
    echo ""
    echo "📦 正在创建 Python 虚拟环境..."
    "$UV_BIN" venv
fi

echo ""
echo "📦 正在安装/更新依赖..."
"$UV_BIN" pip install -e . python-dotenv

# 检查 API Key
if [ -z "$MOSS_API_KEY" ]; then
    echo ""
    echo "⚠️  未设置 MOSS_API_KEY"
    echo "   请在 .env 文件中设置或直接输入："
    read -p "🔑 请输入 MOSS API Key: " API_KEY
    if [ -n "$API_KEY" ]; then
        export MOSS_API_KEY="$API_KEY"
    else
        echo "❌ 需要 API Key 才能运行"
        exit 1
    fi
fi

# 构建命令行参数
ARGS=()
if [ -n "$VOICE_IME_HOTKEY" ]; then
    ARGS+=("--hotkey" "$VOICE_IME_HOTKEY")
fi

if [ "$VOICE_IME_AUTO_PASTE" == "false" ]; then
    ARGS+=("--no-auto-paste")
fi

if [ "$VOICE_IME_AUTO_COPY" == "false" ]; then
    ARGS+=("--no-auto-copy")
fi

echo ""
echo "🚀 启动 VoiceIME..."
echo "   快捷键: ${VOICE_IME_HOTKEY:-f2}"
echo "   自动复制: ${VOICE_IME_AUTO_COPY:-true}"
echo "   自动粘贴: ${VOICE_IME_AUTO_PASTE:-true}"
echo "   按 ESC 可退出程序"
echo ""

# 检查是否需要 sudo（Linux 上 keyboard 库需要 root）
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    if [ "$EUID" -ne 0 ]; then
        echo "⚠️  注意: Linux 上快捷键监听需要 root 权限"
        echo ""
        read -p "是否使用 sudo 运行? (y/n) " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            # 先输入密码
            echo "请输入密码（用于安装依赖和运行程序）..."
            read -s MOSS_SUDO_PASSWORD
            echo ""

            # 授权 root 访问 X server
            echo "🔐 授权 root 访问 X server..."
            xhost +SI:localuser:root 2>/dev/null || true

            # 检查系统依赖是否已安装（首次运行时安装）
            SYS_DEPS_MARKER=".voice_ime_sys_deps_installed"
            if [ ! -f "$SYS_DEPS_MARKER" ]; then
                echo "🔧 首次运行，正在安装系统依赖..."
                echo "$MOSS_SUDO_PASSWORD" | sudo -S apt-get update -qq
                echo "$MOSS_SUDO_PASSWORD" | sudo -S apt-get install -y -qq libportaudio2 python3-tk python3-dev xclip 2>/dev/null
                touch "$SYS_DEPS_MARKER"
                echo "✅ 系统依赖安装完成"
            else
                echo "✅ 系统依赖已安装（跳过）"
            fi

            # 保留环境变量并用完整路径运行
            export MOSS_API_KEY="$MOSS_API_KEY"
            export VOICE_IME_HOTKEY="$VOICE_IME_HOTKEY"
            export VOICE_IME_AUTO_COPY="$VOICE_IME_AUTO_COPY"
            export VOICE_IME_AUTO_PASTE="$VOICE_IME_AUTO_PASTE"
            # 传递 DISPLAY 和 Xauthority 以支持 pyautogui
            export DISPLAY="${DISPLAY:-:0}"
            export XAUTHORITY="${XAUTHORITY:-$HOME/.Xauthority}"

            exec sudo -E PATH="$PATH" HOME="$HOME" DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" "$UV_BIN" run python voice_ime.py "${ARGS[@]}" "$@"
        fi
    fi
fi

# 激活虚拟环境并运行
"$UV_BIN" run python voice_ime.py "${ARGS[@]}" "$@"
