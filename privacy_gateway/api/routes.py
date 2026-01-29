"""
Privacy Gateway API Routes
===========================

API 路由定义
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime, timezone

from ..pii.detector import get_detector
from ..pii.tokenizer import get_tokenizer, reset_tokenizer
from ..pii.patterns import PIIType


# 路由定义
router = APIRouter(prefix="/v1/privacy", tags=["privacy"])


# 请求/响应模型
class ProtectRequest(BaseModel):
    """隐私保护请求"""
    text: str
    encrypt_tokens: bool = False  # MVP 版本暂不实现加密


class ProtectResponse(BaseModel):
    """隐私保护响应"""
    protected_text: str
    tokens: Dict[str, str]
    metadata: dict


class RestoreRequest(BaseModel):
    """隐私还原请求"""
    text: str
    tokens: Dict[str, str]


class RestoreResponse(BaseModel):
    """隐私还原响应"""
    restored_text: str
    metadata: dict


class StatusResponse(BaseModel):
    """状态响应"""
    enabled: bool
    token_count: int
    pii_types: List[str]


@router.post("/protect", response_model=ProtectResponse)
async def protect_text(request: ProtectRequest) -> ProtectResponse:
    """
    保护文本：将 PII 替换为 token

    Args:
        request: 保护请求

    Returns:
        保护后的文本和 token 映射
    """
    detector = get_detector()
    tokenizer = get_tokenizer()

    # 检测 PII
    pii_results = detector.detect(request.text)

    if not pii_results:
        return ProtectResponse(
            protected_text=request.text,
            tokens={},
            metadata={"pii_count": 0, "processing_time_ms": 0}
        )

    # Token 化
    protected_text = request.text
    tokens: Dict[str, str] = {}

    for pii in pii_results:
        token = tokenizer.tokenize(pii.value, pii.pii_type)
        protected_text = protected_text.replace(pii.value, token)

        # 收集 token 映射（token -> 原始值，用于还原）
        tokens[token] = pii.value

    # 保存 tokenizer 状态
    tokenizer.save()

    return ProtectResponse(
        protected_text=protected_text,
        tokens=tokens,
        metadata={
            "pii_count": len(pii_results),
            "types_detected": list(set(r.pii_type.value for r in pii_results))
        }
    )


@router.post("/restore", response_model=RestoreResponse)
async def restore_text(request: RestoreRequest) -> RestoreResponse:
    """
    还原文本：将 token 替换回原始 PII

    Args:
        request: 还原请求

    Returns:
        还原后的文本
    """
    tokenizer = get_tokenizer()

    restored_text = request.text

    # 还原所有 token
    for token, original_value in request.tokens.items():
        restored_text = restored_text.replace(token, original_value)

    return RestoreResponse(
        restored_text=restored_text,
        metadata={"tokens_restored": len(request.tokens)}
    )


@router.get("/status", response_model=StatusResponse)
async def get_status() -> StatusResponse:
    """获取隐私网关状态"""
    tokenizer = get_tokenizer()

    return StatusResponse(
        enabled=True,
        token_count=tokenizer.count(),
        pii_types=[t.value for t in PIIType if t != PIIType.UNKNOWN]
    )


@router.post("/clear")
async def clear_tokens():
    """清空所有 token 映射"""
    tokenizer = get_tokenizer()
    tokenizer.clear()
    reset_tokenizer()
    return {"status": "cleared", "message": "All token mappings have been cleared"}


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "privacy-gateway",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
