"""
Engine API Endpoints
====================

引擎管理 API 端点。

提供：
- 列出所有可用引擎
- 获取引擎详细信息
- 引擎切换（热切换）
"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from engine import (
    EngineManager,
    EngineType,
    EngineInfo,
    get_engine_manager,
)
from service.models.response import ModelInfo, ModelListResponse

router = APIRouter(prefix="/v1/engine", tags=["Engine"])


@router.get("", response_model=dict)
async def list_all_engines():
    """
    列出所有可用的引擎（ASR + TTS + Speaker）

    返回所有已注册的引擎及其状态、能力、性能指标。
    """
    manager = get_engine_manager()

    return {
        "asr": [
            {
                "id": e.name,
                "name": e.display_name,
                "type": "asr",
                "status": "available" if e.available else "unavailable",
                "capabilities": e.capabilities,
                "priority": e.priority,
                "is_default": e.is_default,
                "description": e.description,
            }
            for e in manager.list_engines(EngineType.ASR)
        ],
        "tts": [
            {
                "id": e.name,
                "name": e.display_name,
                "type": "tts",
                "status": "available" if e.available else "unavailable",
                "capabilities": e.capabilities,
                "priority": e.priority,
                "is_default": e.is_default,
                "description": e.description,
            }
            for e in manager.list_engines(EngineType.TTS)
        ],
        "speaker": [
            {
                "id": e.name,
                "name": e.display_name,
                "type": "speaker",
                "status": "available" if e.available else "unavailable",
                "capabilities": e.capabilities,
                "priority": e.priority,
                "is_default": e.is_default,
                "description": e.description,
            }
            for e in manager.list_engines(EngineType.SPEAKER)
        ],
    }


@router.get("/asr", response_model=ModelListResponse)
async def list_asr_engines():
    """
    列出所有可用的 ASR 引擎

    返回 ASR 引擎列表及其详细信息。
    """
    manager = get_engine_manager()
    engines = manager.list_engines(EngineType.ASR)

    models = []
    for e in engines:
        models.append(ModelInfo(
            id=e.name,
            name=e.display_name,
            type="asr",
            status="available" if e.available else "unavailable",
            capabilities={
                "capabilities": e.capabilities,
                "is_default": e.is_default,
            },
            performance=None,
            default=e.is_default,
        ))

    return ModelListResponse(models=models)


@router.get("/tts", response_model=ModelListResponse)
async def list_tts_engines():
    """
    列出所有可用的 TTS 引擎

    返回 TTS 引擎列表及其详细信息。
    """
    manager = get_engine_manager()
    engines = manager.list_engines(EngineType.TTS)

    models = []
    for e in engines:
        models.append(ModelInfo(
            id=e.name,
            name=e.display_name,
            type="tts",
            status="available" if e.available else "unavailable",
            capabilities={
                "capabilities": e.capabilities,
                "is_default": e.is_default,
            },
            performance=None,
            default=e.is_default,
        ))

    return ModelListResponse(models=models)


@router.get("/speaker", response_model=ModelListResponse)
async def list_speaker_engines():
    """
    列出所有可用的 Speaker 引擎

    返回 Speaker 引擎列表及其详细信息。
    """
    manager = get_engine_manager()
    engines = manager.list_engines(EngineType.SPEAKER)

    models = []
    for e in engines:
        models.append(ModelInfo(
            id=e.name,
            name=e.display_name,
            type="speaker",
            status="available" if e.available else "unavailable",
            capabilities={
                "capabilities": e.capabilities,
                "is_default": e.is_default,
            },
            performance=None,
            default=e.is_default,
        ))

    return ModelListResponse(models=models)


@router.get("/default/{engine_type}")
async def get_default_engine(engine_type: str):
    """
    获取指定类型的默认引擎

    - **engine_type**: 引擎类型 (asr, tts, speaker)
    """
    manager = get_engine_manager()

    type_map = {
        "asr": EngineType.ASR,
        "tts": EngineType.TTS,
        "speaker": EngineType.SPEAKER,
    }

    if engine_type.lower() not in type_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown engine type: {engine_type}. Valid types: asr, tts, speaker"
        )

    default_engine = manager.get_default_engine(type_map[engine_type.lower()])
    if default_engine is None:
        raise HTTPException(
            status_code=404,
            detail=f"No default engine found for type: {engine_type}"
        )

    return {
        "engine_type": engine_type.lower(),
        "default_engine": default_engine,
    }


@router.get("/{engine_type}/{engine_name}")
async def get_engine_info(engine_type: str, engine_name: str):
    """
    获取指定引擎的详细信息

    - **engine_type**: 引擎类型 (asr, tts, speaker)
    - **engine_name**: 引擎名称
    """
    manager = get_engine_manager()

    # 解析引擎类型
    type_map = {
        "asr": EngineType.ASR,
        "tts": EngineType.TTS,
        "speaker": EngineType.SPEAKER,
    }

    if engine_type.lower() not in type_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown engine type: {engine_type}. Valid types: asr, tts, speaker"
        )

    engine_type_enum = type_map[engine_type.lower()]

    # 获取引擎信息
    info = manager.get_engine_info(engine_type_enum, engine_name)
    if info is None:
        raise HTTPException(
            status_code=404,
            detail=f"Engine not found: {engine_type}/{engine_name}"
        )

    return {
        "id": info.name,
        "name": info.display_name,
        "type": info.type.value,
        "status": "available" if info.available else "unavailable",
        "capabilities": info.capabilities,
        "priority": info.priority,
        "is_default": info.is_default,
        "description": info.description,
    }


@router.get("/default/{engine_type}")
async def get_default_engine(engine_type: str):
    """
    获取指定类型的默认引擎

    - **engine_type**: 引擎类型 (asr, tts, speaker)
    """
    manager = get_engine_manager()

    type_map = {
        "asr": EngineType.ASR,
        "tts": EngineType.TTS,
        "speaker": EngineType.SPEAKER,
    }

    if engine_type.lower() not in type_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown engine type: {engine_type}. Valid types: asr, tts, speaker"
        )

    default_engine = manager.get_default_engine(type_map[engine_type.lower()])
    if default_engine is None:
        raise HTTPException(
            status_code=404,
            detail=f"No default engine found for type: {engine_type}"
        )

    return {
        "engine_type": engine_type.lower(),
        "default_engine": default_engine,
    }


@router.post("/switch/{engine_type}")
async def switch_engine(
    engine_type: str,
    new_engine: str,
    test: bool = True
):
    """
    切换引擎（热切换）

    - **engine_type**: 引擎类型 (asr, tts)
    - **new_engine**: 目标引擎名称
    - **test**: 是否测试新引擎可用性（默认: True）
    """
    manager = get_engine_manager()

    type_map = {
        "asr": EngineType.ASR,
        "tts": EngineType.TTS,
    }

    if engine_type.lower() not in type_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown engine type: {engine_type}. Valid types: asr, tts"
        )

    engine_type_enum = type_map[engine_type.lower()]

    # 检查目标引擎是否存在
    config = manager.get_engine_config(engine_type_enum, new_engine)
    if config is None:
        raise HTTPException(
            status_code=404,
            detail=f"Engine not found: {new_engine}"
        )

    # 测试引擎可用性
    if test:
        if not manager.create_engine(engine_type_enum, new_engine).is_available():
            raise HTTPException(
                status_code=400,
                detail=f"Engine {new_engine} is not available"
            )

    # 切换引擎（创建新实例）
    old_engine = manager.get_default_engine(engine_type_enum)
    new_instance = manager.switch_engine(engine_type_enum, old_engine, new_engine)

    return {
        "success": True,
        "engine_type": engine_type.lower(),
        "old_engine": old_engine,
        "new_engine": new_engine,
        "message": f"Switched from {old_engine} to {new_engine}",
    }
