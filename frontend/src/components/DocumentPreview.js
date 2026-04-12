import React, { useState, useMemo } from 'react';
import './DocumentPreview.css';

function DocumentPreview({ content, errors, sessionId, onClose, onErrorStatusChange }) {
  const [selectedError, setSelectedError] = useState(null);
  const [showReferences, setShowReferences] = useState(false);
  const [references, setReferences] = useState({ regulations: [], references: [] });
  
  // Track error status: pending, accepted, edited, rejected
  const [errorStatus, setErrorStatus] = useState({});
  const [editingErrorId, setEditingErrorId] = useState(null);
  const [editingValue, setEditingValue] = useState('');

  // Fetch references when component mounts
  React.useEffect(() => {
    if (showReferences) {
      fetchReferences();
    }
  }, [showReferences]);

  const fetchReferences = async () => {
    try {
      const res = await fetch(`/api/references/${sessionId}`);
      const data = await res.json();
      setReferences(data.data);
    } catch (err) {
      console.error('Error fetching references:', err);
    }
  };

  // Handle accept suggestion
  const handleAcceptSuggestion = (error) => {
    const newStatus = { ...errorStatus, [error.id]: 'accepted' };
    setErrorStatus(newStatus);
    if (onErrorStatusChange) {
      onErrorStatusChange(error.id, 'accepted', error.suggestion);
    }
  };

  // Start manual edit
  const handleStartEdit = (error) => {
    setEditingErrorId(error.id);
    setEditingValue(error.suggestion);
  };

  // Save manual edit
  const handleSaveEdit = (error) => {
    const newStatus = { ...errorStatus, [error.id]: 'edited' };
    setErrorStatus(newStatus);
    if (onErrorStatusChange) {
      onErrorStatusChange(error.id, 'edited', editingValue);
    }
    setEditingErrorId(null);
    setEditingValue('');
  };

  // Reject error
  const handleRejectError = (error) => {
    const newStatus = { ...errorStatus, [error.id]: 'rejected' };
    setErrorStatus(newStatus);
    if (onErrorStatusChange) {
      onErrorStatusChange(error.id, 'rejected', null);
    }
  };

  // Get error status text
  const getErrorStatusText = (errorId) => {
    const status = errorStatus[errorId];
    if (status === 'accepted') return '✓ Đã sửa';
    if (status === 'edited') return '✏️ Đã chỉnh sửa';
    if (status === 'rejected') return '✗ Bỏ qua';
    return null;
  };

  // Create error map for quick lookup
  const errorMap = useMemo(() => {
    const map = {};
    errors.forEach(err => {
      if (!map[err.elementId]) {
        map[err.elementId] = [];
      }
      map[err.elementId].push(err);
    });
    return map;
  }, [errors]);

  // Get severity icon
  const getSeverityIcon = (severity) => {
    const icons = {
      'error': '🔴',
      'warning': '🟡',
      'info': '🔵'
    };
    return icons[severity] || '⚪';
  };

  // Render paragraph with highlighted errors
  const renderParagraph = (para, paraIdx) => {
    const paraErrors = errorMap[para.id] || [];

    if (paraErrors.length === 0) {
      return (
        <p key={para.id} className="preview-paragraph">
          {para.text}
        </p>
      );
    }

    // Build highlighted text
    let highlightedText = para.text;
    const segments = [];
    let lastIdx = 0;

    // Sort errors by position
    const sortedErrors = [...paraErrors].sort((a, b) => (a.startOffset || 0) - (b.startOffset || 0));

    sortedErrors.forEach(err => {
      const start = err.startOffset || 0;
      const end = err.endOffset || Math.min(start + err.errorText.length, para.text.length);

      if (start > lastIdx) {
        segments.push({
          text: para.text.substring(lastIdx, start),
          error: null
        });
      }

      segments.push({
        text: para.text.substring(start, end),
        error: err
      });

      lastIdx = end;
    });

    if (lastIdx < para.text.length) {
      segments.push({
        text: para.text.substring(lastIdx),
        error: null
      });
    }

    return (
      <p key={para.id} className="preview-paragraph">
        {segments.map((seg, idx) => {
          if (!seg.error) {
            return <span key={idx}>{seg.text}</span>;
          }

          const status = errorStatus[seg.error.id];
          const errorClass = `error-highlight error-${seg.error.severity} ${status ? `status-${status}` : ''}`;
          return (
            <span
              key={idx}
              className={errorClass}
              onClick={() => setSelectedError(seg.error)}
              title={seg.error.message}
            >
              {seg.text}
              <span className="error-indicator">
                {getErrorStatusText(seg.error.id) || getSeverityIcon(seg.error.severity)}
              </span>
            </span>
          );
        })}
      </p>
    );
  };

  // Render table cell with highlighted errors
  const renderTableCell = (cell, rowIdx, cellIdx, tableIdx) => {
    const cellErrors = errorMap[cell.id] || [];

    if (cellErrors.length === 0) {
      return <td key={`${tableIdx}-${rowIdx}-${cellIdx}`}>{cell.text}</td>;
    }

    const errorClass = `error-cell error-${cellErrors[0].severity}`;
    return (
      <td
        key={`${tableIdx}-${rowIdx}-${cellIdx}`}
        className={errorClass}
        onClick={() => setSelectedError(cellErrors[0])}
        title={cellErrors[0].message}
      >
        <span className="error-indicator">{getSeverityIcon(cellErrors[0].severity)}</span>
        {cell.text}
      </td>
    );
  };

  // Render table with highlighted cells
  const renderTable = (table, tableIdx) => {
    return (
      <div key={table.id} className="preview-table-wrapper">
        <table className="preview-table">
          <tbody>
            {table.rows.map((row, rowIdx) => (
              <tr key={`${tableIdx}-${rowIdx}`}>
                {row.cells.map((cell, cellIdx) =>
                  renderTableCell(cell, rowIdx, cellIdx, tableIdx)
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="document-preview">
      <div className="preview-container">
        {/* Left side: Document preview */}
        <div className="preview-main">
          <div className="preview-header">
            <h2>📄 Xem trước tài liệu</h2>
            <button className="btn-close" onClick={onClose}>✕</button>
          </div>

          <div className="preview-content">
            {content.paragraphs && content.paragraphs.map((para, idx) =>
              renderParagraph(para, idx)
            )}

            {content.tables && content.tables.map((table, idx) =>
              <div key={`table-${idx}`}>
                {renderTable(table, idx)}
              </div>
            )}

            {(!content.paragraphs || content.paragraphs.length === 0) &&
             (!content.tables || content.tables.length === 0) && (
              <p className="no-content">Không có nội dung để hiển thị</p>
            )}
          </div>

          <div className="preview-legend">
            <div className="legend-item">
              <span className="error-highlight error-error">Lỗi</span>
              <span>🔴 Lỗi nghiêm trọng</span>
            </div>
            <div className="legend-item">
              <span className="error-highlight error-warning">Cảnh báo</span>
              <span>🟡 Cảnh báo</span>
            </div>
            <div className="legend-item">
              <span className="error-highlight error-info">Thông tin</span>
              <span>🔵 Thông tin</span>
            </div>
          </div>
        </div>

        {/* Right side: Error details & References */}
        <div className="preview-sidebar">
          {selectedError ? (
            <div className="error-details-panel">
              <h3>📋 Chi tiết lỗi</h3>
              
              <div className="detail-section">
                <strong>Mức độ:</strong>
                <span className={`severity-badge severity-${selectedError.severity}`}>
                  {selectedError.severity === 'error' ? '🔴 Lỗi' :
                   selectedError.severity === 'warning' ? '🟡 Cảnh báo' :
                   '🔵 Thông tin'}
                </span>
              </div>

              <div className="detail-section">
                <strong>Loại lỗi:</strong>
                <p>{selectedError.type}</p>
              </div>

              <div className="detail-section">
                <strong>Mô tả lỗi:</strong>
                <p>{selectedError.message}</p>
              </div>

              <div className="detail-section">
                <strong>Nội dung lỗi:</strong>
                <code className="error-code">{selectedError.errorText}</code>
              </div>

              <div className="detail-section">
                <strong>Ngữ cảnh:</strong>
                <p className="context-text">
                  {selectedError.context || 'Không có ngữ cảnh'}
                </p>
              </div>

              <div className="detail-section highlight-section">
                <strong>💡 Đề xuất sửa chữa:</strong>
                <code className="suggestion-code">{selectedError.suggestion}</code>
              </div>

              {selectedError.reference && (
                <div className="detail-section reference-section">
                  <strong>📚 Viện dẫn sở cứ:</strong>
                  <div className="reference-box">
                    <p className="reference-source">
                      Từ: <strong>{selectedError.reference.source === 'regulation' ? '⚖️ Quy định' : '📖 Văn bản sở cứ'}</strong>
                    </p>
                    <p className="reference-location">
                      Vị trí: {selectedError.reference.location}
                    </p>
                    <p className="reference-excerpt">
                      "{selectedError.reference.excerpt}"
                    </p>
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="action-buttons-section">
                <h4>⚙️ Xử lý lỗi</h4>
                
                {editingErrorId === selectedError.id ? (
                  <div className="edit-section">
                    <label>✏️ Sửa thủ công:</label>
                    <textarea
                      className="edit-textarea"
                      value={editingValue}
                      onChange={(e) => setEditingValue(e.target.value)}
                      placeholder="Nhập nội dung sửa chữa..."
                    />
                    <div className="edit-buttons">
                      <button
                        className="btn btn-success btn-small"
                        onClick={() => handleSaveEdit(selectedError)}
                      >
                        💾 Lưu sửa
                      </button>
                      <button
                        className="btn btn-secondary btn-small"
                        onClick={() => {
                          setEditingErrorId(null);
                          setEditingValue('');
                        }}
                      >
                        ✕ Hủy
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="button-group">
                    {errorStatus[selectedError.id] === 'accepted' && (
                      <div className="status-indicator status-accepted">
                        ✓ Đã chấp nhận đề xuất
                      </div>
                    )}
                    {errorStatus[selectedError.id] === 'edited' && (
                      <div className="status-indicator status-edited">
                        ✏️ Đã chỉnh sửa thủ công
                      </div>
                    )}
                    {errorStatus[selectedError.id] === 'rejected' && (
                      <div className="status-indicator status-rejected">
                        ✗ Đã bỏ qua lỗi này
                      </div>
                    )}

                    <div className="button-row">
                      <button
                        className="btn btn-success btn-small"
                        onClick={() => handleAcceptSuggestion(selectedError)}
                        disabled={errorStatus[selectedError.id] === 'accepted'}
                      >
                        ✓ Chấp nhận đề xuất
                      </button>
                      <button
                        className="btn btn-primary btn-small"
                        onClick={() => handleStartEdit(selectedError)}
                      >
                        ✏️ Sửa thủ công
                      </button>
                    </div>
                    <button
                      className="btn btn-danger btn-small btn-full"
                      onClick={() => handleRejectError(selectedError)}
                      disabled={errorStatus[selectedError.id] === 'rejected'}
                    >
                      ✗ Bỏ qua lỗi này
                    </button>
                  </div>
                )}
              </div>

              <button
                className="btn btn-secondary btn-full"
                onClick={() => setShowReferences(!showReferences)}
              >
                {showReferences ? '✕ Ẩn' : '👁️ Xem'} tất cả quy định & sở cứ
              </button>
            </div>
          ) : (
            <div className="no-selection">
              <p>👆 Click vào nội dung lỗi được highlight để xem chi tiết</p>
              <p className="info-text">
                Tổng cộng: <strong>{errors.length}</strong> lỗi
                ({errors.filter(e => e.severity === 'error').length} lỗi,
                 {errors.filter(e => e.severity === 'warning').length} cảnh báo,
                 {errors.filter(e => e.severity === 'info').length} thông tin)
              </p>
            </div>
          )}

          {/* References section */}
          {showReferences && (
            <div className="references-panel">
              <h3>📚 Quy định & Sở cứ</h3>

              {references.regulations.length > 0 && (
                <div className="references-section">
                  <h4>⚖️ Quy định</h4>
                  {references.regulations.map(reg => (
                    <div key={reg.id} className="reference-item">
                      <h5>{reg.name}</h5>
                      <p>{reg.preview}</p>
                    </div>
                  ))}
                </div>
              )}

              {references.references.length > 0 && (
                <div className="references-section">
                  <h4>📖 Văn bản sở cứ</h4>
                  {references.references.map(ref => (
                    <div key={ref.id} className="reference-item">
                      <h5>{ref.name}</h5>
                      <p>{ref.preview}</p>
                    </div>
                  ))}
                </div>
              )}

              {references.regulations.length === 0 && references.references.length === 0 && (
                <p className="no-references">Không có quy định hoặc sở cứ</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default DocumentPreview;
