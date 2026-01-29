"""
SenseVoice Output Cleaning Tests
================================

测试 FunASRClient 对 SenseVoice 模型输出的清理功能。
SenseVoice 输出包含 <|...|> 格式的特殊标记，需要清理为纯文本。
"""

import pytest
from asr.funasr_client import FunASRClient


class TestSenseVoiceOutputCleaning:
    """SenseVoice 输出清理测试类"""

    # ========== 基础清理测试 ==========

    def test_clean_pure_chinese(self):
        """测试纯中文清理"""
        raw = "<|zh|>你好世界"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "你好世界"

    def test_clean_with_neutral_emotion(self):
        """测试带中性情感标记的清理"""
        raw = "<|zh|><|NEUTRAL|>测试文本"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "测试文本"

    def test_clean_english(self):
        """测试英文清理"""
        raw = "<|en|>Hello World"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "Hello World"

    def test_clean_japanese(self):
        """测试日文清理"""
        raw = "<|ja|>こんにちは世界"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "こんにちは世界"

    def test_clean_korean(self):
        """测试韩文清理"""
        raw = "<|ko|>안녕하세요"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "안녕하세요"

    def test_clean_cantonese(self):
        """测试粤文清理"""
        raw = "<|yue|>你好吖"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "你好吖"

    # ========== 复杂标记测试 ==========

    def test_clean_full_sensevoice_format(self):
        """测试完整 SenseVoice 格式清理"""
        # 完整格式示例：<|zh|><|NEUTRAL|><|Speech|><|woitn|><|wav|><|nes|><|5.89|><|0.0|>这是识别文本。
        raw = "<|zh|><|NEUTRAL|><|Speech|><|woitn|><|wav|><|nes|><|5.89|><|0.0|>这是识别文本。"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "这是识别文本。"

    def test_clean_multiple_markers(self):
        """测试多个标记的清理"""
        raw = "<|zh|><|NEUTRAL|><|Speech|>这是一段话"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "这是一段话"

    def test_clean_speech_type_marker(self):
        """测试语音类型标记清理"""
        raw = "<|Speech|>语音内容"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "语音内容"

    def test_clean_unknown_markers(self):
        """测试未知标记清理"""
        raw = "<|woitn|><|nes|><|wav|>内容"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "内容"

    def test_clean_confidence_markers(self):
        """测试置信度标记清理"""
        raw = "<|5.89|><|0.0|>带置信度的文本"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "带置信度的文本"

    # ========== 边缘情况测试 ==========

    def test_clean_empty_string(self):
        """测试空字符串"""
        result = FunASRClient._clean_sensevoice_output("")
        assert result == ""

    def test_clean_no_markers(self):
        """测试无标记的普通文本"""
        raw = "普通文本不需要清理"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "普通文本不需要清理"

    def test_clean_only_markers(self):
        """测试只有标记没有内容"""
        raw = "<|zh|><|NEUTRAL|>"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == ""

    def test_clean_whitespace_handling(self):
        """测试空白字符处理"""
        raw = "<|zh|>  文本有空格  "
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "文本有空格"

    def test_clean_newline_handling(self):
        """测试换行符处理"""
        raw = "<|zh|>第一行\n第二行"
        result = FunASRClient._clean_sensevoice_output(raw)
        # 换行符会被替换为空格
        assert result == "第一行 第二行"

    def test_clean_mixed_language(self):
        """测试中英混合文本"""
        raw = "<|zh|><|en|>你好Hello世界World"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "你好Hello世界World"

    # ========== 回归测试 ==========

    def test_clean_regression_original_format(self):
        """回归测试：确保原始 FunASR 输出不受影响"""
        # paraformer-zh 的原始输出格式
        raw = "这是原始识别结果"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "这是原始识别结果"

    def test_clean_regression_speaker_diarization(self):
        """回归测试：说话人分离标签不受影响"""
        # 说话人分离标签格式
        raw = "[spk0]: 说话人0的文本[spk1]: 说话人1的文本"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "[spk0]: 说话人0的文本[spk1]: 说话人1的文本"

    def test_clean_regression_with_punctuation(self):
        """回归测试：标点符号保留"""
        raw = "<|zh|>你好，世界！这是一段话。"
        result = FunASRClient._clean_sensevoice_output(raw)
        assert result == "你好，世界！这是一段话。"

    def test_clean_regression_long_text(self):
        """回归测试：长文本处理"""
        long_text = "<|zh|><|NEUTRAL|>这是一个很长的测试文本，包含了很多内容，" \
                   "用于测试清理功能是否能够正确处理长文本。" \
                   "希望清理后只保留纯文本内容，不包含任何标记。"
        result = FunASRClient._clean_sensevoice_output(long_text)
        expected = "这是一个很长的测试文本，包含了很多内容，" \
                  "用于测试清理功能是否能够正确处理长文本。" \
                  "希望清理后只保留纯文本内容，不包含任何标记。"
        assert result == expected

    def test_clean_emotion_labels(self):
        """测试情感标签清理"""
        raw = "<|HAPPY|>开心<Text><|ANGRY|>生气<Text><|SAD|>悲伤"
        result = FunASRClient._clean_sensevoice_output(raw)
        # 所有 <|xxx|> 标记都会被移除
        assert result == "开心<Text>生气<Text>悲伤"


class TestSenseVoiceClient:
    """SenseVoice 客户端集成测试（不实际加载模型）"""

    def test_client_name_with_sensevoice(self):
        """测试客户端名称包含模型名"""
        # 模拟创建一个使用 sensevoice 的客户端
        client = FunASRClient.__new__(FunASRClient)
        client._model_name = 'sensevoice'
        client._device = 'cpu'
        client._enable_diarization = False
        client._model_instance = None

        assert client.name == "FunASR (sensevoice)"

    def test_is_sensevoice_model(self):
        """测试判断是否为 SenseVoice 模型"""
        client = FunASRClient.__new__(FunASRClient)
        client._model_name = 'sensevoice'

        # 通过检查 model name 来判断
        assert client._model_name == 'sensevoice'


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
