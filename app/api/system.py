"""
系统相关 API 路由

提供系统状态监控和配置管理功能
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
from loguru import logger

from app.services.milvus_service import milvus_service
from app.config import settings

router = APIRouter()


# ============================
# 请求/响应模型
# ============================

class MilvusStatusResponse(BaseModel):
    """Milvus 状态响应"""
    status: str
    collection_name: str
    num_entities: int
    host: str
    port: int


class SystemConfigResponse(BaseModel):
    """系统配置响应"""
    app_name: str
    app_version: str
    openai_model: str
    embedding_model: str
    milvus_host: str
    milvus_port: int


# ============================
# API 端点
# ============================

@router.get("/milvus-status", response_model=MilvusStatusResponse)
async def get_milvus_status():
    """
    获取 Milvus 向量数据库状态

    Returns:
        MilvusStatusResponse: Milvus 状态信息
    """
    try:
        info = milvus_service.get_collection_info()

        return MilvusStatusResponse(
            status="healthy",
            collection_name=info["name"],
            num_entities=info["num_entities"],
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )

    except Exception as e:
        logger.error(f"获取 Milvus 状态失败: {e}")
        return MilvusStatusResponse(
            status="error",
            collection_name=settings.MILVUS_COLLECTION_NAME,
            num_entities=0,
            host=settings.MILVUS_HOST,
            port=settings.MILVUS_PORT
        )


@router.get("/config", response_model=SystemConfigResponse)
async def get_system_config():
    """
    获取系统配置 (不包含敏感信息)

    Returns:
        SystemConfigResponse: 系统配置
    """
    return SystemConfigResponse(
        app_name=settings.APP_NAME,
        app_version=settings.APP_VERSION,
        openai_model=settings.OPENAI_CHAT_MODEL,
        embedding_model=settings.OPENAI_EMBEDDING_MODEL,
        milvus_host=settings.MILVUS_HOST,
        milvus_port=settings.MILVUS_PORT
    )


@router.get("/health")
async def health_check():
    """
    系统健康检查

    检查所有依赖服务的状态

    Returns:
        Dict: 健康状态
    """
    health_status = {
        "app": "healthy",
        "milvus": "unknown",
        "openai": "unknown"
    }

    # 检查 Milvus
    try:
        milvus_service.get_collection_info()
        health_status["milvus"] = "healthy"
    except Exception as e:
        logger.warning(f"Milvus 健康检查失败: {e}")
        health_status["milvus"] = f"unhealthy: {str(e)}"

    # 检查 OpenAI
    try:
        from app.services.embedding_service import get_embedding
        test_embedding = get_embedding("test")
        if test_embedding:
            health_status["openai"] = "healthy"
    except Exception as e:
        logger.warning(f"OpenAI 健康检查失败: {e}")
        health_status["openai"] = f"unhealthy: {str(e)}"

    # 计算整体健康状态
    if all(status == "healthy" for status in health_status.values()):
        overall_status = "healthy"
    else:
        overall_status = "degraded"

    return {
        "status": overall_status,
        "details": health_status
    }
