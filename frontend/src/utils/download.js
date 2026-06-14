/**
 * File download utilities: prefer the "Save As" dialog (File System Access API) so the
 * user can choose where to save; fall back to a regular download if the browser does
 * not support it.
 */

/**
 * Save a Blob to a file. Returns true if saved, false if the user cancels.
 */
export async function saveBlob(blob, suggestedName, mimeType) {
  // Chromium: let the user choose the save location
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
      if (err && err.name === 'AbortError') return false; // user cancelled
      // other errors → fall back to a regular download
    }
  }

  // Fallback: an <a download> element (the browser saves into the Downloads folder)
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
 * GET a URL and save the result to a file (via saveBlob). Throws if the response is not OK.
 */
export async function fetchAndSave(url, suggestedName, mimeType, fetchOptions) {
  const res = await fetch(url, fetchOptions);
  if (!res.ok) {
    let msg = `HTTP ${res.status}`;
    try {
      const data = await res.json();
      msg = data.error || msg;
    } catch (e) {
      /* response is not JSON */
    }
    throw new Error(msg);
  }
  const blob = await res.blob();
  return saveBlob(blob, suggestedName, mimeType);
}
