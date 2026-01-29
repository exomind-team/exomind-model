"""
PII Regex Patterns
==================

支持检测的隐私数据类型及其正则表达式：
- 手机号 (PHONE)
- 身份证号 (ID_CARD)
- 银行卡号 (CREDIT_CARD)
- 邮箱 (EMAIL)
"""

import re
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Pattern


class PIIType(str, Enum):
    """PII 类型枚举"""
    PHONE = "PHONE"
    ID_CARD = "ID_CARD"
    CREDIT_CARD = "CREDIT_CARD"
    EMAIL = "EMAIL"
    UNKNOWN = "UNKNOWN"


@dataclass
class PIIPattern:
    """PII 正则模式"""
    pii_type: PIIType
    pattern: Pattern[str]
    min_length: int
    max_length: int


# 正则模式定义
PII_PATTERNS: list[PIIPattern] = [
    # 手机号: 1开头，3-9开头，共11位
    PIIPattern(
        pii_type=PIIType.PHONE,
        pattern=re.compile(r"1[3-9]\d{9}"),
        min_length=11,
        max_length=11
    ),
    # 身份证号: 18位，最后一位可能是X
    PIIPattern(
        pii_type=PIIType.ID_CARD,
        pattern=re.compile(r"\d{17}[\dXx]"),
        min_length=18,
        max_length=18
    ),
    # 银行卡号: 62开头，16-19位
    PIIPattern(
        pii_type=PIIType.CREDIT_CARD,
        pattern=re.compile(r"6[2-9]\d{14,17}"),
        min_length=16,
        max_length=19
    ),
    # 邮箱地址
    PIIPattern(
        pii_type=PIIType.EMAIL,
        pattern=re.compile(r"[\w.-]+@[\w.-]+\.\w+"),
        min_length=5,
        max_length=254
    ),
]


def get_pattern_by_type(pii_type: PIIType) -> Optional[Pattern[str]]:
    """根据类型获取正则模式"""
    for p in PII_PATTERNS:
        if p.pii_type == pii_type:
            return p.pattern
    return None


def detect_pii_type(text: str) -> Optional[PIIType]:
    """检测文本对应的 PII 类型"""
    for p in PII_PATTERNS:
        if p.pattern.match(text):
            return p.pii_type
    return PIIType.UNKNOWN
