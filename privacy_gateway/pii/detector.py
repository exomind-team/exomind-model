"""
PII Detection Module
====================

PII 检测器：使用正则表达式检测文本中的隐私信息
"""

from dataclasses import dataclass
from typing import List, Optional

from .patterns import PIIType, PII_PATTERNS


@dataclass
class PIIDetectionResult:
    """PII 检测结果"""
    value: str
    pii_type: PIIType
    start: int
    end: int


class PIIDetector:
    """PII 检测器"""

    def __init__(self):
        """初始化检测器"""
        pass

    def detect(self, text: str) -> List[PIIDetectionResult]:
        """检测文本中的所有 PII"""
        results: List[PIIDetectionResult] = []

        for pii_pattern in PII_PATTERNS:
            pattern = pii_pattern.pattern
            for match in pattern.finditer(text):
                results.append(PIIDetectionResult(
                    value=match.group(),
                    pii_type=pii_pattern.pii_type,
                    start=match.start(),
                    end=match.end()
                ))

        results.sort(key=lambda x: x.start)
        return results

    def detect_types(self, text: str) -> List[PIIType]:
        """检测文本中包含的 PII 类型"""
        types = set()
        for pii_pattern in PII_PATTERNS:
            if pii_pattern.pattern.search(text):
                types.add(pii_pattern.pii_type)
        return list(types)

    def has_pii(self, text: str) -> bool:
        """检查文本是否包含 PII"""
        for pii_pattern in PII_PATTERNS:
            if pii_pattern.pattern.search(text):
                return True
        return False


_detector: Optional[PIIDetector] = None


def get_detector() -> PIIDetector:
    """获取全局检测器实例"""
    global _detector
    if _detector is None:
        _detector = PIIDetector()
    return _detector
