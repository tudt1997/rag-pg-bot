import os
import json
import time
from datetime import datetime
from flask import Flask, request, Response, stream_with_context, jsonify
from rag_system.components.llm_response.generate_response import LLMResponseGenerator
from flask_cors import CORS
from rag_system.services.vector_store import VectorStore

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Create index if haven't exist
vector_store = VectorStore()
vector_store.create_index()

DATA_FILE = 'sessions/conversations.json'
# ensure the sessions directory exists
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

UPLOAD_FOLDER = 'uploads'
HISTORY_FILE = 'sessions/uploads_history.json'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load existing conversations from disk, or start with empty dict
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        stored = json.load(f)
    order = stored.get('order', list(stored.get('conversations', {}).keys()))
    conversations = stored.get('conversations', {})
else:
    order = []
    conversations = {}

def save_conversations():
    data = {
        'order': order,
        'conversations': conversations
    }
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

searcher = LLMResponseGenerator()

@app.route('/conversations/reorder', methods=['POST'])
def reorder():
    data = request.get_json()
    conv_id = data.get('id')
    if conv_id in order:
        order.remove(conv_id)
    order.insert(0, conv_id)
    save_conversations()
    return jsonify({'success': True})

@app.route('/conversations', methods=['GET'])
def list_conversations():
    return jsonify([
        {'id': cid, 'title': conversations[cid]['title']}
        for cid in order if cid in conversations
    ])

@app.route('/conversation', methods=['POST'])
def create_conversation():
    """Start a new conversation and return its ID and title."""
    data = request.get_json()
    title = data.get('title') or f"Conversation {len(conversations) + 1}"
    conv_id = str(int(time.time() * 1000))
    conversations[conv_id] = {'title': title, 'messages': []}
    save_conversations()
    return jsonify({'id': conv_id, 'title': title})

@app.route('/conversation/<conv_id>', methods=['GET'])
def get_conversation(conv_id):
    """Fetch all messages for a given conversation."""
    conv = conversations.get(conv_id)
    if not conv:
        return jsonify({'error': 'Conversation not found'}), 404
    return jsonify(conv)

@app.route('/conversation/<conv_id>/message', methods=['POST'])
def stream_message(conv_id):
    data = request.get_json()
    user_msg = data.get('message')
    index_name = data.get('index_name', 'text_embeddings')
    enable_thinking = data.get('enable_thinking', False)   # << thêm dòng này

    if not user_msg:
        return jsonify({'error': 'message is required'}), 400

    conv = conversations.get(conv_id)
    if not conv:
        return jsonify({'error': 'Conversation not found'}), 404

    def generate():
        full_reply = ""
        for chunk in searcher.generate_response(index_name, user_msg, conv['messages'], enable_thinking=enable_thinking):
            full_reply += chunk
            yield chunk
        save_conversations()

    return Response(
        stream_with_context(generate()),
        mimetype='text/plain; charset=utf-8'
    )

@app.route('/conversation/<conv_id>', methods=['DELETE'])
def delete_conversation(conv_id):
    if conv_id not in conversations:
        return jsonify({'error': 'Conversation not found'}), 404
    del conversations[conv_id]
    if conv_id in order:
        order.remove(conv_id)
    save_conversations()
    return jsonify({'success': True})

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    original_filename = file.filename

    # Get the document name provided by the user
    user_given_name = request.form.get('name')
    if not user_given_name:
        return jsonify({'error': 'Document name is required.'}), 400

    # Determine file type and save with appropriate extension
    file_extension = os.path.splitext(original_filename)[1].lower()
    if file_extension == '.zip':
        filename = user_given_name + '.zip'
    else:
        filename = user_given_name + '.pdf'  # Default to PDF for other files
    
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)

    # Save upload history
    history_entry = {
        "file_name": original_filename,
        "user_given_name": user_given_name,
        "upload_time": datetime.now().isoformat()
    }

    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
    else:
        history_data = []

    history_data.append(history_entry)

    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

    # Process the file based on its type
    from rag_system.components.chunkers.fixed_size_chunker import LangchainCompatibleChunker
    from rag_system.components.embedders.embedder import Embedder

    chunker = LangchainCompatibleChunker()
    embedder = Embedder(index_name="text_embeddings")

    if file_extension == '.zip':
        # Handle zip file with markdown content
        from rag_system.components.loaders.zip_loader import ZipMarkdownLoader
        loader = ZipMarkdownLoader()
        data_chunks = loader.load(file_path)
    else:
        # Handle PDF files (existing functionality)
        from rag_system.components.loaders.local_loader import LocalOCRPDFLoader
        loader = LocalOCRPDFLoader()
        data_chunks = loader.load(file_path)

    # Chunk and embed the data
    chunked_data = chunker.chunk(data_chunks)
    embedder.embed_and_load(chunked_data)

    return jsonify({'message': f'Successfully uploaded and embedded file: {original_filename}'})

@app.route('/upload/history', methods=['GET'])
def get_upload_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
    else:
        history_data = []
    return jsonify(history_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)