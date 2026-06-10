import React, { useEffect, useRef, useState } from 'react';
import './DocumentPreview.css';

/**
 * DocumentPreview — hiển thị tài liệu gốc (HTML) và HIGHLIGHT các đoạn nội dung
 * bị lỗi (khớp theo original_text của từng lỗi). Click vào vùng highlight để
 * xem chi tiết lỗi ở bảng bên phải.
 *
 * Props:
 *   sessionId: id phiên (để fetch HTML tài liệu)
 *   errors: danh sách lỗi (dùng original_text để highlight)
 */
const SEVERITY_LABEL = { error: '🔴 Lỗi', warning: '🟡 Cảnh báo', info: '🔵 Thông tin' };

function DocumentPreview({ sessionId, errors }) {
  const [html, setHtml] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);
  const containerRef = useRef(null);

  // Tải HTML tài liệu
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

  // Render HTML + highlight sau khi có dữ liệu
  useEffect(() => {
    const container = containerRef.current;
    if (html == null || !container) return;

    container.innerHTML = html; // reset sạch mỗi lần để tránh wrap chồng

    // Sắp xếp text dài trước để tránh khớp lồng nhau một phần
    const targets = errors
      .map((e) => ({
        id: e.id,
        text: (e.original_text || '').trim(),
        severity: e.severity || 'error',
      }))
      .filter((t) => t.text.length >= 2)
      .sort((a, b) => b.text.length - a.text.length);

    targets.forEach((t) => highlightInNode(container, t));

    // Gắn sự kiện click cho các vùng highlight
    const marks = container.querySelectorAll('mark.err-mark');
    marks.forEach((m) => {
      m.style.cursor = 'pointer';
      m.onclick = () => {
        const id = m.getAttribute('data-eid');
        const err = errors.find((e) => e.id === id);
        if (err) setSelected(err);
        container.querySelectorAll('mark.err-mark.active').forEach((x) =>
          x.classList.remove('active')
        );
        container
          .querySelectorAll(`mark.err-mark[data-eid="${cssEscape(id)}"]`)
          .forEach((x) => x.classList.add('active'));
      };
    });
  }, [html, errors]);

  const matchedCount = () => {
    const c = containerRef.current;
    if (!c) return 0;
    const ids = new Set();
    c.querySelectorAll('mark.err-mark').forEach((m) => ids.add(m.getAttribute('data-eid')));
    return ids.size;
  };

  return (
    <div className="doc-preview">
      <div className="doc-preview-main">
        <div className="doc-preview-legend">
          <span className="legend-chip sev-error">Nội dung lỗi</span>
          <span className="legend-note">
            Vùng được tô là nội dung bị phát hiện lỗi — bấm để xem chi tiết.
          </span>
        </div>
        {loading ? (
          <div className="doc-preview-loading">⏳ Đang tải tài liệu…</div>
        ) : html ? (
          <div ref={containerRef} className="doc-preview-content" />
        ) : (
          <div className="doc-preview-empty">
            Không hiển thị được tài liệu (không tạo được HTML preview).
          </div>
        )}
      </div>

      <div className="doc-preview-sidebar">
        {selected ? (
          <div className="dp-error-detail">
            <h3>📋 Chi tiết lỗi</h3>
            <div className="dp-section">
              <strong>📌 Nội dung gốc</strong>
              <code>{selected.original_text}</code>
            </div>
            <div className="dp-section">
              <strong>🔴 Lỗi phát hiện</strong>
              {(selected.danh_sach_cac_loi || []).map((e, i) => (
                <div key={i} className="dp-suberr">
                  <span className="dp-type">{e.error_type}</span>
                  <p>{e.reasoning}</p>
                </div>
              ))}
            </div>
            <div className="dp-section">
              <strong>💡 Đề xuất sửa</strong>
              <code className="dp-suggestion">{selected.suggestion}</code>
            </div>
            <div className="dp-section">
              <strong>📖 Tham chiếu sở cứ</strong>
              <p className="dp-ref-loc">{selected.reference_location}</p>
              <p className="dp-ref-quote">{selected.reference_quote}</p>
            </div>
          </div>
        ) : (
          <div className="dp-no-selection">
            <p>👆 Bấm vào một vùng được tô màu trong tài liệu để xem chi tiết lỗi.</p>
            <p className="dp-hint">
              Đã đánh dấu <strong>{matchedCount()}</strong>/{errors.length} lỗi trong tài liệu.
              {matchedCount() < errors.length &&
                ' (Một số lỗi nằm trong nội dung không khớp chính xác nên không tô được.)'}
            </p>
          </div>
        )}
      </div>
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
    mark.textContent = after.nodeValue;
    after.parentNode.replaceChild(mark, after);
  });
}

function cssEscape(s) {
  if (window.CSS && window.CSS.escape) return window.CSS.escape(s);
  return (s || '').replace(/["\\]/g, '\\$&');
}

export default DocumentPreview;
