# This file to test question answering model

from rag_system.components.llm_response.generate_response import LLMResponseGenerator

def test_search():
    # Instantiate with search enabled
    generator = LLMResponseGenerator(enable_search=True)
    index_name = "text_embeddings"
    user_msg = "Ai là chủ tịch nước Việt Nam?"
    chat_history: list[dict[str, str]] = []

    full_reply = ""
    # Pass the same chat_history list so it gets updated by the generator
    for chunk in generator.generate_response(index_name, user_msg, chat_history, enable_thinking = False):
        full_reply += chunk
        print(chunk, end='', flush=True)

    print("\nFull reply:", full_reply)

if __name__ == "__main__":
    test_search()