/**
 * Tiện ích tải file: ưu tiên hộp thoại "Save As" (File System Access API) để
 * người dùng tự chọn nơi lưu; nếu trình duyệt không hỗ trợ thì fallback sang
 * tải xuống thông thường.
 */

/**
 * Lưu một Blob ra file. Trả về true nếu đã lưu, false nếu người dùng huỷ.
 */
export async function saveBlob(blob, suggestedName, mimeType) {
  // Chromium: cho người dùng chọn vị trí lưu
  if (typeof window !== 'undefined' && window.showSaveFilePicker) {
    try {
      const ext = (suggestedName.split('.').pop() || '').toLowerCase();
      const handle = await window.showSaveFilePicker({
        suggestedName,
        types: mimeType
          ? [{ description: 'Tệp', accept: { [mimeType]: [`.${ext}`] } }]
          : undefined,
      });
      const writable = await handle.createWritable();
      await writable.write(blob);
      await writable.close();
      return true;
    } catch (err) {
      if (err && err.name === 'AbortError') return false; // người dùng huỷ
      // các lỗi khác → fallback tải thường
    }
  }

  // Fallback: thẻ <a download> (trình duyệt tự lưu vào thư mục Downloads)
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = suggestedName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1500);
  return true;
}

/**
 * GET một URL và lưu kết quả ra file (qua saveBlob). Ném lỗi nếu response không OK.
 */
export async function fetchAndSave(url, suggestedName, mimeType, fetchOptions) {
  const res = await fetch(url, fetchOptions);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      msg = data.error || msg;
    } catch (e) {
      /* response không phải JSON */
    }
    throw new Error(msg);
  }
  const blob = await res.blob();
  return saveBlob(blob, suggestedName, mimeType);
}
