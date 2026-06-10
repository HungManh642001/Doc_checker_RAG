import React, { useState, useMemo } from 'react';
import { toast } from 'react-toastify';
import './ErrorViewer.css';

/**
 * ErrorViewer — hiển thị kết quả thẩm định và cho phép người dùng
 * chấp nhận / từ chối / chỉnh sửa từng đề xuất sửa lỗi.
 *
 * Props:
 *   errors: danh sách lỗi từ backend
 *   onApplySuggestions(updates): áp dụng các sửa chữa.
 *       updates = [{ errorId, action: 'accept'|'reject', fixedValue }]
 *   onReset(): thẩm định tài liệu khác
 *   loading: đang ghi file
 */
function ErrorViewer({ errors, onApplySuggestions, onReset, loading }) {
  const [expandedErrorId, setExpandedErrorId] = useState(null);
  // statusMap[errorId] = { action: 'accept'|'reject', value: <custom suggestion> }
  const [statusMap, setStatusMap] = useState({});
  const [editingErrorId, setEditingErrorId] = useState(null);
  const [editedText, setEditedText] = useState('');

  const getStatus = (id) => statusMap[id]?.action || 'accept';

  const setStatus = (id, action) => {
    setStatusMap((prev) => ({
      ...prev,
      [id]: { ...prev[id], action },
    }));
  };

  const filteredErrors = errors;

  const stats = useMemo(() => {
    const s = { total: errors.length, accepted: 0, rejected: 0 };
    errors.forEach((e) => {
      if (getStatus(e.id) === 'reject') s.rejected += 1;
      else s.accepted += 1;
    });
    return s;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [errors, statusMap]);

  const startEdit = (error) => {
    setEditingErrorId(error.id);
    setEditedText(statusMap[error.id]?.value ?? error.suggestion ?? '');
  };

  const cancelEdit = () => {
    setEditingErrorId(null);
    setEditedText('');
  };

  const saveEdit = (errorId) => {
    setStatusMap((prev) => ({
      ...prev,
      [errorId]: { action: 'accept', value: editedText },
    }));
    setEditingErrorId(null);
    toast.success('Đã cập nhật đề xuất');
  };

  const handleApply = () => {
    const updates = errors.map((e) => {
      const st = statusMap[e.id] || {};
      return {
        errorId: e.id,
        action: st.action || 'accept',
        fixedValue: st.value, // undefined nếu không sửa tay
      };
    });

    const acceptedCount = updates.filter((u) => u.action !== 'reject').length;
    if (acceptedCount === 0) {
      toast.warning('Tất cả lỗi đều bị từ chối — không có gì để ghi lại.');
      return;
    }
    onApplySuggestions(updates);
  };

  const getSeverityColor = (severity) =>
    ({ error: '#e74c3c', warning: '#f39c12', info: '#3498db' }[severity] || '#95a5a6');

  const getSeverityLabel = (severity) =>
    ({ error: '❌ LỖI', warning: '⚠️ CẢNH BÁO', info: 'ℹ️ THÔNG TIN' }[severity] || severity);

  return (
    <div className="error-viewer">
      <div className="error-header">
        <div className="header-content">
          <h1>📋 Kết quả thẩm định</h1>
          <p className="subtitle">Đối chiếu quy định &amp; sở cứ theo kiến trúc RAG</p>
          <div className="stats">
            <span className="stat-item total">
              📊 Tổng: <strong>{stats.total}</strong>
            </span>
            <span className="stat-item accepted" style={{ color: '#27ae60' }}>
              ✓ Chấp nhận: <strong>{stats.accepted}</strong>
            </span>
            <span className="stat-item rejected" style={{ color: '#e74c3c' }}>
              ✕ Từ chối: <strong>{stats.rejected}</strong>
            </span>
          </div>
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-hint">
          Mặc định mọi lỗi được <strong>chấp nhận</strong>. Bấm <em>Từ chối</em> với lỗi bạn
          muốn bỏ qua, hoặc <em>Chỉnh sửa</em> để tự nhập giá trị thay thế.
        </div>
      </div>

      <div className="error-list">
        {filteredErrors.length === 0 ? (
          <div className="no-errors">
            <p>✅ Không phát hiện lỗi nào! Tài liệu tuân thủ quy định.</p>
          </div>
        ) : (
          filteredErrors.map((error) => {
            const action = getStatus(error.id);
            const isRejected = action === 'reject';
            const isExpanded = expandedErrorId === error.id;
            const effectiveSuggestion = statusMap[error.id]?.value ?? error.suggestion;
            return (
              <div
                key={error.id}
                className={`error-item ${isRejected ? 'rejected' : ''}`}
                style={{ borderLeftColor: getSeverityColor(error.severity) }}
              >
                <div className="error-item-header">
                  <div className="error-main-info">
                    <div className="error-title-row">
                      <span
                        className="severity-badge"
                        style={{ backgroundColor: getSeverityColor(error.severity) }}
                      >
                        {getSeverityLabel(error.severity)}
                      </span>
                      <span className={`decision-pill ${action}`}>
                        {isRejected ? '✕ Đã từ chối' : '✓ Sẽ áp dụng'}
                      </span>
                    </div>

                    <div className="original-text-box">
                      <strong>📌 Nội dung gốc:</strong>
                      <code className="original-text">{error.original_text}</code>
                    </div>

                    <div className="error-list-container">
                      <strong>🔴 Lỗi phát hiện:</strong>
                      <div className="error-details-list">
                        {(error.danh_sach_cac_loi || []).map((err, idx) => (
                          <div key={idx} className="error-detail-item">
                            <div className="error-type-badge">{err.error_type}</div>
                            <div className="error-reasoning">
                              <p><strong>Giải thích:</strong> {err.reasoning}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  <button
                    className="expand-btn"
                    onClick={() => setExpandedErrorId(isExpanded ? null : error.id)}
                  >
                    {isExpanded ? '▼' : '▶'} Chi tiết
                  </button>
                </div>

                {isExpanded && (
                  <div className="error-expanded-content">
                    <div className="suggestion-section">
                      <strong>💡 Đề xuất sửa chữa:</strong>
                      {editingErrorId === error.id ? (
                        <div className="edit-mode">
                          <textarea
                            value={editedText}
                            onChange={(e) => setEditedText(e.target.value)}
                            className="edit-textarea"
                          />
                          <div className="edit-buttons">
                            <button className="btn btn-success" onClick={() => saveEdit(error.id)}>
                              ✓ Lưu
                            </button>
                            <button className="btn btn-cancel" onClick={cancelEdit}>
                              ✕ Hủy
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="suggestion-display">
                          <code>{effectiveSuggestion}</code>
                          <button className="btn btn-small" onClick={() => startEdit(error)}>
                            ✏️ Chỉnh sửa
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="reference-section">
                      <div className="reference-box">
                        <strong>📖 Tham chiếu sở cứ:</strong>
                        <p className="reference-location">{error.reference_location}</p>
                        <p className="reference-quote">{error.reference_quote}</p>
                      </div>
                    </div>
                  </div>
                )}

                <div className="decision-bar">
                  <button
                    className={`btn-decision accept ${!isRejected ? 'active' : ''}`}
                    onClick={() => setStatus(error.id, 'accept')}
                  >
                    ✓ Chấp nhận
                  </button>
                  <button
                    className={`btn-decision reject ${isRejected ? 'active' : ''}`}
                    onClick={() => setStatus(error.id, 'reject')}
                  >
                    ✕ Từ chối
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      <div className="action-bar">
        <button
          className="btn btn-primary"
          onClick={handleApply}
          disabled={loading || errors.length === 0}
        >
          {loading ? '⏳ Đang ghi file...' : `💾 Ghi lại & tải file đã sửa (${stats.accepted})`}
        </button>
        <button className="btn btn-secondary" onClick={onReset} disabled={loading}>
          ← Thẩm định tài liệu khác
        </button>
      </div>
    </div>
  );
}

export default ErrorViewer;
