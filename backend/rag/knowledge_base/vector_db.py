import math
import unicodedata
import re
from typing import List, Tuple

import qdrant_client
from bs4 import BeautifulSoup

from llama_index.core.schema import TextNode
from llama_index.core import (
    VectorStoreIndex, StorageContext,
    Settings
)
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.ollama import OllamaEmbedding
from rag.config import OLLAMA_URL, EMBEDDING_MODEL
from rag.document_processing.chunker import (
    chunk_html_table, build_yckt_row_payload, build_yckt_section_payload,
    build_yckt_overview_payload, build_yckt_prose_payloads,
)

embed_model = OllamaEmbedding(
    model_name=EMBEDDING_MODEL,
    base_url=OLLAMA_URL
)

Settings.embed_model = embed_model

def is_pseudo_header(element):
    """Heuristic: treat an element as a heading (real <hN> or bold-dominated short text)."""
    if element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return True
    if element.name in ['p', 'div']:
        plain_text = element.get_text(strip=True)
        if not plain_text or len(plain_text) > 150:
            return False
        bold_text = "".join(b.get_text(strip=True) for b in element.find_all(['strong', 'b']))
        if len(bold_text) / len(plain_text) > 0.8:
            return True
    return False

def clean_text_for_embedding(text):
    """Normalize text (NFKC), strip control/zero-width chars, collapse whitespace."""
    if not text:
        return ""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r"[\x00-\x1F\x7F-\x9F\u200B-\u200D\uFEFF]", '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def parse_html_to_nodes_smart(html_content, doc_name):
    """
    Parse a reference document's HTML into embedded nodes, grouped by heading.

    Accumulates content under the current heading chain; when a new heading is hit,
    flushes the buffered chunk into nodes (split into <= max_chars parts). Each node's
    text is the raw HTML (for the LLM) while the embedding is built from plain text.
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    nodes = []
    current_header = []
    current_chunk_html = ""

    elements = soup.body.children if soup.body else soup.children

    for element in elements:
        if element.name is None and not str(element).strip():
            continue

        if element.name is not None and is_pseudo_header(element):
            plain_text = BeautifulSoup(current_chunk_html, 'html.parser').get_text(separator=" ", strip=True)
            plain_text = clean_text_for_embedding(plain_text)

            if len(plain_text) > 20:
                header_chain = " - ".join(current_header) if current_header else "Quy định chung"

                # Original HTML
                html_for_llm = f"[SỞ CỨ: {doc_name} | MỤC: {header_chain}]\nNỘI DUNG HTML:\n{current_chunk_html}"

                max_chars = 1000
                text_parts = [plain_text[i:i+max_chars] for i in range(0, len(plain_text), max_chars)]

                for idx, part in enumerate(text_parts):
                    text_for_embedding = f"Văn bản: {doc_name}. Mục: {header_chain}. Phần {idx+1}. Nội dung: {part}"

                    try:
                        vector = embed_model.get_text_embedding(text_for_embedding)
                        if not any(math.isnan(v) for v in vector):
                            node = TextNode(
                                text=html_for_llm,
                                metadata={"van_ban": doc_name, "muc": header_chain, "phan": idx+1}
                            )
                            node.embedding = vector
                            nodes.append(node)
                    except Exception as e:
                        print(f"Lỗi Ollama phần {idx+1} mục '{header_chain}': {e}")

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

    # Handle the final chunk (apply the same splitting logic)
    tail_plain_text = BeautifulSoup(current_chunk_html, "html.parser").get_text(separator=" ", strip=True)
    tail_plain_text = clean_text_for_embedding(tail_plain_text)

    if len(tail_plain_text) > 20:
        header_chain = " - ".join(current_header) if current_header else "Quy định chung"
        html_for_llm = f"[SỞ CỨ: {doc_name} | MỤC: {header_chain}]\nNỘI DUNG HTML:\n{current_chunk_html}"

        max_chars = 1000
        text_parts = [tail_plain_text[i:i+max_chars] for i in range(0, len(tail_plain_text), max_chars)]

        for idx, part in enumerate(text_parts):
            text_for_embedding = f"Văn bản: {doc_name}. Mục: {header_chain}. Phần {idx+1}. Nội dung: {part}"
            try:
                vector = embed_model.get_text_embedding(text_for_embedding)
                if not any(math.isnan(v) for v in vector):
                    node = TextNode(
                        text=html_for_llm,
                        metadata={"van_ban": doc_name, "muc": header_chain, "phan": idx+1}
                    )
                    node.embedding = vector
                    nodes.append(node)
            except:
                pass

    print(f"  -> Đã bóc tách & nhúng vector thành công {len(nodes)} Node.")
    return nodes


def build_index_in_memory(
    html_docs: List[Tuple[str, str]],
    collection_name: str = "session_refs",
) -> Tuple[VectorStoreIndex, qdrant_client.QdrantClient, List]:
    """
    Build an in-memory Qdrant index from a list of (html_content, doc_name).
    Used per upload session instead of reading a prebuilt DB on disk.

    Args:
        html_docs: list of (html_content, document_name)
        collection_name: Qdrant collection name (each session uses its own)

    Returns:
        (VectorStoreIndex, QdrantClient, all_nodes)
        all_nodes is needed to build the BM25Retriever for hybrid search.
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
    Split a YCKT document into nodes by parameter ROW (for lookup/cross-checking).

    The field-extraction / text-formatting logic lives in chunker.build_yckt_row_payload
    (pure, testable without embedding). This function only cleans the text, embeds the
    vector and attaches it to a TextNode.

    Each node:
    - text  (LLM reads & cites): "[Tài liệu: X | Mục: ...]\\n<cells> "
    - embedding: vector of the plain text (section + requirement name + requirement value)
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
    Split a YCKT document into nodes by SECTION (group all rows of the same heading).

    This is the DEFAULT granularity for the chatbot lookup corpus: asking 'Van xả áp'
    returns the full information for that section instead of scattered individual rows.

    chunk_html_table with chunk_size=max_rows: each section (cut at the section-header
    row) becomes one chunk; max_rows is a safety cap for tables without sub-sections
    (e.g. a manufacturer-comparison table) to avoid an overly large node.
    """
    nodes: List[TextNode] = []
    chunks = chunk_html_table(html_content, chunk_size=max_rows, header_rows_count=2)

    section_names: List[str] = []

    def _embed_payload(payload) -> bool:
        """Embed the vector & attach a node from the payload. True on success."""
        text_for_embed = clean_text_for_embedding(payload["embed_source"])
        if not text_for_embed:
            return False
        try:
            vector = embed_model.get_text_embedding(text_for_embed)
        except Exception as e:  # noqa: BLE001
            print(f"[RAG] Lỗi embedding YCKT '{doc_name}': {e}")
            return False
        if any(math.isnan(v) for v in vector):
            return False
        node = TextNode(text=payload["text_for_llm"], metadata=payload["metadata"])
        node.embedding = vector
        nodes.append(node)
        return True

    for chunk in chunks:
        payload = build_yckt_section_payload(chunk, doc_name)
        if payload is None:
            continue
        if _embed_payload(payload):
            sec = payload["metadata"].get("section")
            if sec:
                section_names.append(sec)

    # OVERVIEW node: list all equipment/material of the document (prevents misses when
    # asking 'list the equipment in document X' but retrieval top_k doesn't cover every section).
    overview = build_yckt_overview_payload(doc_name, section_names)
    if overview is not None:
        _embed_payload(overview)

    # OUTSIDE-TABLE content nodes (paragraphs, headings, appendices...) — chunk_html_table
    # skips this part; added so the chatbot doesn't lose information when a question needs
    # both in-table and out-of-table data.
    prose_count = 0
    for payload in build_yckt_prose_payloads(html_content, doc_name):
        if _embed_payload(payload):
            prose_count += 1

    print(f"  -> YCKT '{doc_name}': nhúng {len(nodes)} node "
          f"({len(section_names)} mục + tổng quan + {prose_count} đoạn ngoài bảng).")
    return nodes


def build_yckt_index_in_memory(
    html_docs: List[Tuple[str, str]],
    collection_name: str = "yckt_session",
) -> Tuple[VectorStoreIndex, qdrant_client.QdrantClient, List]:
    """
    Build an in-memory Qdrant index by SECTION for the YCKT lookup corpus.

    Unlike build_index_in_memory (grouped by prose heading, used for legal reference
    sources): this function groups by table section (e.g. 'Van xả áp' = all of
    1.1.1..1.1.4) — suited to lookup/cross-checking by YCKT equipment cluster (both the
    historical store and the document under review).

    Args:
        html_docs: list of (html_content, document_name)
        collection_name: Qdrant collection name (each in-memory client is independent)

    Returns:
        (VectorStoreIndex, QdrantClient, all_nodes) — all_nodes is for building BM25.
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
    Create a hybrid retriever combining BM25 (lexical) + vector (semantic) with RRF fusion.

    BM25 is especially effective for Vietnamese technical keywords (equipment names,
    measurement units) that the nomic-embed-text (English) embedding model easily misses.

    Falls back to vector-only if llama-index-retrievers-bm25 / rank_bm25 is not installed.
    Install: pip install llama-index-retrievers-bm25

    Args:
        index: the built VectorStoreIndex (used for the vector retriever)
        nodes: list of TextNode — must be the same nodes used to build the index
        top_k: number of results returned by each retriever before fusion
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
            num_queries=1,       # disable query expansion, only fuse results
            mode="reciprocal_rerank",
            use_async=False,
        )
        print("[RAG] Hybrid retriever (BM25 + vector, RRF) sẵn sàng.")
        return hybrid

    except ImportError:
        print("[RAG] llama-index-retrievers-bm25 / rank_bm25 chưa cài — dùng vector-only.")
        return vector_retriever
