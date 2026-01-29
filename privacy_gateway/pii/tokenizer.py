"""
PII Tokenizer Module
====================

Token 生成器：将 PII 替换为可逆的 token
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json
from pathlib import Path

from .patterns import PIIType
from ..config import settings


@dataclass
class TokenInfo:
    """Token 信息"""
    token: str
    pii_value: str
    pii_type: PIIType
    created_at: str


class PIITokenizer:
    """PII Token 生成器（支持一一映射）"""

    def __init__(self, store_path: Optional[Path] = None):
        """
        初始化 Tokenizer

        Args:
            store_path: Token 存储文件路径
        """
        self.store_path = store_path or settings.token_store_path
        self._forward_map: Dict[str, str] = {}  # PII -> Token
        self._reverse_map: Dict[str, str] = {}  # Token -> PII
        self._token_info: Dict[str, TokenInfo] = {}  # Token -> Info
        self._counter: Dict[str, int] = {}  # 类型计数器

        # 加载已有存储
        self._load()

    def tokenize(
        self,
        pii_value: str,
        pii_type: PIIType,
        custom_id: Optional[str] = None
    ) -> str:
        """
        将 PII 转换为 token（一一映射）

        Args:
            pii_value: 原始 PII 值
            pii_type: PII 类型
            custom_id: 自定义 ID（可选）

        Returns:
            Token 字符串
        """
        # 检查是否已有映射
        if pii_value in self._forward_map:
            return self._forward_map[pii_value]

        # 生成唯一 token
        if custom_id:
            token_id = custom_id
        else:
            # 类型计数器，确保同类型 token 序号递增
            type_key = pii_type.value
            if type_key not in self._counter:
                self._counter[type_key] = 0
            self._counter[type_key] += 1
            token_id = str(self._counter[type_key])

        token = settings.token_prefix.format(
            type=pii_type.value,
            id=token_id
        )

        # 建立双向映射
        self._forward_map[pii_value] = token
        self._reverse_map[token] = pii_value

        # 记录 token 信息
        from datetime import datetime, timezone
        self._token_info[token] = TokenInfo(
            token=token,
            pii_value=pii_value,
            pii_type=pii_type,
            created_at=datetime.now(timezone.utc).isoformat()
        )

        return token

    def restore(self, token: str) -> str:
        """
        从 token 还原原始 PII

        Args:
            token: Token 字符串

        Returns:
            原始 PII 值（如果未找到，返回原 token）
        """
        return self._reverse_map.get(token, token)

    def get_pii_type(self, token: str) -> Optional[PIIType]:
        """
        获取 token 对应的 PII 类型

        Args:
            token: Token 字符串

        Returns:
            PII 类型
        """
        info = self._token_info.get(token)
        return info.pii_type if info else None

    def get_all_tokens(self) -> List[str]:
        """获取所有 token 列表"""
        return list(self._reverse_map.keys())

    def count(self) -> int:
        """获取映射数量"""
        return len(self._forward_map)

    def clear(self):
        """清空所有映射"""
        self._forward_map.clear()
        self._reverse_map.clear()
        self._token_info.clear()
        self._counter.clear()
        self._save()

    def _load(self):
        """从文件加载映射"""
        if self.store_path and self.store_path.exists():
            try:
                with open(self.store_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._forward_map = data.get('forward', {})
                    self._reverse_map = data.get('reverse', {})
                    # 重建 counter
                    for token, pii in self._reverse_map.items():
                        if token.startswith('[PII_'):
                            parts = token.split('_')
                            if len(parts) >= 3:
                                type_key = '_'.join(parts[1:-1])
                                try:
                                    num = int(parts[-1].rstrip(']'))
                                    if type_key not in self._counter or self._counter[type_key] < num:
                                        self._counter[type_key] = num
                                except ValueError:
                                    pass
            except (json.JSONDecodeError, IOError):
                pass

    def _save(self):
        """保存映射到文件"""
        if self.store_path:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            data = {
                'forward': self._forward_map,
                'reverse': self._reverse_map,
                'version': '1.0'
            }
            with open(self.store_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def save(self):
        """手动保存映射"""
        self._save()


# 全局 tokenizer 实例
_tokenizer: Optional[PIITokenizer] = None


def get_tokenizer(store_path: Optional[Path] = None) -> PIITokenizer:
    """获取全局 tokenizer 实例"""
    global _tokenizer
    if _tokenizer is None:
        _tokenizer = PIITokenizer(store_path)
    return _tokenizer


def reset_tokenizer():
    """重置全局 tokenizer"""
    global _tokenizer
    _tokenizer = None
