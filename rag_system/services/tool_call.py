import json
from typing import Dict, List

# import any external tools here
from langchain_community.tools import DuckDuckGoSearchRun

class ToolService:
    """
    Centralizes all tool execution logic.
    You can enable or disable web search via `enable_search`.
    """
    # Define all tool schemas here
    CALCULATOR_SCHEMA = {
        "name": "calculator",
        "description": "Thực hiện phép tính đơn giản từ biểu thức string",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Ví dụ: '2 + 2 * (3 - 1)'"
                }
            },
            "required": ["expression"]
        }
    }
    TIME_SCHEMA = {
        "name": "get_current_time",
        "description": "Trả về thời gian hiện tại hệ thống (ISO 8601)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
    DUCK_SCHEMA = {
        "name": "duckduckgo_search",
        "description": "Lấy thông tin cập nhật từ web qua DuckDuckGo.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Nội dung cần tìm kiếm"
                }
            },
            "required": ["query"]
        }
    }

    def __init__(self, enable_search: bool = False):
        """
        :param enable_search: if False, any attempt to call DUCK_SCHEMA will be rejected
        """
        self.enable_search = enable_search

    def get_tool_schemas(self) -> List[Dict]:
        """
        Return the list of JSON Schemas for all enabled tools.
        """
        schemas = [
            self.CALCULATOR_SCHEMA,
            self.TIME_SCHEMA,
        ]
        if self.enable_search:
            schemas.append(self.DUCK_SCHEMA)
        return schemas

    def execute(self, name: str, args: Dict) -> Dict:
        """
        Dispatch actual tool execution based on tool name.
        Raises an error if web search is disabled.
        """
        if name == "calculator":
            # simple eval, but be careful in production!
            try:
                result = eval(args["expression"], {"__builtins__": {}})
                return {"result": result}
            except Exception as e:
                return {"error": str(e)}

        if name == "get_current_time":
            from datetime import datetime
            return {"result": datetime.utcnow().isoformat() + "Z"}

        if name == "duckduckgo_search":
            if not self.enable_search:
                return {"error": "Web search is disabled."}
            tool = DuckDuckGoSearchRun()
            return {"result": tool.run(args["query"])}

        return {"error": f"Unknown tool: {name}"}