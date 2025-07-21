from typing import List
import os
import zipfile
import tempfile
from rag_system.core.data_chunk import DataChunk
from .loader_base import DataLoaderBase

class ZipMarkdownLoader(DataLoaderBase):
    def __init__(self):
        super().__init__()
    
    def load(self, zip_path: str) -> List[DataChunk]:
        '''
        Load markdown files from folders within a zip file and return DataChunks.
        Each markdown file becomes a DataChunk.
        '''
        data_chunks = []
        offset = 0
        
        # Create a temporary directory to extract files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Walk through the extracted directory structure
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith('.md'):
                        file_path = os.path.join(root, file)
                        
                        # Get relative path for source tracking
                        rel_path = os.path.relpath(file_path, temp_dir)
                        folder_name = os.path.dirname(rel_path)
                        
                        # Read the markdown file with error handling
                        try:
                            # First try UTF-8
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                        except UnicodeDecodeError:
                            try:
                                # If UTF-8 fails, try with Latin-1 (which can read any byte sequence)
                                with open(file_path, 'r', encoding='latin-1') as f:
                                    content = f.read()
                            except Exception as e:
                                # If all fails, skip this file and log the error
                                print(f"Error reading file {file_path}: {e}")
                                continue
                        
                        # Create a DataChunk for this markdown file
                        chunk = DataChunk(
                            content=content,
                            source=f"{os.path.basename(zip_path)}:{folder_name}/{file}",
                            offset=offset,
                            page_number=None  # Markdown files don't have pages
                        )
                        
                        data_chunks.append(chunk)
                        offset += len(content)
        
        return data_chunks