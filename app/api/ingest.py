"""
RAG 数据入库接口

提供文档上传、切片、向量化和存储功能
"""
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger
import asyncio

from app.services.milvus_service import milvus_service
from app.services.embedding_service import batch_get_embeddings


class IngestRequest(BaseModel):
    """入库请求参数"""
    file: str = Field(..., description="文件名")


class KnowledgeStatsResponse(BaseModel):
    """知识库统计响应"""
    collection_name: str
    num_entities: int
    description: str


router = APIRouter(prefix="/api/v1/knowledge", tags=["Knowledge"])

# ============================
# API 端点
# ============================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(..., description="上传的文本文件 (.txt)"),
    metadata: Optional[str] = Form(None)
):
    """
    上传文档到知识库

    功能:
    1. 接收上传的 .txt 文件
    2. 读取文件内容
    3. 使用 RecursiveCharacterTextSplitter 进行文本切片
    4. 调用 MilvusService 插入数据和向量
    """
    try:
        # 读取文件内容
        content = await file.read()

        # 验证文件类型
        if not file.filename.endswith('.txt'):
            return JSONResponse(
                status="error",
                message="目前只支持 .txt 文件"
            )

        text = content.decode('utf-8')

        # 解析元数据
        import json
        metadata_dict = {"filename": file.filename}
        if metadata:
            try:
                metadata_dict.update(json.loads(metadata))
            except:
                metadata_dict["raw_metadata"] = metadata

        logger.info(f"开始处理文档: {file.filename} ({len(text)} 字符)")

        # 使用 RecursiveCharacterTextSplitter 进行文本切片
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,  # 每个切片 500 字符
            chunk_overlap=50,  # 切片间重叠 50 字符
            length_function=len,
            separators=["\n\n", "\n", "。", "，", "！", "？", "。", "!", "?", "\n\n\n"]
        )

        logger.info("开始切片文档...")
        chunks = text_splitter.split_text(text)
        logger.info(f"文档已切片为 {len(chunks)} 个切片")

        # 生成所有切片的向量嵌入
        logger.info("开始生成向量嵌入...")
        texts = [chunk.page_content for chunk in chunks]
        embeddings = batch_get_embeddings(texts)

        # 准备每个切片的元数据
        metadata_list = []
        for i, chunk in enumerate(chunks):
            chunk_metadata = {
                **metadata_dict,
                "chunk_id": i,
                "chunk_size": len(chunk.page_content),
                "start_index": chunk.metadata.get('start_index', 0)
            }
            metadata_list.append(chunk_metadata)

        # 插入 Milvus
        logger.info("开始插入向量数据...")
        count = milvus_service.insert(
            texts=texts,
            vectors=embeddings,
            metadata=metadata_list
        )

        logger.info(f"文档处理完成！插入 {count} 条记录")

        return JSONResponse(
            status="success",
            message="文档上传成功",
            data={
                "filename": file.filename,
                "chunks_processed": len(chunks),
                "records_inserted": count,
                "chunk_size": 500,
                "chunk_overlap": 50
            }
        )

    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        return JSONResponse(
            status="error",
            message=f"处理失败: {str(e)}"
        )


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats():
    """
    获取知识库统计信息

    Returns:
        KnowledgeStatsResponse: 结计信息
    """
    try:
        info = milvus_service.get_collection_info()

        return KnowledgeStatsResponse(
            collection_name=info["name"],
            num_entities=info["num_entities"],
            description=info["description"]
        )

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise


@router.post("/batch-insert")
async def batch_insert_documents(
    texts: List[str],
    metadata: Optional[List[Dict[str, Any]] = None
):
    """
    批量插入文档到知识库

    Args:
        texts: 文本列表
        metadata: 元数据列表 (可选)

    Returns:
        JSONResponse: 插入结果
    """
    try:
        # 验证输入
        if metadata and len(texts) != len(metadata):
            raise ValueError("texts 和 metadata 的长度必须一致")

        # 准备元数据
        if not metadata:
            metadata = [{"index": i} for i in range(len(texts))]

        # 生成向量嵌入
        logger.info(f"开始处理 {len(texts)} 个文档...")
        embeddings = batch_get_embeddings(texts)

        # 插入 Milvus
        logger.info("开始插入向量数据...")
        count = milvus_service.insert(
            texts=texts,
            vectors=embeddings,
            metadata=metadata
        )

        logger.info(f"批量插入完成，插入 {count} 条记录")

        return JSONResponse(
            status="success",
            message="批量插入成功",
            data={
                "records_inserted": count
            }
        )

    except Exception as e:
        logger.error(f"批量插入失败: {e}")
        return JSONResponse(
            status="error",
            message=f"处理失败: {str(e)}"
        )


@router.post("/search")
async def search_knowledge(query: str, top_k: int = 5):
    """搜索知识库"""
    try:
        from app.services.embedding_service import get_embedding

        # 生成查询向量
        query_vector = get_embedding(query)

        # 执行搜索
        results = milvus_service.search(
            query_vector=query_vector,
            top_k=top_k
        )

        return JSONResponse({
            "query": query,
            "results": results,
            "total": len(results)
        })

    except Exception as e:
        logger.error(f"知识库搜索失败: {e}")
        raise
