import json
import ollama
from langchain_community.tools import DuckDuckGoSearchResults

# 1) DuckDuckGo qua langchain community
search_tool = DuckDuckGoSearchResults()

def duckduckgo_search(query: str) -> dict:
    """
    Thực hiện tìm kiếm DuckDuckGo qua Langchain community.
    """
    results = search_tool.invoke(query)
    if isinstance(results, list):
        texts = [r["snippet"] if "snippet" in r else r.get("content", "") for r in results[:3]]
    else:
        texts = [str(results)]
    return {"results": texts if texts else ["Không tìm thấy kết quả."]}

# 2) Định nghĩa tool schema
tools = [
    {
        "type": "function",
        "function": {
            "name": "duckduckgo_search",
            "description": "Tìm kiếm thông tin trên web qua DuckDuckGo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Chuỗi truy vấn cần tìm kiếm"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def main():
    messages = [
        {"role": "system", "content": "Bạn là trợ lý AI; nếu không rõ câu trả lời, sử dụng tool call."},
        {"role": "user", "content": "Ai là chủ tịch nước Việt Nam hiện nay?"}
    ]

    # 3) Gọi lần đầu (streaming)
    response_stream = ollama.chat(
        model="qwen3:4b",
        messages=messages,
        tools=tools,
        stream=True
    )

    full_reply = ""
    tool_called = False

    for chunk in response_stream:
        msg = chunk["message"]

        # Nếu có tool_call
        if "tool_calls" in msg and msg["tool_calls"] and not tool_called:
            tool_called = True  # chỉ gọi 1 lần, tránh lặp
            call = msg["tool_calls"][0]
            print(f"\n>> TOOL_CALL: {call['function']['name']}({call['function']['arguments']})")

            args = call['function']['arguments']
            result = duckduckgo_search(args["query"])
            print(">> TOOL_RESULT:", result)

            # Cập nhật messages để tiếp tục cuộc hội thoại
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": msg["tool_calls"]
            })
            messages.append({
                "role": "tool",
                "name": call["function"]["name"],
                "content": json.dumps(result)
            })

            # Gọi lại model lần 2 (stream)
            response_stream2 = ollama.chat(
                model="qwen3:4b",
                messages=messages,
                tools=tools,
                stream=True
            )

            print("\n>> FINAL RESPONSE (STREAM):")
            for chunk2 in response_stream2:
                content = chunk2["message"].get("content", "")
                print(content, end="", flush=True)
            print()
            break

        # Nếu không phải tool call, chỉ in content
        elif "content" in msg and msg["content"]:
            content = msg["content"]
            print(content, end="", flush=True)
            full_reply += content

if __name__ == "__main__":
    main()