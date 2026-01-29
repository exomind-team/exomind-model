"""
PII Storage Module
==================

Token 持久化存储：JSON 文件存储映射关系
"""

import json
from pathlib import Path
from typing import Dict, Optional


class TokenStore:
    """Token 持久化存储"""

    def __init__(self, store_path: Path):
        """
        初始化存储

        Args:
            store_path: 存储文件路径
        """
        self.store_path = store_path
        self._data: Dict[str, dict] = {}

        # 确保目录存在
        self.store_path.parent.mkdir(parents=True, exist_ok=True)

        # 加载已有数据
        self._load()

    def _load(self):
        """从文件加载数据"""
        if self.store_path.exists():
            try:
                with open(self.store_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
            except (json.JSONDecodeError, IOError):
                self._data = {}

    def save(self):
        """保存数据到文件"""
        with open(self.store_path, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    def set(self, key: str, value: dict):
        """设置键值对"""
        self._data[key] = value
        self.save()

    def get(self, key: str) -> Optional[dict]:
        """获取值"""
        return self._data.get(key)

    def delete(self, key: str) -> bool:
        """删除键值对"""
        if key in self._data:
            del self._data[key]
            self.save()
            return True
        return False

    def clear(self):
        """清空所有数据"""
        self._data = {}
        self.save()

    def all(self) -> Dict[str, dict]:
        """获取所有数据"""
        return self._data.copy()

    def count(self) -> int:
        """获取数据数量"""
        return len(self._data)

    def keys(self):
        """获取所有键"""
        return self._data.keys()
