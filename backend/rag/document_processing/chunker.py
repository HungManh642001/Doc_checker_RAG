import re
from bs4 import BeautifulSoup, Tag
from typing import List, Tuple

# Trích tên "Mục" (đề mục/phân cấp) mà chunker đã inject vào mỗi chunk.
_RE_MUC = re.compile(r'<!--\s*Mục:\s*(.+?)\s*-->')


def extract_muc(html_chunk: str) -> str:
    """Lấy tên đề mục từ comment <!-- Mục: ... --> trong chunk (rỗng nếu không có)."""
    m = _RE_MUC.search(html_chunk or '')
    return m.group(1).strip() if m else ''


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
