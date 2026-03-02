"""
知识库相关 API 路由

提供文档上传、搜索和管理功能
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from loguru import logger

from app.services.milvus_service import milvus_service
from app.services.embedding_service import batch_get_embeddings

router = APIRouter()


# ============================
# 请求/响应模型
# ============================

class KnowledgeSearchRequest(BaseModel):
    """知识库搜索请求"""
    query: str = Field(..., description="搜索查询", min_length=1)
    top_k: int = Field(5, description="返回结果数量", ge=1, le=20)


class KnowledgeSearchResponse(BaseModel):
    """知识库搜索响应"""
    query: str
    results: List[Dict[str, Any]]
    total: int


class KnowledgeStatsResponse(BaseModel):
    """知识库统计响应"""
    collection_name: str
    num_entities: int  # 文档片段总数
    num_files: int  # 唯一文件数量
    description: str


# ============================
# API 端点
# ============================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    metadata: Optional[str] = Form(None)
):
    """
    上传文档到知识库

    支持的文件格式: .txt, .md, .json, .doc, .docx, .pdf
    上传后会将文档内容转换为向量并存储到 Milvus

    Args:
        file: 上传的文件
        metadata: 元数据 (JSON 字符串)

    Returns:
        Dict: 上传结果
    """
    try:
        # 根据文件类型读取内容
        filename = file.filename.lower()

        if filename.endswith('.pdf'):
            # 处理 PDF 文档
            from pypdf import PdfReader
            import io

            content = await file.read()
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)

            # 提取所有页面的文本
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text())

            text = '\n'.join(text_parts)
            file_size = len(content)

        elif filename.endswith('.docx'):
            # 处理 Word 文档 (.docx)
            from docx import Document
            import io

            content = await file.read()
            doc = Document(io.BytesIO(content))

            # 提取所有段落文本
            text = '\n'.join([para.text for para in doc.paragraphs])
            file_size = len(content)

        elif filename.endswith('.doc'):
            # 处理旧版 Word 文档 (.doc)
            # 使用 docx2txt 处理旧格式
            try:
                import docx2txt
                import tempfile

                # 保存到临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix='.doc') as tmp:
                    tmp.write(await file.read())
                    tmp_path = tmp.name
                    file_size = tmp.tell()

                # 提取文本
                text = docx2txt.process(tmp_path)

                # 删除临时文件
                import os
                os.unlink(tmp_path)

                if not text or not text.strip():
                    raise HTTPException(
                        status_code=400,
                        detail=".doc 文件解析失败。请将文件另存为 .docx 格式后重试。"
                    )

            except ImportError:
                raise HTTPException(
                    status_code=400,
                    detail=".doc 格式需要额外依赖。请将文件另存为 .docx 格式后重试。"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f".doc 文件处理失败: {str(e)}。建议将文件另存为 .docx 格式。"
                )

        elif filename.endswith(('.txt', '.md', '.json')):
            # 处理文本文件
            content = await file.read()
            text = content.decode("utf-8")
            file_size = len(content)

        else:
            raise HTTPException(
                status_code=400,
                detail="不支持的文件格式。请上传 .txt, .md, .json, .doc, .docx 或 .pdf 文件（注意：.doc 文件建议转换为 .docx 格式以获得更好的兼容性）"
            )

        if not text.strip():
            raise HTTPException(status_code=400, detail="文件内容为空")

        # 解析元数据
        import json
        meta_dict = {}
        if metadata:
            try:
                meta_dict = json.loads(metadata)
            except:
                meta_dict = {"raw_metadata": metadata}

        # 添加文件名到元数据
        meta_dict["filename"] = file.filename
        meta_dict["file_size"] = file_size

        # 生成向量嵌入
        logger.info(f"正在为文件 '{file.filename}' 生成向量...")
        embedding = batch_get_embeddings([text])[0]

        # 插入 Milvus
        count = milvus_service.insert(
            texts=[text],
            vectors=[embedding],
            metadata=[meta_dict]
        )

        logger.info(f"文件 '{file.filename}' 上传成功，插入 {count} 条记录")

        return {
            "status": "success",
            "filename": file.filename,
            "records_inserted": count,
            "message": "文档上传成功"
        }

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="文件编码错误，请使用 UTF-8 编码的文本文件")
    except Exception as e:
        logger.error(f"文档上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(request: KnowledgeSearchRequest):
    """
    搜索知识库

    执行向量相似性搜索，找到与查询最相关的文档

    Args:
        request: 搜索请求

    Returns:
        KnowledgeSearchResponse: 搜索结果

    示例:
        ```python
        response = await search_knowledge(
            KnowledgeSearchRequest(
                query="人工智能在医疗领域的应用",
                top_k=5
            )
        )
        ```
    """
    try:
        from app.services.embedding_service import get_embedding

        # 生成查询向量
        logger.info(f"正在搜索: {request.query}")
        query_vector = get_embedding(request.query)

        # 执行搜索
        results = milvus_service.search(
            query_vector=query_vector,
            top_k=request.top_k
        )

        logger.info(f"搜索完成，返回 {len(results)} 条结果")

        return KnowledgeSearchResponse(
            query=request.query,
            results=results,
            total=len(results)
        )

    except Exception as e:
        logger.error(f"知识库搜索失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=KnowledgeStatsResponse)
async def get_knowledge_stats():
    """
    获取知识库统计信息

    Returns:
        KnowledgeStatsResponse: 统计信息
    """
    try:
        # 获取所有文档
        documents = milvus_service.query_all(limit=10000)

        # 提取唯一的文件名
        unique_filenames = set()
        for doc in documents:
            filename = doc.get("metadata", {}).get("filename", "未知文件")
            unique_filenames.add(filename)

        info = milvus_service.get_collection_info()

        return KnowledgeStatsResponse(
            collection_name=info["name"],
            num_entities=info["num_entities"],  # 文档片段总数（实际向量数量）
            num_files=len(unique_filenames),  # 唯一文件数量
            description=f"共 {info['num_entities']} 个片段，{len(unique_filenames)} 个文件"
        )

    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{doc_id}")
async def delete_document(doc_id: int):
    """
    删除知识库文档（按文档ID）

    Args:
        doc_id: 文档 ID

    Returns:
        Dict: 删除结果
    """
    try:
        result = milvus_service.delete(expr=f"id == {doc_id}")

        return {
            "status": "success",
            "message": f"文档 {doc_id} 已删除",
            "deleted_count": result
        }

    except Exception as e:
        logger.error(f"删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/filename/{filename}")
async def delete_document_by_filename(filename: str):
    """
    按文件名删除知识库文档

    Args:
        filename: 文件名

    Returns:
        Dict: 删除结果
    """
    try:
        # Milvus 不支持直接按 JSON 字段删除，需要先查询再删除
        # 这里我们使用元数据字段的模糊匹配
        result = milvus_service.delete(expr=f'metadata["filename"] == "{filename}"')

        return {
            "status": "success",
            "message": f"文件 '{filename}' 相关的文档已删除",
            "deleted_count": result
        }

    except Exception as e:
        logger.error(f"按文件名删除文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents")
async def list_documents(limit: int = 100):
    """
    列出所有知识库文档

    Args:
        limit: 返回的最大文档数量

    Returns:
        Dict: 文档列表
    """
    try:
        # 使用新添加的 query_all 方法
        documents = milvus_service.query_all(limit=limit)

        # 提取所有唯一的文件名
        filenames = set()
        for doc in documents:
            filename = doc.get("metadata", {}).get("filename", "未知文件")
            filenames.add(filename)

        return {
            "status": "success",
            "documents": documents,
            "unique_files": list(filenames),
            "total_documents": len(documents),
            "total_files": len(filenames)
        }

    except Exception as e:
        logger.error(f"列出文档失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/batch-insert")
async def batch_insert_documents(
    texts: List[str],
    metadata: Optional[List[Dict[str, Any]]] = None
):
    """
    批量插入文档到知识库

    Args:
        texts: 文本列表
        metadata: 元数据列表 (可选)

    Returns:
        Dict: 插入结果
    """
    try:
        if metadata and len(texts) != len(metadata):
            raise HTTPException(
                status_code=400,
                detail="texts 和 metadata 的长度必须一致"
            )

        # 生成向量嵌入
        logger.info(f"正在为 {len(texts)} 个文档生成向量...")
        embeddings = batch_get_embeddings(texts)

        # 准备元数据
        if not metadata:
            metadata = [{"index": i} for i in range(len(texts))]

        # 批量插入
        count = milvus_service.insert(
            texts=texts,
            vectors=embeddings,
            metadata=metadata
        )

        logger.info(f"批量插入完成，插入 {count} 条记录")

        return {
            "status": "success",
            "records_inserted": count,
            "message": f"成功插入 {count} 条记录"
        }

    except Exception as e:
        logger.error(f"批量插入失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
