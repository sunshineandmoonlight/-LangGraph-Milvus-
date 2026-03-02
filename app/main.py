"""
FastAPI 主应用

企业级多智能体系统的后端入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
import sys

from app.config import settings
from app.api import agent, knowledge, system, auth, session

# 配置日志
logger.remove()
logger.add(
    sys.stdout,
    level=settings.LOG_LEVEL,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
)

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 LangGraph 和 Milvus 的企业级多智能体系统"
)

# ============================
# CORS 配置
# ============================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境请设置具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# 路由注册
# ============================

app.include_router(
    agent.router,
    prefix=f"{settings.API_PREFIX}/agent",
    tags=["Agent"]
)

app.include_router(
    knowledge.router,
    prefix=f"{settings.API_PREFIX}/knowledge",
    tags=["Knowledge"]
)

app.include_router(
    system.router,
    prefix=f"{settings.API_PREFIX}/system",
    tags=["System"]
)

app.include_router(
    auth.router,
    prefix=f"{settings.API_PREFIX}",
    tags=["认证"]
)

app.include_router(
    session.router,
    prefix=f"{settings.API_PREFIX}",
    tags=["会话管理"]
)


# ============================
# 健康检查
# ============================

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# ============================
# 启动事件
# ============================

@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    logger.info(f"Enterprise Multi-Agent System v{settings.APP_VERSION} starting...")
    logger.info(f"Milvus: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
    logger.info(f"PostgreSQL: {settings.DATABASE_URL}")
    logger.info(f"GLM Model: {settings.GLM_CHAT_MODEL}")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    logger.info("Application shutdown")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
