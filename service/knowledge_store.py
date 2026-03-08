# service/knowledge_store.py
"""
知识库检索模块 - 阿里云百炼 RAG 官方 SDK
参数根据 SDK 探测结果确认：
  RetrieveRequest(index_id, query, rerank_top_n, dense_similarity_top_k, ...)
  响应结构：response.body.data.nodes → [RetrieveResponseBodyDataNodes(text, score, metadata)]
"""
import os
from typing import List, Optional, Union

import requests
from langchain_core.documents import Document

try:
    from alibabacloud_bailian20231229 import models as bailian_models
    from alibabacloud_bailian20231229.client import Client as BailianClient
    from alibabacloud_tea_openapi import models as open_api_models
    from alibabacloud_tea_util import models as util_models
    _HAS_OFFICIAL_SDK = True
except ImportError:
    _HAS_OFFICIAL_SDK = False


class KnowledgeStore:

    def __init__(
        self,
        db=None,
        api_key: Optional[str] = None,
        knowledge_base_id: Optional[str] = None,
        workspace_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        **kwargs,
    ):
        self.api_key           = api_key           or os.getenv("DASHSCOPE_API_KEY", "")
        self.knowledge_base_id = knowledge_base_id or os.getenv("BAILOU_KNOWLEDGE_BASE_ID", "")
        self.workspace_id      = workspace_id      or os.getenv("BAILOU_WORKSPACE_ID", "")
        self.access_key_id     = access_key_id     or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
        self.access_key_secret = access_key_secret or os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")

        if not self.knowledge_base_id:
            raise ValueError("请在 .env 中设置 BAILOU_KNOWLEDGE_BASE_ID")

        if _HAS_OFFICIAL_SDK and self.access_key_id and self.access_key_secret and self.workspace_id:
            self._mode = "official_sdk"
            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
                endpoint="bailian.cn-beijing.aliyuncs.com",
            )
            self._sdk_client = BailianClient(config)
            print(f"[KnowledgeStore] ✅ 官方 SDK 模式，index_id={self.knowledge_base_id}")
        elif self.api_key:
            self._mode = "http_api"
            print(f"[KnowledgeStore] ✅ HTTP API 模式")
        else:
            raise ValueError("请配置 DASHSCOPE_API_KEY 或 ALIBABA_CLOUD 密钥三件套")

    # ── 核心检索 ──────────────────────────────────────────────────────────────

    def retrieve(self, query: str, job_position_id: int = 0, top_k: int = 3) -> List[str]:
        try:
            if self._mode == "official_sdk":
                raw_nodes = self._retrieve_sdk(query, top_k)
            else:
                raw_nodes = self._retrieve_http(query, top_k)

            if not raw_nodes:
                return ["📭 知识库中未找到相关内容。"]

            results = []
            for node in raw_nodes:
                text  = node.get("text", "").strip()
                score = node.get("score", 0.0)
                title = node.get("title", "")
                if not text:
                    continue
                parts = []
                if title:
                    parts.append(f"【{title}】")
                parts.append(text)
                if score:
                    parts.append(f"(相关度: {score:.2f})")
                results.append(" ".join(parts))

            return results or ["📭 知识库中未找到相关内容。"]

        except Exception as e:
            import traceback
            print(f"[KnowledgeStore] ❌ 检索异常:\n{traceback.format_exc()}")
            return [f"⚠️ 知识库检索异常：{type(e).__name__}: {e}"]

    def _retrieve_sdk(self, query: str, top_k: int) -> List[dict]:
        """
        官方 SDK 检索。
        经探测确认的正确参数（alibabacloud-bailian20231229）：
          - index_id: 知识库 ID（即 BAILOU_KNOWLEDGE_BASE_ID）
          - query: 查询文本
          - rerank_top_n: 返回结果数量（不是 top_k）
          - dense_similarity_top_k: 向量检索候选数（建议设为 rerank_top_n 的 3~5 倍）
        响应结构：
          response.body.data.nodes → List[RetrieveResponseBodyDataNodes]
          每个 node 有属性：text, score, metadata
        """
        request = bailian_models.RetrieveRequest(
            index_id=self.knowledge_base_id,
            query=query,
            rerank_top_n=top_k,
            dense_similarity_top_k=top_k * 4,  # 候选池，建议为结果数的 4 倍
            enable_reranking=True,
        )
        runtime  = util_models.RuntimeOptions()
        response = self._sdk_client.retrieve_with_options(
            self.workspace_id, request, {}, runtime
        )

        # 响应结构：response.body.data.nodes
        body  = getattr(response, "body", None)
        data  = getattr(body, "data", None)
        nodes = getattr(data, "nodes", None) or []

        print(f"[KnowledgeStore] 检索到 {len(nodes)} 个节点")

        result = []
        for node in nodes:
            # RetrieveResponseBodyDataNodes 有 text, score, metadata 三个属性
            text     = getattr(node, "text", "") or ""
            score    = getattr(node, "score", 0) or 0
            metadata = getattr(node, "metadata", {}) or {}

            # metadata 可能是 dict 或对象
            if isinstance(metadata, dict):
                title = metadata.get("file_name") or metadata.get("title") or ""
            else:
                title = getattr(metadata, "file_name", "") or getattr(metadata, "title", "") or ""

            result.append({
                "text":  str(text).strip(),
                "score": float(score),
                "title": str(title),
            })

        return result

    def _retrieve_http(self, query: str, top_k: int) -> List[dict]:
        resp = requests.post(
            "https://dashscope.aliyuncs.com/api/v1/indices/query",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type":  "application/json",
            },
            json={"pipeline_id": self.knowledge_base_id, "query": query, "top_k": top_k},
            timeout=15,
        )
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:300]}")

        raw   = resp.json()
        nodes = raw.get("output", {}).get("nodes", [])
        result = []
        for item in nodes:
            node  = item.get("node", item)
            score = item.get("score", 0)
            text  = node.get("text", "") or node.get("content", "")
            meta  = node.get("metadata", {})
            title = (meta.get("file_name") or meta.get("title") or "") if isinstance(meta, dict) else ""
            result.append({"text": text.strip(), "score": float(score), "title": title})
        return result

    def retrieve_as_context(self, query: str, job_position_id: int = 0, top_k: int = 3) -> str:
        results = self.retrieve(query, job_position_id=job_position_id, top_k=top_k)
        if not results or results[0].startswith("📭") or results[0].startswith("⚠️"):
            return ""
        lines = ["【参考知识库】"]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r}")
        return "\n".join(lines)

    # ── 文档管理存根 ──────────────────────────────────────────────────────────

    def add_file(self, file_path: str, job_position_id: int = 0) -> int:
        print(f"ℹ️  [KnowledgeStore] 请在百炼控制台上传文档，跳过: {file_path}")
        return 0

    def add_qa_pairs(self, qa_list: list, job_position_id: int = 0) -> int:
        print(f"ℹ️  [KnowledgeStore] 请在百炼控制台导入 Q&A（{len(qa_list)} 条），已跳过")
        return 0

    def add_documents(self, documents, job_position_id: int = 0) -> int:
        print("ℹ️  [KnowledgeStore] 请在百炼控制台上传文档，已跳过")
        return 0

    def add_text(self, text: str, job_position_id: int = 0, source: str = "") -> int:
        print(f"ℹ️  [KnowledgeStore] 请在百炼控制台上传文档，已跳过: {source}")
        return 0

    def delete_collection(self):
        print("ℹ️  请在百炼控制台管理知识库：https://bailian.console.aliyun.com/")

    def get_stats(self) -> dict:
        return {"type": "aliyun_bailian_rag", "mode": self._mode,
                "knowledge_base_id": self.knowledge_base_id}