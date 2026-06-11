import React, { useState, useRef, useEffect, useCallback } from 'react';
import './ChatPanel.css';

/**
 * ChatPanel — widget hỏi-đáp nổi trong DocumentPreview.
 *
 * Người thẩm định hỏi xem một thông số kỹ thuật đã từng xuất hiện trong các YCKT
 * trước đây chưa, giá trị bao nhiêu, có tham khảo được cho tài liệu mới không.
 * Câu trả lời kèm "citation chips" trỏ về nguồn (tài liệu · mục · giá trị).
 *
 * Props:
 *   - sessionId: id phiên thẩm định (bắt buộc).
 *   - prefill:   {question, focusParam} — câu hỏi điền sẵn (dùng cho bước 4
 *                "Hỏi về thông số này"). Tuỳ chọn.
 *   - onConsumePrefill: callback báo đã dùng xong prefill (để cha xoá state).
 */
function ChatPanel({ sessionId, prefill, onConsumePrefill }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // {role, content, citations?, error?}
  const [input, setInput] = useState('');
  const [focusParam, setFocusParam] = useState(null);
  const [sending, setSending] = useState(false);
  const listRef = useRef(null);
  const inputRef = useRef(null);

  // Tự cuộn xuống cuối khi có tin nhắn mới / mở panel
  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, open]);

  // Nhận câu hỏi điền sẵn từ cha (mở panel, điền input, ghim focusParam)
  useEffect(() => {
    if (!prefill) return;
    setOpen(true);
    if (prefill.question) setInput(prefill.question);
    if (prefill.focusParam) setFocusParam(prefill.focusParam);
    if (inputRef.current) inputRef.current.focus();
    onConsumePrefill?.();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [prefill]);

  const send = useCallback(async () => {
    const q = input.trim();
    if (!q || sending) return;

    const history = messages
      .filter((m) => !m.error)
      .map(({ role, content }) => ({ role, content }));
    const currentFocus = focusParam;

    setMessages((prev) => [...prev, { role: 'user', content: q }]);
    setInput('');
    setSending(true);

    try {
      const res = await fetch(`/api/session/${sessionId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, history, focusParam: currentFocus }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Lỗi hỏi đáp');
      }
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: data.answer || '(Không có nội dung trả lời.)',
          citations: data.citations || [],
        },
      ]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `⚠️ ${e.message}`, error: true },
      ]);
    } finally {
      setSending(false);
      setFocusParam(null); // focus chỉ áp dụng cho 1 câu hỏi
    }
  }, [input, sending, messages, focusParam, sessionId]);

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  if (!open) {
    return (
      <button
        className="chat-fab"
        onClick={() => setOpen(true)}
        title="Hỏi đáp về thông số kỹ thuật"
      >
        💬 Hỏi đáp
      </button>
    );
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span className="chat-title">💬 Hỏi đáp thông số kỹ thuật</span>
        <button className="chat-close" onClick={() => setOpen(false)} title="Thu gọn">
          ✕
        </button>
      </div>

      <div className="chat-messages" ref={listRef}>
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p>👋 Hỏi xem một thông số đã từng dùng trong các YCKT trước đây chưa.</p>
            <p className="chat-empty-hint">
              Ví dụ: <em>"Áp suất van xả áp đã từng dùng giá trị nào?"</em>
            </p>
          </div>
        ) : (
          messages.map((m, i) => (
            <div key={i} className={`chat-msg ${m.role} ${m.error ? 'error' : ''}`}>
              <div className="chat-bubble">{m.content}</div>
              {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
                <div className="chat-citations">
                  {m.citations.map((c, j) => (
                    <span
                      key={j}
                      className={`cite-chip ${
                        c.source === 'YCKT trước đây' ? 'src-a' : 'src-b'
                      }`}
                      title={`${c.source} · ${c.doc_name}${
                        c.section ? ' · Mục: ' + c.section : ''
                      }${c.param_value ? ' · Giá trị: ' + c.param_value : ''}`}
                    >
                      📄 {c.doc_name}
                      {c.section ? ` · ${c.section}` : ''}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
        {sending && <div className="chat-typing">Đang soạn câu trả lời…</div>}
      </div>

      {focusParam && (
        <div className="chat-focus" title={focusParam}>
          🎯 Đang hỏi về: <strong>{focusParam}</strong>
          <button className="chat-focus-clear" onClick={() => setFocusParam(null)}>
            ✕
          </button>
        </div>
      )}

      <div className="chat-input-row">
        <textarea
          ref={inputRef}
          className="chat-input"
          value={input}
          placeholder="Nhập câu hỏi… (Enter để gửi, Shift+Enter xuống dòng)"
          rows={2}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={sending}
        />
        <button
          className="chat-send"
          onClick={send}
          disabled={sending || !input.trim()}
        >
          {sending ? '…' : 'Gửi'}
        </button>
      </div>
    </div>
  );
}

export default ChatPanel;
