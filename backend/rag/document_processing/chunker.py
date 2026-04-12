from bs4 import BeautifulSoup
import time

def chunk_html_table(html_content, chunk_size=5, header_rows_count=2):
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')

    if not tables:
        return [html_content[i:i+4000] for i in range(0, len(html_content), 4000)]
    
    chunks = []
    for table_idx, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) <= header_rows_count:
            continue
    
        headers = rows[:header_rows_count]
        data_rows = rows[header_rows_count:]

        header_html = "".join([str(h) for h in headers])

        for i in range(0, len(data_rows), chunk_size):
            batch = data_rows[i:i+chunk_size]
            batch_html = "".join([str(r) for r in batch])

            mini_table_html = f"<table>{header_html}{batch_html}</table>"
            chunks.append(mini_table_html)
    return chunks