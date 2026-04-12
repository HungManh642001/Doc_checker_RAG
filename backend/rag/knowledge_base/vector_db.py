import os
import math
import unicodedata
import re
import qdrant_client
from bs4 import BeautifulSoup

from llama_index.core.schema import TextNode
from llama_index.core import (
    VectorStoreIndex, StorageContext,
    Settings
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.embeddings.ollama import OllamaEmbedding
from config import OLLAMA_URL,EMBEDDING_MODEL, EMBEDDING_MODEL_PATH, EMBEDDING_CACHE_FOLDER

# embed_model = HuggingFaceEmbedding(
#     model_name=EMBEDDING_MODEL_PATH,
#     cache_folder=EMBEDDING_CACHE_FOLDER,
#     device='cuda',
#     trust_remote_code=True,
# )

embed_model = OllamaEmbedding(
    model_name=EMBEDDING_MODEL,
    base_url=OLLAMA_URL
)

Settings.embed_model = embed_model

def is_pseudo_header(element):
    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return True
    if element.name in ['p', 'div']:
        text_thuan = element.get_text(strip=True)
        if not text_thuan or len(text_thuan) > 150:
            return False
        bold_text = "".join(b.get_text(strip=True) for b in element.find_all(['strong', 'b']))
        if len(bold_text) / len(text_thuan) > 0.8:
            return True
    return False

def clean_text_for_embedding(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r"[\x00-\x1F\x7F-\x9F\u200B-\u200D\uFEFF]", '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_html_to_nodes_smart(html_content, ten_van_ban):
    soup = BeautifulSoup(html_content, 'html.parser')
    nodes = []
    current_header = []
    current_chunk_html = ""

    elements = soup.body.children if soup.body else soup.children

    for element in elements:
        if element.name is None and not str(element).strip():
            continue

        if element.name is not None and is_pseudo_header(element):
            text_thuan = BeautifulSoup(current_chunk_html, 'html.parser').get_text(separator=" ", strip=True)
            text_thuan = clean_text_for_embedding(text_thuan)

            if len(text_thuan) > 20:
                chuoi_header = " - ".join(current_header) if current_header else "Quy định chung"

                # HTML nguyên bản
                html_cho_llm = f"[SỞ CỨ: {ten_van_ban} | MỤC: {chuoi_header}]\nNỘI DUNG HTML:\n{current_chunk_html}"

                max_chars = 1000
                text_parts = [text_thuan[i:i+max_chars] for i in range(0, len(text_thuan), max_chars)]

                for idx, part in enumerate(text_parts):
                    text_cho_embed = f"Văn bản: {ten_van_ban}. Mục: {chuoi_header}. Phần {idx+1}. Nội dung: {part}"

                    try:
                        vector = embed_model.get_text_embedding(text_cho_embed)
                        if not any(math.isnan(v) for v in vector):
                            node = TextNode(
                                text=html_cho_llm,
                                metadata={"van_ban": ten_van_ban, "muc": chuoi_header, "phan": idx+1}
                            )
                            node.embedding = vector
                            nodes.append(node)
                    except Exception as e:
                        print(f"Lỗi Ollama phần {idx+1} mục '{chuoi_header}': {e}")
                
                # Reset chunk
                current_header = [clean_text_for_embedding(element.get_text())]
                current_chunk_html = str(element)
            
            else:
                header_text = clean_text_for_embedding(element.get_text())
                if header_text not in current_header:
                    current_header.append(header_text)
                current_chunk_html += str(element)
        
        else:
            current_chunk_html += str(element)
    
    # Xử lý đoạn chunk cuối cùng (áp dụng logic chia nhỏ tương tự)
    text_thuan_cuoi = BeautifulSoup(current_chunk_html, "html.parser").get_text(separator=" ", strip=True)
    text_thuan_cuoi = clean_text_for_embedding(text_thuan_cuoi)

    if len(text_thuan_cuoi) > 20:
        chuoi_header = " - ".join(current_header) if current_header else "Quy định chung"
        html_cho_llm = f"[SỞ CỨ: {ten_van_ban} | MỤC: {chuoi_header}]\nNỘI DUNG HTML:\n{current_chunk_html}"

        max_chars = 1000
        text_parts = [text_thuan_cuoi[i:i+max_chars] for i in range(0, len(text_thuan_cuoi), max_chars)]

        for idx, part in enumerate(text_parts):
            text_cho_embed = f"Văn bản: {ten_van_ban}. Mục: {chuoi_header}. Phần {idx+1}. Nội dung: {part}"
            try:
                vector = embed_model.get_text_embedding(text_cho_embed)
                if not any(math.isnan(v) for v in vector):
                    node = TextNode(
                        text=html_cho_llm,
                        metadata={"van_ban": ten_van_ban, "muc": chuoi_header, "phan": idx+1}
                    )
                    node.embedding = vector
                    nodes.append(node)
            except:
                pass

    print(f"  -> Đã bóc tách & nhúng vector thành công {len(nodes)} Node.")
    return nodes

def get_or_build_index(data_dir="./data/reference_html", db_path='./data/qdrant_db', collection_name="van_ban_so_cu"):
    client = qdrant_client.QdrantClient(path=db_path)
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    try:
        if client.collection_exists(collection_name) and client.get_collection(collection_name).vectors_count > 0:
            print(f"Đã tải Database '{collection_name}' từ ổ cứng")
            return VectorStoreIndex.from_vector_store(vector_store=vector_store)
    except Exception:
        pass

    print(f"Đang tạo Database mới từ thư mục '{data_dir}'...")
    all_nodes = []
    for filename in os.listdir(data_dir):
        if filename.endswith(".html"):
            filepath = os.path.join(data_dir, filename)
            with open(filepath, "r", encoding='utf-8') as f:
                noi_dung_html = f.read()
            nodes_cua_file = parse_html_to_nodes_smart(noi_dung_html, filename)
            all_nodes.extend(nodes_cua_file)
    
    if not all_nodes:
        raise ValueError("Không trích xuất được Node nào hợp lệ.")
    
    index = VectorStoreIndex(nodes=all_nodes, storage_context=storage_context)
    print("Lưu Qdrant database thành công!")
    return index, client

def load_existing_index(db_path='./data/qdrant_db', collection_name="van_ban_so_cu"):
    client = qdrant_client.QdrantClient(path=db_path)
    vector_store = QdrantVectorStore(
        client=client,
        collection_name=collection_name
    )

    index = VectorStoreIndex.from_vector_store(
        vector_store=vector_store,
        embed_model=embed_model
    )
    return index, client

def test_retrieval(index, query_html_chunk, top_k=5):
    retriever = index.as_retriever(similarity_top_k=top_k)

    nodes = retriever.retrieve(query_html_chunk)
    print(f"\n Tìm thấy {len(nodes)} đoạn context liên quan:")
    print("-"*50)
    for i, node in enumerate(nodes):
        print(f"\n[Top {i+1}] Độ tương đồng (Score): {node.score}")
        print(f"Tên file/metadata: {node.metadata}")
        print(f"Nội dung nguyên bản:\n{node.text}")
        print("-"*50)
