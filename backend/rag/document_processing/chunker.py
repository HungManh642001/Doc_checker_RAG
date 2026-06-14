import re
from bs4 import BeautifulSoup, Tag
from typing import Dict, List, Optional, Tuple

# Extract the "Mục" name (section heading / hierarchy) that the chunker injected into each chunk.
_RE_MUC = re.compile(r'<!--\s*Mục:\s*(.+?)\s*-->')


def extract_muc(html_chunk: str) -> str:
    """Get the section name from the <!-- Mục: ... --> comment in a chunk (empty if absent)."""
    m = _RE_MUC.search(html_chunk or '')
    return m.group(1).strip() if m else ''


# ---------------------------------------------------------------------------
# Extract structured fields from a mini-table chunk (used for the YCKT lookup corpus)
# ---------------------------------------------------------------------------

def row_chunk_to_fields(html_chunk: str) -> Dict[str, object]:
    """
    Extract structured fields from a mini-table chunk (header + 1 data row).

    Used for the chatbot lookup corpus (historical YCKT store + document under review),
    where each parameter ROW is a retrieval unit — unlike parse_html_to_nodes_smart
    (grouped by heading, used for legal reference sources).

    Assumed YCKT column layout: TT | Requirement name | Requirement value | (Criteria | Method...).

    Returns:
        {
          "section": <section name from the <!-- Mục: ... --> comment>,
          "tt": <column 1>, "param_name": <column 2>, "param_value": <column 3>,
          "cells": [<all data cells>],
        }
    """
    section = extract_muc(html_chunk)
    soup = BeautifulSoup(html_chunk, 'html.parser')

    cells: List[str] = []
    for row in soup.find_all('tr'):
        if row.find('th'):
            continue  # skip header row
        tds = row.find_all('td', recursive=False)
        texts = [c.get_text(separator=' ', strip=True) for c in tds]
        if any(texts):
            cells = texts
            break  # chunk_size=1 → only one real data row

    return {
        'section': section,
        'tt': cells[0] if len(cells) > 0 else '',
        'param_name': cells[1] if len(cells) > 1 else '',
        'param_value': cells[2] if len(cells) > 2 else '',
        'cells': cells,
    }


def build_yckt_row_payload(html_chunk: str, doc_name: str) -> Optional[Dict[str, object]]:
    """
    Build the payload for a row-level YCKT node (vector not yet embedded).

    Separates the PURE logic (no llama_index/embedding dependency) from vector_db for
    easier testing: vector_db only cleans `embed_source`, embeds the vector and attaches
    it to the node.

    Returns:
        None if the row has no extractable data, otherwise:
        {
          "text_for_llm": <string the LLM reads & cites, stating the source document>,
          "embed_source": <raw string to embed (section + name + value)>,
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


def build_yckt_section_payload(
    html_chunk: str, doc_name: str, max_embed_chars: int = 4000
) -> Optional[Dict[str, object]]:
    """
    Build the payload for a SECTION-level YCKT node — group ALL parameter rows within
    the same section heading (e.g. 'Van xả áp' covering 1.1.1..1.1.4) into ONE node.

    Optimized to NOT LOSE INFORMATION during chatbot lookup:
    - text_for_llm: includes the COLUMN-LABEL row (from <th>) + every data row (all
      columns) → the LLM understands what each column is and sees the full information
      (including explanation/reference/manufacturer-assessment columns in wide tables).
    - embed_source: merges EVERY non-empty cell of every row (not just name+value) →
      retrieval still finds it no matter which column the keyword is in. Truncated to
      max_embed_chars so large tables don't exceed the embedding limit.

    Use together with chunk_html_table(large chunk_size) so each chunk = one section.

    Returns:
        None if the chunk has no data rows, otherwise:
        {"text_for_llm", "embed_source", "metadata": {doc_name, section,
         param_name (merged), param_value, row_count}}
    """
    section = extract_muc(html_chunk)
    soup = BeautifulSoup(html_chunk, 'html.parser')

    # Column labels from the first <th> header row (helps the LLM understand the columns)
    header_labels: List[str] = []
    for row in soup.find_all('tr'):
        ths = row.find_all('th', recursive=False)
        if ths:
            labels = [t.get_text(separator=' ', strip=True) for t in ths]
            if any(labels):
                header_labels = labels
                break

    data_rows: List[List[str]] = []
    for row in soup.find_all('tr'):
        if row.find('th'):
            continue  # skip header row
        tds = row.find_all('td', recursive=False)
        texts = [c.get_text(separator=' ', strip=True) for c in tds]
        if any(texts):
            data_rows.append(texts)

    if not data_rows:
        return None

    lines: List[str] = []
    param_names: List[str] = []
    embed_bits: List[str] = []
    if section:
        embed_bits.append(section)

    for cells in data_rows:
        lines.append(' | '.join(c for c in cells if c))
        if len(cells) > 1 and cells[1]:
            param_names.append(cells[1])
        # embed EVERY non-empty cell → boost recall (info is found in whichever column)
        embed_bits.append(' '.join(c for c in cells if c))

    embed_source = '. '.join(b for b in embed_bits if b and b.strip())[:max_embed_chars]
    if not embed_source.strip():
        return None

    header_line = ''
    if header_labels:
        header_line = 'Cột: ' + ' | '.join(h for h in header_labels if h) + '\n'
    ctx = f' | Mục: {section}' if section else ''
    text_for_llm = f'[Tài liệu: {doc_name}{ctx}]\n{header_line}' + '\n'.join(lines)

    return {
        'text_for_llm': text_for_llm,
        'embed_source': embed_source,
        'metadata': {
            'doc_name': doc_name,
            'section': section,
            'param_name': '; '.join(param_names),
            'param_value': '',
            'row_count': len(data_rows),
        },
    }


def build_yckt_overview_payload(
    doc_name: str, section_names: List[str]
) -> Optional[Dict[str, object]]:
    """
    Build an OVERVIEW node for a YCKT document: list every equipment/material name
    (section) in the document.

    Purpose: questions like 'list the equipment in which YCKT', 'what equipment does
    document X have' need to see ALL section names — but retrieval top_k is limited so
    items are easily missed. A single overview node makes one retrieval enough for the
    complete list.

    Returns None if there are no sections.
    """
    names = [s.strip() for s in section_names if s and s.strip()]
    # de-duplicate while preserving order
    seen = set()
    unique = [n for n in names if not (n in seen or seen.add(n))]
    if not unique:
        return None

    joined = '; '.join(unique)
    text_for_llm = (
        f'[Tài liệu: {doc_name} | Tổng quan]\n'
        f'Các thiết bị/vật liệu (mục) trong tài liệu này: {joined}'
    )
    return {
        'text_for_llm': text_for_llm,
        'embed_source': f'{doc_name}. Danh sách thiết bị/vật liệu: {joined}',
        'metadata': {
            'doc_name': doc_name,
            'section': '(Tổng quan tài liệu)',
            'param_name': joined,
            'param_value': '',
            'row_count': 0,
        },
    }


def _looks_like_heading(el: Tag, txt: str) -> bool:
    """Heuristic to detect a prose heading/section line (outside tables)."""
    if el.name in ('h1', 'h2', 'h3', 'h4', 'h5', 'h6'):
        return True
    if txt and len(txt) <= 120:
        bold = ''.join(b.get_text(strip=True) for b in el.find_all(['strong', 'b']))
        if len(bold) >= 0.6 * len(txt):
            return True
        if re.match(r'^(Phụ lục|PHỤ LỤC|Chương|Mục|[IVX]+\.|\d+(\.\d+)*\.?)\s', txt):
            return True
    return False


def build_yckt_prose_payloads(
    html_content: str, doc_name: str, max_chars: int = 1200
) -> List[Dict[str, object]]:
    """
    Extract OUTSIDE-TABLE content (paragraphs, headings, lists) into text nodes.

    IMPORTANT: chunk_html_table only handles <table> → all non-table text is dropped.
    This function compensates so the chatbot doesn't lose information when a question
    needs data both inside and outside the table.

    Groups text by the nearest heading; truncated by max_chars. Returns a list of
    payloads like build_yckt_section_payload (text_for_llm / embed_source / metadata).
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    for t in soup.find_all('table'):
        t.decompose()  # tables are handled separately in yckt_sections_to_nodes
    root = soup.body or soup

    payloads: List[Dict[str, object]] = []
    current_heading = ''
    buffer: List[str] = []

    def _flush() -> None:
        nonlocal buffer
        text = re.sub(r'\s+', ' ', ' '.join(buffer)).strip()
        buffer = []
        if len(text) < 15:
            return
        for i in range(0, len(text), max_chars):
            part = text[i:i + max_chars]
            ctx = f' | Mục: {current_heading}' if current_heading else ''
            embed = f'{current_heading}. {part}' if current_heading else part
            payloads.append({
                'text_for_llm': f'[Tài liệu: {doc_name}{ctx}]\n{part}',
                'embed_source': embed,
                'metadata': {
                    'doc_name': doc_name,
                    'section': current_heading or '(Nội dung ngoài bảng)',
                    'param_name': '',
                    'param_value': '',
                    'row_count': 0,
                },
            })

    # Walk the prose blocks (recursively) — skip <div> to avoid double-counting containers.
    # Treat HEADINGS as content too (in many documents the non-table part is only
    # headings/appendices) so they still get indexed & retrieved.
    for el in root.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li']):
        txt = el.get_text(' ', strip=True)
        if not txt:
            continue
        if _looks_like_heading(el, txt):
            _flush()
            current_heading = txt
            buffer.append(txt)  # the heading is also content of the node
        else:
            buffer.append(txt)
            if sum(len(b) for b in buffer) >= max_chars:
                _flush()
    _flush()
    return payloads


def chunk_html_table(
    html_content: str,
    chunk_size: int = 1,
    header_rows_count: int = 2,
) -> List[str]:
    """
    Split table HTML into a list of mini-table HTML chunks for the audit pipeline.

    Each chunk looks like:
        <!-- Mục: <hierarchy name> -->   (if there was a preceding section-header row)
        <table>
            <header row(s)>
            <chunk_size data rows>
        </table>

    Improvements over the old version:
    - Auto-counts header rows from <thead>/<tbody>; header_rows_count is only a fallback
      when the table has no <thead> — fixes the Phụ lục 1 bug (3-row header truncated to 2).
    - A colspan row (hierarchy heading "1.1 Van xả áp", "Bộ công cụ dụng cụ"…) does not
      create its own chunk but is injected into the <!-- Mục: --> comment of the
      following chunks — the LLM still has hierarchy context without an extra LLM call.
    - Wrapper tables (tbody containing only a nested table) are skipped; the real inner
      data table (Phụ lục 2) is processed directly — neither duplicated nor missed.
    - A table nested inside a real (non-wrapper) data table is skipped.

    Args:
        html_content: the entire document HTML
        chunk_size: number of actual data rows per chunk
        header_rows_count: fallback header-row count when the table has no <thead>
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    chunks: List[str] = []

    for table in soup.find_all('table'):
        parent = table.find_parent('table')
        if parent is not None:
            # Table nested inside another table:
            # - If the parent is a wrapper → this is the real data table → process it
            # - If the parent is a data table → this is an inline nested table → skip it
            if not _is_wrapper_table(parent):
                continue
        else:
            # Top-level table that only contains a nested table → skip
            if _is_wrapper_table(table):
                continue

        header_rows, data_rows = _split_header_data(table, header_rows_count)
        if not header_rows or not data_rows:
            continue

        total_cols = _count_cols(header_rows[0])
        header_html = ''.join(str(r) for r in header_rows)

        # Section hierarchy stack: keep the parent→child PATH (e.g. "1 Bộ công cụ dụng cụ >
        # 1.1 Van xả áp") so that asking for a PARENT section name still retrieves its children.
        section_stack: List[Tuple[int, str]] = []
        batch: List[Tag] = []

        def _path() -> str:
            return ' > '.join(t for _, t in section_stack)

        for row in data_rows:
            if _is_section_header(row, total_cols):
                if batch:
                    chunks.append(_make_chunk(header_html, batch, _path()))
                    batch = []
                text = row.get_text(separator=' ', strip=True)
                depth = _section_depth(text)
                # Open a new section at depth `depth`: pop same-level/deeper sections off the stack
                while section_stack and section_stack[-1][0] >= depth:
                    section_stack.pop()
                section_stack.append((depth, text))
            else:
                batch.append(row)
                if len(batch) >= chunk_size:
                    chunks.append(_make_chunk(header_html, batch, _path()))
                    batch = []

        if batch:
            chunks.append(_make_chunk(header_html, batch, _path()))

    # Fallback: no table with a valid structure was found
    if not chunks:
        return [html_content[i:i + 4000] for i in range(0, len(html_content), 4000)]
    return chunks


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

# Leading number of a hierarchy heading: "1", "1.1", "1.1.3" → depth = number of parts.
_RE_SECTION_NUM = re.compile(r'^\s*(\d+(?:\.\d+)*)')


def _section_depth(text: str) -> int:
    """Hierarchy depth of a section-heading line from its leading number (default 1)."""
    m = _RE_SECTION_NUM.match(text or '')
    if not m:
        return 1  # no number → treat as a top-level section
    return m.group(1).count('.') + 1


def _is_wrapper_table(table: Tag) -> bool:
    """
    Return True if the table is merely a wrapper around another table.
    Heuristic: ALL direct <tr> of the tbody contain a nested <table>.
    Example: the Phụ lục 2 outer table.
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
    """Split header rows and data rows from a <table> element."""
    thead = table.find('thead')
    tbody = table.find('tbody')

    if thead and tbody:
        # Full structure: use thead and tbody directly
        return (
            thead.find_all('tr', recursive=False),
            tbody.find_all('tr', recursive=False),
        )

    if thead:
        # Has thead but no tbody: data rows are all tr not belonging to thead
        header_rows = thead.find_all('tr', recursive=False)
        header_ids = {id(r) for r in header_rows}
        data_rows = [r for r in table.find_all('tr') if id(r) not in header_ids]
        return header_rows, data_rows

    # No thead/tbody: take all tr, split by fallback_header_count
    all_rows = table.find_all('tr')
    if len(all_rows) <= fallback_header_count:
        return [], []
    return all_rows[:fallback_header_count], all_rows[fallback_header_count:]


def _count_cols(row: Tag) -> int:
    """Count the total number of columns (accounting for colspan) of a row."""
    return sum(
        int(c.get('colspan', 1))
        for c in row.find_all(['td', 'th'], recursive=False)
    )


def _is_section_header(row: Tag, total_cols: int) -> bool:
    """
    Return True if the row is a hierarchy heading row (large colspan, few real cells).
    Example: <tr><td>1.1</td><td colspan="5">Van xả áp</td></tr>
    """
    cells = row.find_all(['td', 'th'], recursive=False)
    if not cells:
        return True  # empty row
    span = sum(int(c.get('colspan', 1)) for c in cells)
    # Hierarchy heading: at most 2 cells, total colspan covering >= 2/3 of all columns
    return len(cells) <= 2 and span >= max(total_cols * 2 // 3, 2)


def _make_chunk(header_html: str, rows: List[Tag], section: str) -> str:
    """Build the HTML string for one chunk: context comment + mini-table."""
    rows_html = ''.join(str(r) for r in rows)
    ctx = f'<!-- Mục: {section} -->\n' if section else ''
    return f'{ctx}<table>{header_html}{rows_html}</table>'
