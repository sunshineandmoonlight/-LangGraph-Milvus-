"""
Milvus 向量数据库服务模块

本模块封装了 Milvus 向量数据库的所有操作，包括：
1. Collection (集合) 的创建和管理
2. 向量数据的插入
3. 向量相似性搜索

Milvus 核心概念说明：
- Collection (集合): 类似于关系数据库的表，用于存储向量数据
- Field (字段): Collection 的列，定义数据的结构
- Schema (模式): Collection 的结构定义，包含字段和类型
- Index (索引): 加速向量搜索的数据结构
- Vector Embedding (向量嵌入): 将文本、图像等转换为数值向量
- Similarity Search (相似性搜索): 找到与查询向量最相似的数据
"""
import time
from typing import List, Dict, Any, Optional
from pymilvus import (
    connections,
    Collection,
    CollectionSchema,
    FieldSchema,
    DataType,
    utility,
)
from loguru import logger
from app.config import settings


class MilvusService:
    """Milvus 服务类

    提供完整的 Milvus 向量数据库操作接口
    包含连接管理、Collection 创建、数据插入和向量搜索功能
    """

    def __init__(self):
        """初始化 Milvus 服务

        建立与 Milvus 服务器的连接，并初始化 Collection
        """
        self.host = settings.MILVUS_HOST
        self.port = settings.MILVUS_PORT
        self.collection_name = settings.MILVUS_COLLECTION_NAME
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index_type = settings.INDEX_TYPE
        self.metric_type = settings.METRIC_TYPE

        # Collection 对象 (初始化时为 None，在 connect() 后创建)
        self.collection: Optional[Collection] = None

        # 建立连接并初始化
        self._connect_with_retry()
        self._init_collection()

    def _connect_with_retry(self) -> None:
        """使用重试机制连接到 Milvus 服务器

        由于 Milvus 启动较慢，需要实现重试机制
        避免因 Milvus 未就绪而导致连接失败
        """
        max_retries = settings.MILVUS_MAX_RETRIES
        retry_interval = settings.MILVUS_RETRY_INTERVAL

        for attempt in range(max_retries):
            try:
                # 连接到 Milvus 服务器
                connections.connect(
                    alias="default",  # 连接别名，默认为 "default"
                    host=self.host,
                    port=self.port,
                )

                # 测试连接是否成功
                connections.list_connections()

                logger.info(
                    f"成功连接到 Milvus 服务器: {self.host}:{self.port}"
                )
                return

            except Exception as e:
                logger.warning(
                    f"连接 Milvus 失败 (尝试 {attempt + 1}/{max_retries}): {e}"
                )

                if attempt < max_retries - 1:
                    logger.info(f"等待 {retry_interval} 秒后重试...")
                    time.sleep(retry_interval)
                else:
                    logger.error("达到最大重试次数，连接失败")
                    raise

    def _init_collection(self) -> None:
        """初始化 Milvus Collection

        检查 Collection 是否存在，如果不存在则创建
        如果存在则加载到内存中以便查询

        Collection 概念说明：
        - Collection 是 Milvus 中存储和检索数据的基本单元
        - 类似于关系数据库中的 "表"
        - 每个 Collection 有一个固定的 Schema (结构定义)
        - 包含多个 Field (字段)，如 ID、向量、文本、元数据等
        """
        try:
            # 检查 Collection 是否已存在
            if utility.has_collection(self.collection_name):
                logger.info(f"Collection '{self.collection_name}' 已存在，加载中...")

                # 加载已存在的 Collection
                self.collection = Collection(self.collection_name)
                logger.info(f"成功加载 Collection: {self.collection_name}")

            else:
                logger.info(f"Collection '{self.collection_name}' 不存在，开始创建...")

                # 定义 Collection 的 Schema (结构)
                self._create_collection()

            # 加载 Collection 到内存
            # 注意：必须加载 Collection 后才能进行搜索操作
            self.collection.load()
            logger.info(f"Collection '{self.collection_name}' 已加载到内存")

        except Exception as e:
            logger.error(f"初始化 Collection 失败: {e}")
            raise

    def _create_collection(self) -> None:
        """创建 Milvus Collection

        定义 Collection 的 Schema (结构)，包括：
        1. id_field: 唯一标识符 (主键)
        2. vector_field: 向量嵌入 (用于相似性搜索)
        3. text_field: 原始文本内容
        4. metadata_field: 元数据 (JSON 格式)

        Schema 概念说明：
        - Schema 定义了 Collection 的结构，类似于数据库表结构
        - 每个字段有名称、数据类型和属性
        - 向量字段必须指定维度 (dimension)
        """
        try:
            # ============================
            # 定义字段 (Fields)
            # ============================

            # 1. ID 字段 - 主键，自增
            # DataType.INT64: 64 位整数
            # is_primary=True: 设为主键
            # auto_id=True: 自动生成 ID
            id_field = FieldSchema(
                name="id",
                dtype=DataType.INT64,
                is_primary=True,
                auto_id=True,
                description="文档唯一标识符 (主键，自动生成)"
            )

            # 2. 向量字段 - 存储向量嵌入
            # DataType.FLOAT_VECTOR: 浮点数向量
            # dim: 向量维度 (OpenAI ada-002 模型为 1536 维)
            vector_field = FieldSchema(
                name="vector",
                dtype=DataType.FLOAT_VECTOR,
                dim=self.dimension,
                description="向量嵌入 (用于相似性搜索)"
            )

            # 3. 文本字段 - 存储原始文本
            # DataType.VARCHAR: 可变长度字符串
            # max_length: 最大长度
            text_field = FieldSchema(
                name="text",
                dtype=DataType.VARCHAR,
                max_length=65535,
                description="文档的原始文本内容"
            )

            # 4. 元数据字段 - 存储额外的元信息
            # DataType.JSON: JSON 格式数据，可以存储键值对
            metadata_field = FieldSchema(
                name="metadata",
                dtype=DataType.JSON,
                description="文档元数据 (如来源、时间戳、标签等)"
            )

            # ============================
            # 创建 Schema
            # ============================
            # 将所有字段组合成 Schema
            # Schema 是 Collection 的蓝图，定义了数据的结构
            schema = CollectionSchema(
                fields=[id_field, vector_field, text_field, metadata_field],
                description="企业知识库向量集合",
                enable_dynamic_field=False  # 禁用动态字段
            )

            # ============================
            # 创建 Collection
            # ============================
            self.collection = Collection(
                name=self.collection_name,
                schema=schema
            )

            logger.info(f"成功创建 Collection: {self.collection_name}")

            # ============================
            # 创建索引 (Index)
            # ============================
            self._create_index()

        except Exception as e:
            logger.error(f"创建 Collection 失败: {e}")
            raise

    def _create_index(self) -> None:
        """为向量字段创建索引

        Index 概念说明：
        - Index 是一种加速向量搜索的数据结构
        - 类似于书籍的索引，可以快速定位到相关内容
        - HNSW (Hierarchical Navigable Small World) 是一种高效的近似最近邻索引
        - 索引参数：
          - M: 每个节点的最大连接数 (影响召回率和速度)
          - efConstruction: 构建索引时的搜索深度 (影响索引质量)

        Metric Type (度量类型) 说明：
        - IP (Inner Product): 内积，值越大越相似
        - L2 (Euclidean Distance): 欧几里得距离，值越小越相似
        - COSINE (Cosine Similarity): 余弦相似度，值越大越相似
        """
        try:
            # 定义索引参数
            # HNSW 是一种高效的图索引结构
            index_params = {
                "index_type": self.index_type,  # HNSW
                "metric_type": self.metric_type,  # IP (内积)
                "params": {
                    "M": 16,  # 每个节点的最大连接数 (范围: 2-100)
                    "efConstruction": 256  # 构建时的搜索深度 (范围: 8-512)
                }
            }

            # 在 vector 字段上创建索引
            self.collection.create_index(
                field_name="vector",
                index_params=index_params
            )

            logger.info(
                f"成功在字段 'vector' 上创建索引 "
                f"(类型: {self.index_type}, 度量: {self.metric_type})"
            )

        except Exception as e:
            logger.error(f"创建索引失败: {e}")
            raise

    def insert(
        self,
        texts: List[str],
        vectors: List[List[float]],
        metadata: List[Dict[str, Any]]
    ) -> int:
        """插入数据到 Collection

        Args:
            texts: 文本内容列表
            vectors: 向量嵌入列表
            metadata: 元数据列表

        Returns:
            int: 插入的记录数量

        注意事项：
        - texts, vectors, metadata 的长度必须一致
        - vectors 的每个元素维度必须与 Collection 定义一致
        - metadata 必须是有效的 JSON 可序列化对象
        """
        try:
            # 数据验证
            if not (len(texts) == len(vectors) == len(metadata)):
                raise ValueError(
                    "texts, vectors, metadata 的长度必须一致"
                )

            # 构造插入数据
            # Milvus 使用字典格式插入数据
            data = [
                vectors,  # vector 字段
                texts,    # text 字段
                metadata  # metadata 字段
            ]

            # 插入数据
            insert_result = self.collection.insert(data)

            # 刷新数据，使其立即可被搜索
            # 注意：flush 操作会消耗资源，生产环境建议批量刷新
            self.collection.flush()

            logger.info(
                f"成功插入 {insert_result.insert_count} 条记录 "
                f"到 Collection '{self.collection_name}'"
            )

            return insert_result.insert_count

        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            raise

    def search(
        self,
        query_vector: List[float],
        top_k: Optional[int] = None,
        expr: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """向量相似性搜索

        Args:
            query_vector: 查询向量 (通常是查询文本的 Embedding)
            top_k: 返回的最相似结果数量 (默认使用配置值)
            expr: 过滤表达式 (可选，用于过滤搜索结果)

        Returns:
            List[Dict[str, Any]]: 搜索结果列表，每个结果包含：
                - id: 文档 ID
                - text: 文本内容
                - metadata: 元数据
                - score: 相似度得分

        搜索概念说明：
        - 向量搜索基于"相似性"而非"精确匹配"
        - 返回与查询向量最相似的 Top-K 个结果
        - 相似度得分取决于度量类型 (IP/L2/COSINE)

        过滤表达式示例：
        - expr='metadata["category"] == "技术文档"'
        - expr='metadata["timestamp"] > 1704067200'
        """
        try:
            top_k = top_k or settings.SEARCH_TOP_K

            # 定义搜索参数
            # 这些参数会影响搜索的速度和准确率
            search_params = {
                "metric_type": self.metric_type,
                "params": {
                    "ef": top_k * 2  # 搜索深度，越大越准确但越慢
                }
            }

            # 执行向量搜索
            results = self.collection.search(
                data=[query_vector],  # 查询向量列表 (可以是多个)
                anns_field="vector",  # 要搜索的向量字段
                param=search_params,  # 搜索参数
                limit=top_k,  # 返回结果数量
                expr=expr,  # 过滤表达式 (可选)
                output_fields=["text", "metadata"]  # 返回的字段
            )

            # 解析搜索结果
            formatted_results = []
            for hit in results[0]:
                formatted_results.append({
                    "id": hit.id,
                    "text": hit.entity.get("text"),
                    "metadata": hit.entity.get("metadata"),
                    "score": hit.score
                })

            logger.info(
                f"搜索完成，返回 {len(formatted_results)} 条结果 "
                f"(Top-K: {top_k})"
            )

            return formatted_results

        except Exception as e:
            logger.error(f"向量搜索失败: {e}")
            raise

    def delete(self, expr: str) -> int:
        """删除符合条件的数据

        Args:
            expr: 删除表达式 (例如: 'id in [1,2,3]' 或 'metadata["category"] == "test"')

        Returns:
            int: 删除的记录数量
        """
        try:
            # 执行删除操作
            self.collection.delete(expr)
            logger.info(f"执行删除操作: {expr}")
            return 0  # Milvus 不返回删除数量

        except Exception as e:
            logger.error(f"删除数据失败: {e}")
            raise

    def get_collection_info(self) -> Dict[str, Any]:
        """获取 Collection 的信息

        Returns:
            Dict[str, Any]: Collection 信息，包括：
                - name: Collection 名称
                - description: 描述
                - num_entities: 实体数量
        """
        try:
            info = {
                "name": self.collection.name,
                "description": self.collection.description,
                "num_entities": self.collection.num_entities
            }
            return info

        except Exception as e:
            logger.error(f"获取 Collection 信息失败: {e}")
            raise

    def query_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        """查询所有文档的元数据

        Args:
            limit: 返回的最大文档数量

        Returns:
            List[Dict[str, Any]]: 文档列表，每个文档包含：
                - id: 文档ID
                - metadata: 元数据（包含filename, file_size等）
                - text: 文本内容（前200字符）
        """
        try:
            # 使用 Milvus 的 query 功能
            # expr="" 表示查询所有数据
            results = self.collection.query(
                expr="",  # 空表达式表示查询所有
                output_fields=["id", "metadata", "text"],
                limit=limit
            )

            # 格式化结果
            documents = []
            for result in results:
                # 只获取文本的前200字符作为预览
                text_preview = result.get("text", "")[:200]

                documents.append({
                    "id": result.get("id"),
                    "metadata": result.get("metadata", {}),
                    "text_preview": text_preview
                })

            logger.info(f"查询到 {len(documents)} 个文档")
            return documents

        except Exception as e:
            logger.error(f"查询文档失败: {e}")
            raise


# ============================
# 全局 Milvus 服务实例
# ============================
# 创建单例实例，供整个应用使用
milvus_service = MilvusService()
