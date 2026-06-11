import os
import math
import unicodedata
import re
from pathlib import Path
from typing import List, Tuple

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
from rag.config import OLLAMA_URL, EMBEDDING_MODEL, EMBEDDING_MODEL_PATH, EMBEDDING_CACHE_FOLDER
from rag.document_processing.chunker import (
    chunk_html_table, build_yckt_row_payload, build_yckt_section_payload,
)

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

_RAG_DATA = Path(__file__).parent.parent / "data"


def get_or_build_index(
    data_dir: str | None = None,
    db_path: str | None = None,
    collection_name: str = "van_ban_so_cu",
):
    data_dir = data_dir or str(_RAG_DATA / "reference_html")
    db_path = db_path or str(_RAG_DATA / "qdrant_db")
    client = qdrant_client.QdrantClient(path=db_path)
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    try:
        if client.collection_exists(collection_name) and client.get_collection(collection_name).vectors_count > 0:
            print(f"Đã tải Database '{collection_name}' từ ổ cứng")
            index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
            return index, client
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

def build_index_in_memory(
    html_docs: List[Tuple[str, str]],
    collection_name: str = "session_refs",
) -> Tuple[VectorStoreIndex, qdrant_client.QdrantClient, List]:
    """
    Dựng Qdrant index in-memory từ danh sách (html_content, doc_name).
    Dùng cho mỗi session upload thay vì đọc DB dựng sẵn trên ổ cứng.

    Args:
        html_docs: list of (html_content, document_name)
        collection_name: tên collection Qdrant (mỗi session dùng riêng)

    Returns:
        (VectorStoreIndex, QdrantClient, all_nodes)
        all_nodes cần thiết để xây BM25Retriever cho hybrid search.
    """
    all_nodes: List = []
    for html_content, doc_name in html_docs:
        nodes = parse_html_to_nodes_smart(html_content, doc_name)
        all_nodes.extend(nodes)

    if not all_nodes:
        raise ValueError("Không trích xuất được node nào từ sở cứ đã cung cấp.")

    client = qdrant_client.QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(nodes=all_nodes, storage_context=storage_context)
    return index, client, all_nodes


def yckt_rows_to_nodes(html_content: str, doc_name: str) -> List[TextNode]:
    """
    Chẻ một tài liệu YCKT thành các node theo DÒNG thông số (để tra cứu/đối chiếu).

    Logic trích trường/định dạng text nằm ở chunker.build_yckt_row_payload (thuần,
    test được không cần embedding). Hàm này chỉ làm sạch text, nhúng vector và
    gắn vào TextNode.

    Mỗi node:
    - text  (LLM đọc & trích dẫn): "[Tài liệu: X | Mục: ...]\\n<các cell> "
    - embedding: vector của plain text (Mục + Tên yêu cầu + Giá trị yêu cầu)
    - metadata: doc_name, section, tt, param_name, param_value
    """
    nodes: List[TextNode] = []
    chunks = chunk_html_table(html_content, chunk_size=1, header_rows_count=2)

    for chunk in chunks:
        payload = build_yckt_row_payload(chunk, doc_name)
        if payload is None:
            continue

        text_for_embed = clean_text_for_embedding(payload["embed_source"])
        if not text_for_embed:
            continue

        try:
            vector = embed_model.get_text_embedding(text_for_embed)
        except Exception as e:  # noqa: BLE001
            print(f"[RAG] Lỗi embedding dòng YCKT '{doc_name}': {e}")
            continue
        if any(math.isnan(v) for v in vector):
            continue

        node = TextNode(text=payload["text_for_llm"], metadata=payload["metadata"])
        node.embedding = vector
        nodes.append(node)

    print(f"  -> YCKT '{doc_name}': bóc tách & nhúng {len(nodes)} dòng thông số.")
    return nodes


def yckt_sections_to_nodes(
    html_content: str, doc_name: str, max_rows: int = 40
) -> List[TextNode]:
    """
    Chẻ một tài liệu YCKT thành các node theo MỤC (gom mọi dòng cùng đề mục).

    Đây là granularity MẶC ĐỊNH cho corpus tra cứu chatbot: hỏi 'Van xả áp' trả về
    đủ thông tin mục đó thay vì từng dòng rời rạc.

    chunk_html_table với chunk_size=max_rows: mỗi mục (cắt ở dòng section header)
    thành một chunk; max_rows là trần an toàn cho bảng không có đề mục con (vd bảng
    so sánh NSX) để tránh node quá lớn.
    """
    nodes: List[TextNode] = []
    chunks = chunk_html_table(html_content, chunk_size=max_rows, header_rows_count=2)

    for chunk in chunks:
        payload = build_yckt_section_payload(chunk, doc_name)
        if payload is None:
            continue

        text_for_embed = clean_text_for_embedding(payload["embed_source"])
        if not text_for_embed:
            continue

        try:
            vector = embed_model.get_text_embedding(text_for_embed)
        except Exception as e:  # noqa: BLE001
            print(f"[RAG] Lỗi embedding mục YCKT '{doc_name}': {e}")
            continue
        if any(math.isnan(v) for v in vector):
            continue

        node = TextNode(text=payload["text_for_llm"], metadata=payload["metadata"])
        node.embedding = vector
        nodes.append(node)

    print(f"  -> YCKT '{doc_name}': bóc tách & nhúng {len(nodes)} mục.")
    return nodes


def build_yckt_index_in_memory(
    html_docs: List[Tuple[str, str]],
    collection_name: str = "yckt_session",
) -> Tuple[VectorStoreIndex, qdrant_client.QdrantClient, List]:
    """
    Dựng Qdrant index in-memory theo MỤC cho corpus tra cứu YCKT.

    Khác build_index_in_memory (gom theo heading văn bản, dùng cho sở cứ pháp lý):
    hàm này gom theo đề mục bảng (vd 'Van xả áp' = đủ 1.1.1..1.1.4) — phù hợp tra
    cứu/đối chiếu theo cụm thiết bị YCKT (kho lịch sử và tài liệu đang xét).

    Args:
        html_docs: list of (html_content, document_name)
        collection_name: tên collection Qdrant (mỗi client in-memory độc lập)

    Returns:
        (VectorStoreIndex, QdrantClient, all_nodes) — all_nodes để dựng BM25.
    """
    all_nodes: List = []
    for html_content, doc_name in html_docs:
        all_nodes.extend(yckt_sections_to_nodes(html_content, doc_name))

    if not all_nodes:
        raise ValueError("Không trích xuất được mục thông số nào từ tài liệu YCKT.")

    client = qdrant_client.QdrantClient(location=":memory:")
    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    index = VectorStoreIndex(nodes=all_nodes, storage_context=storage_context)
    return index, client, all_nodes


def build_hybrid_retriever(
    index: VectorStoreIndex,
    nodes: List,
    top_k: int = 6,
):
    """
    Tạo hybrid retriever kết hợp BM25 (lexical) + vector (semantic) với RRF fusion.

    BM25 đặc biệt hiệu quả với từ khóa kỹ thuật tiếng Việt (tên thiết bị, đơn vị đo)
    mà embedding model nomic-embed-text (tiếng Anh) dễ bỏ sót.

    Fallback sang vector-only nếu llama-index-retrievers-bm25 / rank_bm25 chưa cài.
    Cài đặt: pip install llama-index-retrievers-bm25

    Args:
        index: VectorStoreIndex đã dựng (dùng cho vector retriever)
        nodes: list TextNode — phải là cùng nodes đã dùng để dựng index
        top_k: số kết quả trả về từ mỗi retriever trước khi fuse
    """
    vector_retriever = index.as_retriever(similarity_top_k=top_k)

    try:
        from llama_index.retrievers.bm25 import BM25Retriever
        from llama_index.core.retrievers import QueryFusionRetriever

        bm25_retriever = BM25Retriever.from_defaults(
            nodes=nodes,
            similarity_top_k=top_k,
        )
        hybrid = QueryFusionRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            similarity_top_k=top_k,
            num_queries=1,       # tắt query expansion, chỉ fuse kết quả
            mode="reciprocal_rerank",
            use_async=False,
        )
        print("[RAG] Hybrid retriever (BM25 + vector, RRF) sẵn sàng.")
        return hybrid

    except ImportError:
        print("[RAG] llama-index-retrievers-bm25 / rank_bm25 chưa cài — dùng vector-only.")
        return vector_retriever


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
