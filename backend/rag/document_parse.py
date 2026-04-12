import mammoth

def docx_to_html(docx_path, output):
    with open(docx_path, "rb") as docx_file:
        result = mammoth.convert_to_html(docx_file)
        html_content = result.value

        with open(output, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print("Đã xuất ra HTML.")

file_path = "Mẫu YCKT đầu vào_1.docx"
docx_to_html(file_path, "Mẫu YCKT đầu vào_1.html")
