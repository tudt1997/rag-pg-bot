import json
from typing import List, Dict, Generator

from rag_system.components.search.elastic_search import ElasticSearch
from rag_system.services.embedding import EmbeddingClient
from rag_system.services.reranker import RankerClient
from rag_system.services.llm import LLMClient
from rag_system.services.tool_call import ToolService

class LLMResponseGenerator:
    def __init__(self, enable_search: bool = False):
        """
        Orchestrates the RAG pipeline and tool calling.

        :param enable_search: allow or disable DuckDuckGoSearch tool
        """
        self.searcher = ElasticSearch()
        self.embed_client = EmbeddingClient()
        self.reranker = RankerClient()
        self.llm = LLMClient()
        self.tool_service = ToolService(enable_search=enable_search)

    def generate_response(
        self,
        index_name: str,
        user_query: str,
        chat_history: List[Dict[str, str]],
        enable_thinking: bool = False
    ) -> Generator[str, None, None]:
        """
        1. Embed + retrieve + rerank documents
        2. Build chat messages
        3. Call Ollama chat with registered tool schemas
        4. Stream back assistant reply, handling any tool_call
        5. Append reply to history
        """

        # 1) Build RAG context 
        query_vec = self.embed_client.generate_embeddings(user_query)
        hits = self.searcher.search(index_name, query_vec)
        filtered = [h for h in hits if h["score"] > 1.3]
        texts = [h["text"] for h in filtered]
        scores = self.reranker.rerank(user_query, texts)
        docs = sorted([
            {"text": h["text"], "source": h["source"], "page_number": h["page_number"], "score": s}
            for h, s in zip(filtered, scores)
        ], key=lambda d: d["score"], reverse=True)[:5]
        context = "\n".join(
            f"- {d['text']} (Nguồn: {d['source']}, trang {d['page_number']})"
            for d in docs
        ) or "Không tìm thấy thông tin liên quan."

        # 2) Construct messages (Tiếng Việt for prompts)
        system_prompt = (
            "Bạn là chuyên gia trích xuất thông tin từ văn bản. "
            "Bạn chỉ được trả lời các thông tin nếu nó xuất hiện trong ngữ cảnh được trích xuất"
            "Hãy trả lời thân thiện."
            "Trả lời dưới dạng: [Câu trả lời] (Nguồn [Tên tài liệu], trang X) khi trích dẫn"
            "Nếu không tìm được thông tin liên quan, hãy trả lời: Không tìm được thông tin liên quan"
        )

        if enable_thinking:
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": system_prompt},
                *chat_history,
                {"role": "user", "content": f"Ngữ cảnh:\n{context}\n\nCâu hỏi:\n{user_query}"}
            ]
        else:
            messages: List[Dict[str, str]] = [
                {"role": "system", "content": system_prompt},
                *chat_history,
                {"role": "user", "content": f"Ngữ cảnh:\n{context}\n\nCâu hỏi:\n{user_query}" + "/no_think"}
            ]

        # 3) Call LLM
        resp_iter = self.llm.chat(
            messages=messages,
            stream=True,
            enable_thinking=enable_thinking
        )

        # 4) Stream response 
        full_reply = ""
        for chunk in resp_iter:
            msg = chunk.message

            if msg.content:
                full_reply += msg.content
                yield msg.content

        # 5) Update history
        chat_history.append({"role": "user", "content": user_query})
        chat_history.append({"role": "assistant", "content": full_reply})