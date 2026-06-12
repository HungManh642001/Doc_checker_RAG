import React, { useState, useMemo } from 'react';
import './ErrorViewer.css';

/**
 * ErrorViewer — DANH SÁCH LỖI (chỉ xem / báo cáo).
 *
 * Việc sửa & tải tài liệu đã chuyển sang tab "Xem trên tài liệu" (DocumentPreview);
 * xuất báo cáo qua nút "Xuất Excel" trên thanh công cụ. Component này chỉ hiển thị.
 *
 * Props:
 *   errors: danh sách lỗi từ backend
 */
function ErrorViewer({ errors }) {
  const [expandedErrorId, setExpandedErrorId] = useState(null);

  const errCount = useMemo(
    () => errors.filter((e) => e.severity !== 'warning').length,
    [errors]
  );
  const warnCount = errors.length - errCount;

  // Thống kê theo loại lỗi để xem nhanh bức tranh tổng thể
  const typeCounts = useMemo(() => {
    const m = {};
    errors.forEach((e) =>
      (e.danh_sach_cac_loi || []).forEach((d) => {
        const t = d.error_type || 'Khác';
        m[t] = (m[t] || 0) + 1;
      })
    );
    return Object.entries(m).sort((a, b) => b[1] - a[1]);
  }, [errors]);

  return (
    <div className="error-viewer">
      <div className="error-header">
        <div className="header-content">
          <h1>📋 Kết quả thẩm định</h1>
          <p className="subtitle">
            Phát hiện <strong>{errCount}</strong> lỗi
            {warnCount > 0 && (
              <> và <strong>{warnCount}</strong> cảnh báo nội dung</>
            )}{' '}
            cần xem xét
          </p>
          <div className="stats">
            <span className="stat-item total">
              ❌ Lỗi: <strong>{errCount}</strong>
            </span>
            {warnCount > 0 && (
              <span className="stat-item total" style={{ background: '#fef3c7', color: '#b9770e' }}>
                ⚠️ Cảnh báo: <strong>{warnCount}</strong>
              </span>
            )}
            {typeCounts.map(([t, c]) => (
              <span key={t} className="stat-item type">
                {t}: <strong>{c}</strong>
              </span>
            ))}
          </div>
        </div>
      </div>

      <div className="filter-section">
        <div className="filter-hint">
          Danh sách chỉ để xem. Để <strong>sửa &amp; tải tài liệu</strong>, chuyển sang tab
          <strong> 📄 Xem trên tài liệu</strong>. Để xuất danh sách lỗi, bấm
          <strong> 📊 Xuất Excel</strong>.
        </div>
      </div>

      <div className="error-list">
        {errors.length === 0 ? (
          <div className="no-errors">
            <p>✅ Không phát hiện lỗi nào! Tài liệu tuân thủ quy định.</p>
          </div>
        ) : (
          errors.map((error) => {
            const isExpanded = expandedErrorId === error.id;
            const isWarn = error.severity === 'warning';
            const color = isWarn ? '#f39c12' : '#e74c3c';
            return (
              <div
                key={error.id}
                className="error-item"
                style={{ borderLeftColor: color }}
              >
                <div className="error-item-header">
                  <div className="error-main-info">
                    <div className="error-title-row">
                      <span className="severity-badge" style={{ backgroundColor: color }}>
                        {isWarn ? '⚠️ CẢNH BÁO' : '❌ LỖI'}
                      </span>
                    </div>

                    <div className="original-text-box">
                      <strong>📌 Nội dung gốc:</strong>
                      <code className="original-text">{error.original_text}</code>
                    </div>

                    <div className="error-list-container">
                      <strong>{isWarn ? '⚠️ Đối chiếu phát hiện:' : '🔴 Lỗi phát hiện:'}</strong>
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
                    {!isWarn && error.suggestion && (
                      <div className="suggestion-section">
                        <strong>💡 Đề xuất sửa chữa:</strong>
                        <div className="suggestion-display">
                          <code>{error.suggestion}</code>
                        </div>
                      </div>
                    )}

                    <div className="reference-section">
                      <div className="reference-box">
                        <strong>
                          {isWarn ? '📖 Đối chiếu YCKT trước đây:' : '📖 Tham chiếu sở cứ:'}
                        </strong>
                        <p className="reference-location">{error.reference_location}</p>
                        <p className="reference-quote">{error.reference_quote}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

export default ErrorViewer;
