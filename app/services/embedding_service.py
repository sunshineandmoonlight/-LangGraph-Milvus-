"""
Embedding 服务模块

负责将文本转换为向量嵌入
支持智谱 AI (GLM) 和 SiliconFlow
"""
from zhipuai import ZhipuAI
from openai import OpenAI
from app.config import settings
from typing import List
import time

# 初始化智谱 AI 客户端（备用）
glm_client = ZhipuAI(api_key=settings.GLM_API_KEY)

# 初始化 SiliconFlow 客户端
siliconflow_client = OpenAI(
    api_key=settings.SILICONFLOW_API_KEY,
    base_url=settings.SILICONFLOW_API_BASE
)


def get_embedding(text: str) -> List[float]:
    """获取文本的向量嵌入

    Args:
        text: 输入文本

    Returns:
        List[float]: 向量嵌入

    注意事项:
        - 文本过长时会自动截断
        - 网络错误时会自动重试 (最多 3 次)
    """
    max_retries = 3

    for attempt in range(max_retries):
        try:
            if settings.USE_SILICONFLOW:
                # 使用 SiliconFlow Embedding
                response = siliconflow_client.embeddings.create(
                    model=settings.SILICONFLOW_EMBEDDING_MODEL,
                    input=text
                )
                return response.data[0].embedding
            else:
                # 使用智谱 AI Embedding
                response = glm_client.embeddings.create(
                    model=settings.GLM_EMBEDDING_MODEL,
                    input=text
                )
                return response.data[0].embedding

        except Exception as e:
            if attempt < max_retries - 1:
                print(f"Embedding 请求失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                time.sleep(2 ** attempt)  # 指数退避
            else:
                raise


def batch_get_embeddings(texts: List[str]) -> List[List[float]]:
    """批量获取文本的向量嵌入

    Args:
        texts: 输入文本列表

    Returns:
        List[List[float]]: 向量嵌入列表

    注意事项:
        - 支持批量 Embedding
        - 批量处理比单个处理更高效
    """
    # 为了稳定性，我们分批处理
    batch_size = 100
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        try:
            if settings.USE_SILICONFLOW:
                # 使用 SiliconFlow Embedding
                response = siliconflow_client.embeddings.create(
                    model=settings.SILICONFLOW_EMBEDDING_MODEL,
                    input=batch
                )
            else:
                # 使用智谱 AI Embedding
                response = glm_client.embeddings.create(
                    model=settings.GLM_EMBEDDING_MODEL,
                    input=batch
                )

            # 提取向量嵌入
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        except Exception as e:
            print(f"批量 Embedding 失败: {e}")
            # 如果批量失败，回退到单个处理
            for text in batch:
                embedding = get_embedding(text)
                all_embeddings.append(embedding)

    return all_embeddings
