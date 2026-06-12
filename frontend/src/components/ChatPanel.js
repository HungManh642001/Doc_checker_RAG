import React, { useState, useRef, useEffect, useCallback } from 'react';
import './ChatPanel.css';

/**
 * ChatPanel — widget hỏi-đáp nổi trong DocumentPreview.
 *
 * Mục đích: người dùng tra cứu thông tin từ các YCKT đã duyệt TRƯỚC ĐÂY (upload
 * kèm session). Câu trả lời kèm "citation chips" trỏ về nguồn (tài liệu · mục).
 *
 * Props:
 *   - sessionId: id phiên thẩm định (bắt buộc).
 */

// Câu hỏi gợi ý — khám phá các loại câu hỏi tra cứu YCKT trước đây.
const SUGGESTIONS = [
  'Liệt kê các thiết bị/vật liệu có trong các YCKT trước đây.',
  'Van xả áp từng được dùng với những thông số và giá trị nào?',
  'Tài liệu YCKT nào có thiết bị này?',
  'Các YCKT trước đây dùng dải giá trị nào cho thông số này?',
];

function ChatPanel({ sessionId }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // {role, content, citations?, error?}
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const listRef = useRef(null);
  const inputRef = useRef(null);

  // Tự cuộn xuống cuối khi có tin nhắn mới / mở panel
  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [messages, open]);

  const send = useCallback(async () => {
    const q = input.trim();
    if (!q || sending) return;

    const history = messages
      .filter((m) => !m.error)
      .map(({ role, content }) => ({ role, content }));

    setMessages((prev) => [...prev, { role: 'user', content: q }]);
    setInput('');
    setSending(true);

    try {
      const res = await fetch(`/api/session/${sessionId}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q, history }),
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
    }
  }, [input, sending, messages, sessionId]);

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
        title="Hỏi đáp thông tin từ các YCKT trước đây"
      >
        💬 Hỏi đáp YCKT trước đây
      </button>
    );
  }

  return (
    <div className="chat-panel">
      <div className="chat-header">
        <span className="chat-title">💬 Hỏi đáp YCKT trước đây</span>
        <button className="chat-close" onClick={() => setOpen(false)} title="Thu gọn">
          ✕
        </button>
      </div>

      <div className="chat-messages" ref={listRef}>
        {messages.length === 0 ? (
          <div className="chat-empty">
            <p>👋 Tra cứu thông tin thiết bị/vật liệu từ các YCKT đã duyệt trước đây.</p>
            <p className="chat-empty-hint">
              Mỗi mục trong bảng (vd "1.1 Van xả áp") là một thiết bị/vật liệu. Bấm
              một câu hỏi gợi ý để bắt đầu:
            </p>
            <div className="chat-suggestions">
              {SUGGESTIONS.map((s, i) => (
                <button
                  key={i}
                  className="chat-suggestion"
                  onClick={() => {
                    setInput(s);
                    inputRef.current?.focus();
                  }}
                >
                  {s}
                </button>
              ))}
            </div>
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
                      className="cite-chip src-a"
                      title={`${c.doc_name}${
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
