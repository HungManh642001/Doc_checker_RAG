import re
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional, Tuple

# Trích tên "Mục" (đề mục/phân cấp) mà chunker đã inject vào mỗi chunk.
_RE_MUC = re.compile(r'<!--\s*Mục:\s*(.+?)\s*-->')


def extract_muc(html_chunk: str) -> str:
    """Lấy tên đề mục từ comment <!-- Mục: ... --> trong chunk (rỗng nếu không có)."""
    m = _RE_MUC.search(html_chunk or '')
    return m.group(1).strip() if m else ''


# ---------------------------------------------------------------------------
# Trích trường có cấu trúc từ một mini-table chunk (dùng cho corpus tra cứu YCKT)
# ---------------------------------------------------------------------------

def row_chunk_to_fields(html_chunk: str) -> Dict[str, object]:
    """
    Trích các trường có cấu trúc từ một mini-table chunk (header + 1 dòng dữ liệu).

    Dùng cho corpus tra cứu chatbot (kho YCKT lịch sử + tài liệu đang xét) — nơi mỗi
    DÒNG thông số là một đơn vị truy hồi, khác parse_html_to_nodes_smart (gom theo
    heading, dùng cho sở cứ pháp lý).

    Cấu trúc cột YCKT giả định: TT | Tên yêu cầu | Giá trị yêu cầu | (Tiêu chí | PP...).

    Returns:
        {
          "section": <tên đề mục từ comment <!-- Mục: ... -->>,
          "tt": <cột 1>, "param_name": <cột 2>, "param_value": <cột 3>,
          "cells": [<toàn bộ cell dữ liệu>],
        }
    """
    section = extract_muc(html_chunk)
    soup = BeautifulSoup(html_chunk, 'html.parser')

    cells: List[str] = []
    for row in soup.find_all('tr'):
        if row.find('th'):
            continue  # bỏ dòng header
        tds = row.find_all('td', recursive=False)
        texts = [c.get_text(separator=' ', strip=True) for c in tds]
        if any(texts):
            cells = texts
            break  # chunk_size=1 → chỉ có 1 dòng dữ liệu thực

    return {
        'section': section,
        'tt': cells[0] if len(cells) > 0 else '',
        'param_name': cells[1] if len(cells) > 1 else '',
        'param_value': cells[2] if len(cells) > 2 else '',
        'cells': cells,
    }


def build_yckt_row_payload(html_chunk: str, doc_name: str) -> Optional[Dict[str, object]]:
    """
    Dựng payload cho một node YCKT theo dòng (chưa nhúng vector).

    Tách phần logic THUẦN (không phụ thuộc llama_index/embedding) khỏi vector_db để
    dễ test: vector_db chỉ việc làm sạch `embed_source`, nhúng vector rồi gắn vào node.

    Returns:
        None nếu dòng không có dữ liệu trích xuất được, ngược lại:
        {
          "text_for_llm": <chuỗi LLM đọc & trích dẫn, nêu rõ nguồn tài liệu>,
          "embed_source": <chuỗi thô để embed (Mục + Tên + Giá trị)>,
          "metadata": {doc_name, section, tt, param_name, param_value},
        }
    """
    fields = row_chunk_to_fields(html_chunk)
    cells: List[str] = fields['cells']  # type: ignore[assignment]
    if not cells:
        return None

    section = fields['section']
    cell_text = ' | '.join(c for c in cells if c)

    ctx = f' | Mục: {section}' if section else ''
    text_for_llm = f'[Tài liệu: {doc_name}{ctx}]\n{cell_text}'

    embed_parts = [
        p for p in (section, fields['param_name'], fields['param_value']) if p
    ]
    embed_source = '. '.join(embed_parts) or cell_text
    if not embed_source.strip():
        return None

    return {
        'text_for_llm': text_for_llm,
        'embed_source': embed_source,
        'metadata': {
            'doc_name': doc_name,
            'section': section,
            'tt': fields['tt'],
            'param_name': fields['param_name'],
            'param_value': fields['param_value'],
        },
    }


def chunk_html_table(
    html_content: str,
    chunk_size: int = 1,
    header_rows_count: int = 2,
) -> List[str]:
    """
    Chia HTML bảng thành danh sách mini-table HTML chunk để đưa vào pipeline thẩm định.

    Mỗi chunk có dạng:
        <!-- Mục: <tên phân cấp> -->   (nếu có dòng section header trước đó)
        <table>
            <header row(s)>
            <chunk_size dòng dữ liệu>
        </table>

    Cải tiến so với phiên bản cũ:
    - Tự động đếm header rows từ <thead>/<tbody>; header_rows_count chỉ là fallback
      khi bảng không có <thead> — giải quyết lỗi Phụ lục 1 (3-row header bị cắt còn 2).
    - Dòng colspan (tiêu đề phân cấp "1.1 Van xả áp", "Bộ công cụ dụng cụ"…) không
      tạo chunk riêng mà được inject vào comment <!-- Mục: --> của các chunk sau —
      LLM vẫn có ngữ cảnh phân cấp mà không tốn thêm LLM call.
    - Bảng wrapper (tbody chỉ chứa nested table) bị bỏ qua; bảng dữ liệu thực bên
      trong (Phụ lục 2) được xử lý trực tiếp — không lặp cũng không bỏ sót.
    - Bảng lồng bên trong bảng dữ liệu thực (non-wrapper) bị bỏ qua.

    Args:
        html_content: toàn bộ HTML tài liệu
        chunk_size: số dòng dữ liệu thực tế mỗi chunk
        header_rows_count: số dòng header dự phòng khi bảng không có <thead>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    chunks: List[str] = []

    for table in soup.find_all('table'):
        parent = table.find_parent('table')
        if parent is not None:
            # Bảng lồng bên trong một bảng khác:
            # - Nếu bảng cha là wrapper → đây là bảng dữ liệu thực → xử lý
            # - Nếu bảng cha là bảng dữ liệu → đây là nested table inline → bỏ qua
            if not _is_wrapper_table(parent):
                continue
        else:
            # Bảng cấp cao nhất nhưng chỉ chứa nested table → bỏ qua
            if _is_wrapper_table(table):
                continue

        header_rows, data_rows = _split_header_data(table, header_rows_count)
        if not header_rows or not data_rows:
            continue

        total_cols = _count_cols(header_rows[0])
        header_html = ''.join(str(r) for r in header_rows)

        current_section = ''
        batch: List[Tag] = []

        for row in data_rows:
            if _is_section_header(row, total_cols):
                if batch:
                    chunks.append(_make_chunk(header_html, batch, current_section))
                    batch = []
                current_section = row.get_text(separator=' ', strip=True)
            else:
                batch.append(row)
                if len(batch) >= chunk_size:
                    chunks.append(_make_chunk(header_html, batch, current_section))
                    batch = []

        if batch:
            chunks.append(_make_chunk(header_html, batch, current_section))

    # Fallback: không tìm thấy bảng nào có cấu trúc hợp lệ
    if not chunks:
        return [html_content[i:i + 4000] for i in range(0, len(html_content), 4000)]
    return chunks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_wrapper_table(table: Tag) -> bool:
    """
    Trả True nếu bảng chỉ là wrapper bọc ngoài bảng khác.
    Heuristic: TẤT CẢ direct-tr của tbody đều chứa nested <table>.
    Ví dụ: Phụ lục 2 outer table.
    """
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr', recursive=False)
    else:
        rows = [el for el in table.children if isinstance(el, Tag) and el.name == 'tr']
    return bool(rows) and all(row.find('table') is not None for row in rows)


def _split_header_data(
    table: Tag,
    fallback_header_count: int,
) -> Tuple[List[Tag], List[Tag]]:
    """Tách header rows và data rows từ một <table> element."""
    thead = table.find('thead')
    tbody = table.find('tbody')

    if thead and tbody:
        # Cấu trúc đầy đủ: dùng thead và tbody trực tiếp
        return (
            thead.find_all('tr', recursive=False),
            tbody.find_all('tr', recursive=False),
        )

    if thead:
        # Có thead nhưng không có tbody: data rows là tất cả tr không thuộc thead
        header_rows = thead.find_all('tr', recursive=False)
        header_ids = {id(r) for r in header_rows}
        data_rows = [r for r in table.find_all('tr') if id(r) not in header_ids]
        return header_rows, data_rows

    # Không có thead/tbody: lấy tất cả tr, cắt theo fallback_header_count
    all_rows = table.find_all('tr')
    if len(all_rows) <= fallback_header_count:
        return [], []
    return all_rows[:fallback_header_count], all_rows[fallback_header_count:]


def _count_cols(row: Tag) -> int:
    """Đếm tổng số cột (tính colspan) của một dòng."""
    return sum(
        int(c.get('colspan', 1))
        for c in row.find_all(['td', 'th'], recursive=False)
    )


def _is_section_header(row: Tag, total_cols: int) -> bool:
    """
    Trả True nếu row là dòng tiêu đề phân cấp (colspan lớn, ít cell thực).
    Ví dụ: <tr><td>1.1</td><td colspan="5">Van xả áp</td></tr>
    """
    cells = row.find_all(['td', 'th'], recursive=False)
    if not cells:
        return True  # dòng rỗng
    span = sum(int(c.get('colspan', 1)) for c in cells)
    # Tiêu đề phân cấp: tối đa 2 cell, tổng colspan chiếm >= 2/3 tổng số cột
    return len(cells) <= 2 and span >= max(total_cols * 2 // 3, 2)


def _make_chunk(header_html: str, rows: List[Tag], section: str) -> str:
    """Tạo HTML string cho một chunk: comment context + mini-table."""
    rows_html = ''.join(str(r) for r in rows)
    ctx = f'<!-- Mục: {section} -->\n' if section else ''
    return f'{ctx}<table>{header_html}{rows_html}</table>'
