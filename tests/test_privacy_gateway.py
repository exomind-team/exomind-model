"""
Unit Tests for Privacy Gateway
===============================

单元测试：PII 检测器、Tokenizer、API 端点
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
FILE = Path(__file__).resolve()
ROOT = FILE.parents[2] / "voice-ime"
sys.path.insert(0, str(ROOT))

from privacy_gateway.pii.patterns import PIIType, detect_pii_type
from privacy_gateway.pii.detector import PIIDetector, get_detector
from privacy_gateway.pii.tokenizer import PIITokenizer, get_tokenizer, reset_tokenizer
from privacy_gateway.storage.token_store import TokenStore
import tempfile
import json


class TestPIIPatterns:
    """PII 正则模式测试"""

    def test_phone_detection(self):
        """测试手机号检测"""
        assert detect_pii_type("13812345678") == PIIType.PHONE
        assert detect_pii_type("15987654321") == PIIType.PHONE
        assert detect_pii_type("19711112222") == PIIType.PHONE

    def test_phone_invalid(self):
        """测试无效手机号"""
        assert detect_pii_type("12812345678") == PIIType.UNKNOWN  # 2开头
        assert detect_pii_type("1381234567") == PIIType.UNKNOWN  # 10位
        assert detect_pii_type("138123456789") == PIIType.UNKNOWN  # 12位

    def test_id_card_detection(self):
        """测试身份证号检测"""
        assert detect_pii_type("110101199001011234") == PIIType.ID_CARD
        assert detect_pii_type("31010119900101123X") == PIIType.ID_CARD

    def test_credit_card_detection(self):
        """测试银行卡号检测"""
        assert detect_pii_type("6222021234567890") == PIIType.CREDIT_CARD
        assert detect_pii_type("6212345678901234") == PIIType.CREDIT_CARD

    def test_email_detection(self):
        """测试邮箱检测"""
        assert detect_pii_type("user@example.com") == PIIType.EMAIL
        assert detect_pii_type("test+tag@domain.org") == PIIType.EMAIL


class TestPIIDetector:
    """PII 检测器测试"""

    def setup_method(self):
        """每个测试前重置检测器"""
        self.detector = PIIDetector()

    def test_detect_phone(self):
        """测试检测手机号"""
        text = "张三的手机号是13812345678"
        results = self.detector.detect(text)

        assert len(results) == 1
        assert results[0].value == "13812345678"
        assert results[0].pii_type == PIIType.PHONE

    def test_detect_multiple_pii(self):
        """测试检测多个 PII"""
        text = "张三的手机号是13812345678，邮箱是zhangsan@email.com"
        results = self.detector.detect(text)

        assert len(results) == 2
        values = [r.value for r in results]
        assert "13812345678" in values
        assert "zhangsan@email.com" in values

    def test_detect_no_pii(self):
        """测试无 PII 情况"""
        text = "今天天气很好，适合出去散步"
        results = self.detector.detect(text)
        assert len(results) == 0

    def test_detect_types(self):
        """测试检测 PII 类型"""
        text = "手机13812345678，身份证110101199001011234"
        types = self.detector.detect_types(text)

        assert PIIType.PHONE in types
        assert PIIType.ID_CARD in types

    def test_has_pii(self):
        """测试 PII 存在性检查"""
        assert self.detector.has_pii("手机号13812345678") is True
        assert self.detector.has_pii("今天天气很好") is False


class TestPIITokenizer:
    """PII Tokenizer 测试"""

    def setup_method(self):
        """每个测试前重置 tokenizer"""
        reset_tokenizer()

    def test_tokenize_single(self):
        """测试单个 PII token 化"""
        tokenizer = PIITokenizer()
        token = tokenizer.tokenize("13812345678", PIIType.PHONE)

        assert token == "[PII_PHONE_1]"
        assert tokenizer.count() == 1

    def test_bijective_mapping(self):
        """测试双射映射（一一对应）"""
        tokenizer = PIITokenizer()

        token1 = tokenizer.tokenize("13812345678", PIIType.PHONE)
        token2 = tokenizer.tokenize("13812345678", PIIType.PHONE)

        # 同一个 PII 应该返回相同的 token
        assert token1 == token2
        assert tokenizer.count() == 1

    def test_different_pii_same_type(self):
        """测试同类型不同 PII"""
        tokenizer = PIITokenizer()

        token1 = tokenizer.tokenize("13812345678", PIIType.PHONE)
        token2 = tokenizer.tokenize("15987654321", PIIType.PHONE)

        # 不同 PII 应该返回不同的 token
        assert token1 != token2
        assert tokenizer.count() == 2

    def test_restore(self):
        """测试还原"""
        tokenizer = PIITokenizer()

        token = tokenizer.tokenize("13812345678", PIIType.PHONE)
        restored = tokenizer.restore(token)

        assert restored == "13812345678"

    def test_restore_unknown_token(self):
        """测试还原未知 token"""
        tokenizer = PIITokenizer()
        restored = tokenizer.restore("[UNKNOWN_TOKEN]")

        # 未知 token 应返回原值
        assert restored == "[UNKNOWN_TOKEN]"

    def test_get_pii_type(self):
        """测试获取 PII 类型"""
        tokenizer = PIITokenizer()
        token = tokenizer.tokenize("13812345678", PIIType.PHONE)

        pii_type = tokenizer.get_pii_type(token)
        assert pii_type == PIIType.PHONE


class TestTokenStore:
    """Token 存储测试"""

    def test_save_and_load(self):
        """测试保存和加载"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            store_path = Path(f.name)

        try:
            store = TokenStore(store_path)

            # 设置数据
            store.set("token1", {"value": "data1"})
            store.set("token2", {"value": "data2"})

            # 验证数量
            assert store.count() == 2

            # 加载新实例
            new_store = TokenStore(store_path)
            assert new_store.count() == 2
            assert new_store.get("token1")["value"] == "data1"

        finally:
            store_path.unlink(missing_ok=True)

    def test_delete(self):
        """测试删除"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            store_path = Path(f.name)

        try:
            store = TokenStore(store_path)
            store.set("token1", {"value": "data1"})

            # 删除
            result = store.delete("token1")
            assert result is True
            assert store.count() == 0

            # 删除不存在的键
            result = store.delete("nonexistent")
            assert result is False

        finally:
            store_path.unlink(missing_ok=True)

    def test_clear(self):
        """测试清空"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            store_path = Path(f.name)

        try:
            store = TokenStore(store_path)
            store.set("token1", {"value": "data1"})
            store.set("token2", {"value": "data2"})

            store.clear()
            assert store.count() == 0

        finally:
            store_path.unlink(missing_ok=True)


class TestIntegration:
    """集成测试"""

    def setup_method(self):
        """每个测试前重置"""
        reset_tokenizer()

    def test_protect_and_restore_flow(self):
        """测试完整的保护-还原流程"""
        tokenizer = PIITokenizer()
        detector = PIIDetector()

        # 原始文本
        original = "张三的手机号是13812345678，邮箱是zhangsan@email.com"

        # 保护
        pii_results = detector.detect(original)
        protected = original
        tokens = {}

        for pii in pii_results:
            token = tokenizer.tokenize(pii.value, pii.pi_type)
            protected = protected.replace(pii.value, token)
            tokens[token] = pii.value

        # 验证保护后文本不含原始 PII
        assert "13812345678" not in protected
        assert "zhangsan@email.com" not in protected
        assert "[PII_PHONE_1]" in protected
        assert "[PII_EMAIL_1]" in protected

        # 还原
        restored = protected
        for token, original_value in tokens.items():
            restored = restored.replace(token, original_value)

        # 验证还原后文本与原始文本一致
        assert restored == original

    def test_multiple_same_pii(self):
        """测试同一 PII 多次出现"""
        tokenizer = PIITokenizer()
        detector = PIIDetector()

        text = "我的手机号是13812345678，朋友的手机号也是13812345678"
        results = detector.detect(text)

        assert len(results) == 2
        assert results[0].value == results[1].value

        # Token 化后应该只生成一个 token
        protected = text
        token_map = {}
        for pii in results:
            token = tokenizer.tokenize(pii.value, pii.pi_type)
            protected = protected.replace(pii.value, token, 1)
            token_map[token] = pii.value

        # 检查 token 数量
        assert tokenizer.count() == 1


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
