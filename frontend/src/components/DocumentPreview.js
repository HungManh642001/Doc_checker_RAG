import React, { useEffect, useRef, useState } from 'react';
import { toast } from 'react-toastify';
import './DocumentPreview.css';
import DOMPurify from 'dompurify';
import { fetchAndSave } from '../utils/download';
import ChatPanel from './ChatPanel';

const DOCX_MIME =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

/**
 * DocumentPreview — renders the original document (HTML) + HIGHLIGHTS the error content
 * (matched by original_text). The user can:
 *   - Click a highlighted region to view the error details
 *   - Edit the suggested text then "Accept & update" → updates the text IMMEDIATELY
 *   - Download the corrected document (choose where to save)
 *
 * Props: sessionId, errors
 */
function DocumentPreview({ sessionId, errors }) {
  const [html, setHtml] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [accepted, setAccepted] = useState({}); // errorId -> fixedValue
  const [downloading, setDownloading] = useState(false);
  const containerRef = useRef(null);

  // Load the document HTML
  useEffect(() => {
    let active = true;
    setLoading(true);
    fetch(`/api/session/${sessionId}/document`)
      .then((r) => r.json())
      .then((d) => {
        if (active) {
          setHtml(d.html || '');
          setLoading(false);
        }
      })
      .catch(() => {
        if (active) {
          setHtml('');
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [sessionId]);

  // Render HTML + highlight (runs once when html is available). Store the verbatim text in data-original.
  useEffect(() => {
    const container = containerRef.current;
    if (html == null || !container) return;

    // Sanitize the HTML from the backend (mammoth-converted from the user-uploaded DOCX)
    // before injecting it into the DOM, to prevent stored XSS from a malicious file.
    container.innerHTML = DOMPurify.sanitize(html);

    const targets = errors
      .map((e) => ({
        id: e.id,
        text: (e.original_text || '').trim(),
        severity: e.severity || 'error',
      }))
      .filter((t) => t.text.length >= 2)
      .sort((a, b) => b.text.length - a.text.length);

    targets.forEach((t) => highlightInNode(container, t));

    container.querySelectorAll('mark.err-mark').forEach((m) => {
      m.style.cursor = 'pointer';
      m.onclick = () => {
        const id = m.getAttribute('data-eid');
        const err = errors.find((e) => e.id === id);
        if (err) selectError(err);
        container.querySelectorAll('mark.err-mark.active').forEach((x) =>
          x.classList.remove('active')
        );
        container
          .querySelectorAll(`mark.err-mark[data-eid="${cssEscape(id)}"]`)
          .forEach((x) => x.classList.add('active'));
      };
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [html, errors]);

  const selectError = (err) => {
    setSelected(err);
    setEditValue(accepted[err.id] != null ? accepted[err.id] : err.suggestion || '');
  };

  const updateMarks = (errorId, text, fixed) => {
    const container = containerRef.current;
    if (!container) return;
    container
      .querySelectorAll(`mark.err-mark[data-eid="${cssEscape(errorId)}"]`)
      .forEach((m) => {
        m.textContent = text;
        m.classList.toggle('fixed', fixed);
      });
  };

  const acceptCurrent = () => {
    if (!selected) return;
    const value = (editValue || '').trim();
    if (!value) {
      toast.warning('Nội dung đề xuất đang trống.');
      return;
    }
    setAccepted((prev) => ({ ...prev, [selected.id]: value }));
    updateMarks(selected.id, value, true); // update immediately in the text
    toast.success('✓ Đã cập nhật trong văn bản', { autoClose: 1500 });
  };

  const undoCurrent = () => {
    if (!selected) return;
    const container = containerRef.current;
    const mark = container?.querySelector(
      `mark.err-mark[data-eid="${cssEscape(selected.id)}"]`
    );
    const original = mark?.getAttribute('data-original') ?? selected.original_text;
    updateMarks(selected.id, original, false);
    setAccepted((prev) => {
      const next = { ...prev };
      delete next[selected.id];
      return next;
    });
    setEditValue(selected.suggestion || '');
  };

  const acceptedCount = Object.keys(accepted).length;

  const downloadCorrected = async () => {
    if (acceptedCount === 0) return;
    setDownloading(true);
    try {
      const updates = Object.entries(accepted).map(([errorId, fixedValue]) => ({
        errorId,
        action: 'accept',
        fixedValue,
      }));
      const res = await fetch(`/api/session/${sessionId}/apply-suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ updates }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Ghi file thất bại');
      }
      const saved = await fetchAndSave(
        `/api/session/${sessionId}/download`,
        'tai_lieu_da_sua.docx',
        DOCX_MIME
      );
      if (saved) {
        toast.success(`✓ Đã ghi ${data.appliedCount || 0} sửa chữa & tải file.`, {
          autoClose: 3000,
        });
      }
    } catch (e) {
      toast.error(`Không tải được file: ${e.message}`, { autoClose: 4000 });
    } finally {
      setDownloading(false);
    }
  };

  const matchedCount = () => {
    const c = containerRef.current;
    if (!c) return 0;
    const ids = new Set();
    c.querySelectorAll('mark.err-mark').forEach((m) => ids.add(m.getAttribute('data-eid')));
    return ids.size;
  };

  const isAccepted = selected && accepted[selected.id] != null;
  const isWarning = selected && selected.severity === 'warning';

  return (
    <div className="doc-preview">
      <div className="doc-preview-main">
        <div className="doc-preview-bar">
          <div className="legend-group">
            <span className="legend-chip sev-error">Nội dung lỗi</span>
            <span className="legend-chip sev-warning">Cảnh báo nội dung</span>
            <span className="legend-chip fixed">Đã sửa</span>
          </div>
          <button
            className="btn-download-doc"
            onClick={downloadCorrected}
            disabled={acceptedCount === 0 || downloading}
            title={acceptedCount === 0 ? 'Hãy chấp nhận ít nhất một sửa chữa' : ''}
          >
            {downloading ? '⏳ Đang tạo file…' : `💾 Tải tài liệu đã sửa (${acceptedCount})`}
          </button>
        </div>

        {loading ? (
          <div className="doc-preview-loading">⏳ Đang tải tài liệu…</div>
        ) : html ? (
          <div className="doc-preview-scroll">
            <div ref={containerRef} className="doc-preview-content" />
          </div>
        ) : (
          <div className="doc-preview-empty">
            Không hiển thị được tài liệu (không tạo được HTML preview).
          </div>
        )}
      </div>

      <div className="doc-preview-sidebar">
        {selected ? (
          <div className="dp-error-detail">
            <h3>{isWarning ? '⚠️ Cảnh báo nội dung' : '📋 Chi tiết lỗi'}</h3>
            <div className="dp-section">
              <strong>📌 Nội dung gốc</strong>
              <code>{selected.original_text}</code>
            </div>
            <div className="dp-section">
              <strong>{isWarning ? '⚠️ Đối chiếu phát hiện' : '🔴 Lỗi phát hiện'}</strong>
              {(selected.danh_sach_cac_loi || []).map((e, i) => (
                <div key={i} className={isWarning ? 'dp-suberr warn' : 'dp-suberr'}>
                  <span className="dp-type">{e.error_type}</span>
                  <p>{e.reasoning}</p>
                </div>
              ))}
            </div>

            {/* Content warning: reference only, NO automatic fix. Formatting error:
                has a suggestion card to fix & apply to the text. */}
            {!isWarning && (
              <div className="dp-suggest-card">
                <div className="dp-suggest-head">💡 Đề xuất sửa</div>
                <textarea
                  className="dp-suggest-input"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  rows={3}
                />
                <div className="dp-suggest-actions">
                  {isAccepted ? (
                    <>
                      <span className="dp-applied">✓ Đã áp dụng vào văn bản</span>
                      <button className="dp-btn ghost" onClick={undoCurrent}>
                        ↩︎ Hoàn tác
                      </button>
                      <button className="dp-btn primary" onClick={acceptCurrent}>
                        ↻ Cập nhật lại
                      </button>
                    </>
                  ) : (
                    <button className="dp-btn primary" onClick={acceptCurrent}>
                      ✓ Chấp nhận &amp; cập nhật
                    </button>
                  )}
                </div>
              </div>
            )}

            <div className="dp-section">
              <strong>
                {isWarning ? '📖 Đối chiếu YCKT trước đây' : '📖 Tham chiếu sở cứ'}
              </strong>
              <p className="dp-ref-loc">{selected.reference_location}</p>
              <p className="dp-ref-quote">{selected.reference_quote}</p>
            </div>
          </div>
        ) : (
          <div className="dp-no-selection">
            <p>👆 Bấm vào một vùng được tô màu (đỏ = lỗi, vàng = cảnh báo nội dung)
              để xem chi tiết.</p>
            <p className="dp-hint">
              Đã đánh dấu <strong>{matchedCount()}</strong>/{errors.length} mục trong tài liệu.
              {matchedCount() < errors.length &&
                ' (Một số mục nằm trong nội dung không khớp chính xác nên không tô được.)'}
            </p>
            <p className="dp-hint">
              💬 Cần tra cứu thông tin thiết bị từ các YCKT trước đây? Mở{' '}
              <strong>Hỏi đáp YCKT trước đây</strong> ở góc phải dưới.
            </p>
          </div>
        )}
      </div>

      <ChatPanel sessionId={sessionId} />
    </div>
  );
}

// --- Helpers ---

function highlightInNode(root, target) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue || !node.nodeValue.includes(target.text)) {
        return NodeFilter.FILTER_REJECT;
      }
      if (node.parentElement && node.parentElement.closest('mark.err-mark')) {
        return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    },
  });

  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);

  nodes.forEach((node) => {
    const idx = node.nodeValue.indexOf(target.text);
    if (idx === -1) return;
    const after = node.splitText(idx);
    after.splitText(target.text.length);
    const mark = document.createElement('mark');
    mark.className = `err-mark sev-${target.severity}`;
    mark.setAttribute('data-eid', target.id);
    mark.setAttribute('data-original', after.nodeValue); // store for undo
    mark.textContent = after.nodeValue;
    after.parentNode.replaceChild(mark, after);
  });
}

function cssEscape(s) {
  if (window.CSS && window.CSS.escape) return window.CSS.escape(s);
  return (s || '').replace(/["\\]/g, '\\$&');
}

export default DocumentPreview;
