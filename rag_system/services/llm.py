import ollama
from typing import List, Dict, Optional

class LLMClient:
    def __init__(self, model_name: str = "qwen3:4b"):
        """
        A wrapper around Ollama’s chat API for an instruct-style model.
        """
        self.model_name = model_name

    def chat(
        self,
        messages: List[Dict[str, str]],
        stream: bool = False,
        options: Optional[Dict] = None,
        enable_thinking: bool = False
    ):
        """
        :param messages: list of {"role":..., "content":...}
        :param stream: whether to stream the response
        :param options: tool schemas / tool_choice, v.v.
        :param enable_thinking: if True -> thinking-mode with sampling (T=0.6,P=0.95,K=20,MinP=0)
        """
        # copy incoming options
        opts = options.copy() if options else {}

        if enable_thinking:
            opts.setdefault("temperature", 0.6)
            opts.setdefault("top_p", 0.95)
            opts.setdefault("top_k", 20)
            opts.setdefault("min_p", 0.0)
        else:
            opts.setdefault("temperature", 0.7)
            opts.setdefault("top_p", 0.8)
            opts.setdefault("top_k", 20)
            opts.setdefault("min_p", 0.0)


        kwargs = {
            "model": self.model_name,
            "messages": messages,
            "stream": stream,
            "options": opts,
        }
        return ollama.chat(**kwargs)