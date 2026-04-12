import React, { useState, useMemo } from 'react';
import { toast } from 'react-toastify';
import './ErrorViewer.css';


function ErrorViewer({ errors, sessionId, onApplySuggestions, onReset, loading, onPreview, onReupload }) {
  const [selectedErrors, setSelectedErrors] = useState(new Set());
  const [filterSeverity, setFilterSeverity] = useState('all');
  const [expandedErrorId, setExpandedErrorId] = useState(null);
  const [editingErrorId, setEditingErrorId] = useState(null);
  const [editedText, setEditedText] = useState('');

  const filteredErrors = useMemo(() => {
    return errors.filter(error => {
      const severityMatch = filterSeverity === 'all' || error.severity === filterSeverity;
      return severityMatch;
    });
  }, [errors, filterSeverity]);

  const errorStats = useMemo(() => {
    const stats = {
      total: errors.length,
      error: 0,
      warning: 0,
      info: 0
    };
    
    errors.forEach(err => {
      stats[err.severity] = (stats[err.severity] || 0) + 1;
    });
    
    return stats;
  }, [errors]);

  const toggleError = (errorId) => {
    const newSelected = new Set(selectedErrors);
    if (newSelected.has(errorId)) {
      newSelected.delete(errorId);
    } else {
      newSelected.add(errorId);
    }
    setSelectedErrors(newSelected);
  };

  const toggleAllErrors = () => {
    if (selectedErrors.size === filteredErrors.length) {
      setSelectedErrors(new Set());
    } else {
      setSelectedErrors(new Set(filteredErrors.map(e => e.id)));
    }
  };

  const startEdit = (error) => {
    setEditingErrorId(error.id);
    setEditedText(error.suggestion || '');
  };

  const cancelEdit = () => {
    setEditingErrorId(null);
    setEditedText('');
  };

  const applyEdit = (errorId) => {
    setEditingErrorId(null);
    const errorIndex = errors.findIndex(e => e.id === errorId);
    if (errorIndex !== -1) {
      errors[errorIndex].suggestion = editedText;
      toast.success('Đã cập nhật đề xuất');
    }
  };

  const handleApplySuggestions = () => {
    if (selectedErrors.size === 0) {
      toast.warning('Vui lòng chọn ít nhất một lỗi để sửa chữa');
      return;
    }

    const acceptedErrors = Array.from(selectedErrors)
      .map(errorId => {
        const error = errors.find(e => e.id === errorId);
        return {
          elementId: error.elementId,
          newText: error.suggestion
        };
      });

    onApplySuggestions(acceptedErrors);
  };

  const getSeverityColor = (severity) => {
    const colors = {
      'error': '#e74c3c',
      'warning': '#f39c12',
      'info': '#3498db'
    };
    return colors[severity] || '#95a5a6';
  };

  const getSeverityLabel = (severity) => {
    const labels = {
      'error': '❌ LỖI',
      'warning': '⚠️  CẢNH BÁO',
      'info': 'ℹ️ THÔNG TIN'
    };
    return labels[severity] || severity;
  };

  const getErrorTypeLabel = (errorType) => {
    const labels = {
      'vi_pham_ky_hieu_don_vi': 'Ký hiệu đơn vị sai',
      'vi_pham_ky_hieu_don_vi_khac': 'Ký hiệu không tiêu chuẩn',
      'thieu_don_vi_do': 'Thiếu đơn vị đo',
      'sai_dau_thap_phan': 'Sai dấu thập phân',
      'vi_pham_don_vi_tieu_chuan': 'Đơn vị không tiêu chuẩn',
      'vi_pham_trinh_bay_don_vi_do': 'Trình bày đơn vị sai'
    };
    return labels[errorType] || errorType;
  };

  return (
    <div className="error-viewer">
      <div className="error-header">
        <div className="header-content">
          <h1>📋 KẾT QUẢ PHÂN TÍCH TÀI LIỆU</h1>
          <p className="subtitle">Phân tích theo kiến trúc RAG - Kiểm tra quy định & pháp lệ</p>
          <div className="stats">
            <span className="stat-item total">
              📊 Tổng: <strong>{errorStats.total}</strong>
            </span>
            <span className="stat-item error" style={{ color: getSeverityColor('error') }}>
              ❌ Lỗi: <strong>{errorStats.error}</strong>
            </span>
            <span className="stat-item warning" style={{ color: getSeverityColor('warning') }}>
              ⚠️ Cảnh báo: <strong>{errorStats.warning}</strong>
            </span>
            <span className="stat-item info" style={{ color: getSeverityColor('info') }}>
              ℹ️ Thông tin: <strong>{errorStats.info}</strong>
            </span>
          </div>
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-group">
          <label>🔍 Lọc theo mức độ:</label>
          <select value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value)}>
            <option value="all">Tất cả</option>
            <option value="error">❌ Lỗi</option>
            <option value="warning">⚠️ Cảnh báo</option>
            <option value="info">ℹ️ Thông tin</option>
          </select>
        </div>

        <div className="filter-group">
          <label>
            <input
              type="checkbox"
              checked={selectedErrors.size === filteredErrors.length && filteredErrors.length > 0}
              onChange={toggleAllErrors}
            />
            ☑️ Chọn tất cả
          </label>
        </div>
      </div>

      <div className="error-list">
        {filteredErrors.length === 0 ? (
          <div className="no-errors">
            <p>✅ Không phát hiện lỗi nào! Tài liệu tuân thủ quy định.</p>
          </div>
        ) : (
          filteredErrors.map((error, index) => (
            <div key={error.id} className="error-item" style={{
              borderLeftColor: getSeverityColor(error.severity)
            }}>
              <div className="error-item-header">
                <div className="checkbox-section">
                  <input
                    type="checkbox"
                    checked={selectedErrors.has(error.id)}
                    onChange={() => toggleError(error.id)}
                    id={`error-${error.id}`}
                  />
                </div>

                <div className="error-main-info">
                  <div className="error-title-row">
                    <label htmlFor={`error-${error.id}`}>
                      <span className="severity-badge" style={{backgroundColor: getSeverityColor(error.severity)}}>
                        {getSeverityLabel(error.severity)}
                      </span>
                    </label>
                  </div>
                  
                  <div className="original-text-box">
                    <strong>📌 Nội dung gốc:</strong>
                    <code className="original-text">{error.original_text}</code>
                  </div>

                  <div className="error-list-container">
                    <strong>🔴 Danh sách lỗi phát hiện:</strong>
                    <div className="error-details-list">
                      {error.danh_sach_cac_loi && error.danh_sach_cac_loi.map((err, idx) => (
                        <div key={idx} className="error-detail-item">
                          <div className="error-type-badge">
                            {getErrorTypeLabel(err.error_type)}
                          </div>
                          <div className="error-reasoning">
                            <p><strong>Giải thích:</strong> {err.reasoning}</p>
                            {err.reference && (
                              <p className="reference-text">
                                <strong>Tham chiếu:</strong> {err.reference}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <button
                  className="expand-btn"
                  onClick={() => setExpandedErrorId(expandedErrorId === error.id ? null : error.id)}
                >
                  {expandedErrorId === error.id ? '▼' : '▶'} Chi tiết
                </button>
              </div>

              {expandedErrorId === error.id && (
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
                          <button
                            className="btn btn-success"
                            onClick={() => applyEdit(error.id)}
                          >
                            ✓ Lưu
                          </button>
                          <button
                            className="btn btn-cancel"
                            onClick={cancelEdit}
                          >
                            ✕ Hủy
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="suggestion-display">
                        <code>{error.suggestion}</code>
                        <button
                          className="btn btn-small"
                          onClick={() => startEdit(error)}
                        >
                          ✏️ Chỉnh sửa
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="reference-section">
                    <div className="reference-box">
                      <strong>📖 Tham chiếu quy định:</strong>
                      <p className="reference-location">{error.reference_location}</p>
                      <p className="reference-quote">{error.reference_quote}</p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="action-bar">
        <button
          className="btn btn-primary"
          onClick={handleApplySuggestions}
          disabled={loading || selectedErrors.size === 0}
        >
          {loading ? '⏳ Đang xử lý...' : `✓ Chấp nhận ${selectedErrors.size} đề xuất`}
        </button>
        <button
          className="btn btn-info"
          onClick={() => onReupload && onReupload()}
          disabled={loading}
        >
          🔁 Tái Thẩm Định
        </button>
        <button
          className="btn btn-secondary"
          onClick={onReset}
          disabled={loading}
        >
          ← Quay lại
        </button>
      </div>
    </div>
  );
}

export default ErrorViewer;
