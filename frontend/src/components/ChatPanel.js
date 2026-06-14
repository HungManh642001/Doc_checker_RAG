import React, { useState, useRef, useEffect, useCallback } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './ChatPanel.css';

/**
 * ChatPanel — floating Q&A widget inside DocumentPreview.
 *
 * Purpose: lets the user look up information from PREVIOUSLY approved YCKT (uploaded
 * with the session). Answers come with "citation chips" pointing back to the source
 * (document · section).
 *
 * Props:
 *   - sessionId: the audit session id (required).
 */

// Suggested questions — to explore the kinds of questions available.
const SUGGESTIONS = [
  'Liệt kê các thiết bị/vật liệu có trong các YCKT trước đây.',
  'Cho biết thông tin về "Bộ công cụ dụng cụ" trong các YCKT trước đây.',
  'So sánh thông số Van xả áp của tài liệu này với các YCKT trước đây.',
  'Van xả áp từng được dùng với dải giá trị nào?',
];

function ChatPanel({ sessionId }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([]); // {role, content, citations?, error?}
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const listRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to the bottom on new messages / when the panel opens
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
            <p>👋 Tra cứu thông tin thiết bị/vật liệu từ các YCKT trước đây — và đối
              chiếu với tài liệu đang thẩm định.</p>
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
              {m.role === 'assistant' && !m.error && (
                <div className="chat-role">🤖 Trợ lý</div>
              )}
              {m.role === 'assistant' && !m.error ? (
                <div className="chat-bubble md">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {m.content}
                  </ReactMarkdown>
                </div>
              ) : (
                <div className="chat-bubble">{m.content}</div>
              )}
              {m.role === 'assistant' && m.citations && m.citations.length > 0 && (
                <div className="chat-citations">
                  <span className="cite-label">Nguồn:</span>
                  {m.citations.map((c, j) => (
                    <span
                      key={j}
                      className={`cite-chip ${
                        c.source === 'Tài liệu đang xét' ? 'src-b' : 'src-a'
                      }`}
                      title={`${c.source} · ${c.doc_name}${
                        c.section ? ' · Mục: ' + c.section : ''
                      }`}
                    >
                      {c.source === 'Tài liệu đang xét' ? '📝' : '📄'} {c.doc_name}
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
