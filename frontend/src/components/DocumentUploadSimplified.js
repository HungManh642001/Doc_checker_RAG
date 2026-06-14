import React from 'react';
import './DocumentUploadSimplified.css';
import { toast } from 'react-toastify';

/**
 * DocumentUploadSimplified - Simplified upload component
 * 
 * Uploads:
 * - Main document (required) - DOCX to analyze
 * - Reference documents (optional) - DOCX files for building RAG index
 * - Rule documents (optional) - DOCX files with regulations
 */
function DocumentUploadSimplified({ onUploadComplete, loading, setLoading }) {
  const [mainDocument, setMainDocument] = React.useState(null);
  const [referenceDocuments, setReferenceDocuments] = React.useState([]);
  const [ruleDocuments, setRuleDocuments] = React.useState([]);
  // Previously approved YCKT → lookup store for the Q&A chatbot
  const [historyDocuments, setHistoryDocuments] = React.useState([]);
  const [defaultRules, setDefaultRules] = React.useState(null);
  const [showDefaultRules, setShowDefaultRules] = React.useState(false);
  // Saved preset library + the user's selection
  const [presets, setPresets] = React.useState({ references: [], rules: [] });
  const [selectedRefPresets, setSelectedRefPresets] = React.useState([]);
  const [selectedRulePresets, setSelectedRulePresets] = React.useState([]);
  const [savePresets, setSavePresets] = React.useState(false);
  const fileInputMain = React.useRef(null);
  const fileInputRef = React.useRef(null);
  const fileInputRule = React.useRef(null);
  const fileInputHistory = React.useRef(null);

  const loadPresets = React.useCallback(async () => {
    try {
      const res = await fetch('/api/presets');
      const data = await res.json();
      setPresets({ references: data.references || [], rules: data.rules || [] });
    } catch (e) {
      console.error('Không tải được thư viện preset:', e);
    }
  }, []);

  React.useEffect(() => {
    loadPresets();
  }, [loadPresets]);

  const togglePreset = (kind, name) => {
    if (kind === 'reference') {
      setSelectedRefPresets((prev) =>
        prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
      );
    } else {
      setSelectedRulePresets((prev) =>
        prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]
      );
    }
  };

  const deletePreset = async (kind, name) => {
    if (!window.confirm(`Xoá preset "${name}" khỏi thư viện?`)) return;
    try {
      const res = await fetch(`/api/presets/${kind}/${encodeURIComponent(name)}`, {
        method: 'DELETE',
      });
      if (!res.ok) {
        const d = await res.json();
        throw new Error(d.error || 'Xoá thất bại');
      }
      toast.success(`Đã xoá ${name}`, { autoClose: 2000 });
      setSelectedRefPresets((p) => p.filter((n) => n !== name));
      setSelectedRulePresets((p) => p.filter((n) => n !== name));
      loadPresets();
    } catch (e) {
      toast.error(e.message, { autoClose: 3000 });
    }
  };

  const formatSize = (bytes) =>
    bytes >= 1024 * 1024
      ? `${(bytes / 1024 / 1024).toFixed(1)} MB`
      : `${(bytes / 1024).toFixed(1)} KB`;

  const toggleDefaultRules = async () => {
    if (showDefaultRules) {
      setShowDefaultRules(false);
      return;
    }
    if (defaultRules === null) {
      try {
        const res = await fetch('/api/rules/default');
        const data = await res.json();
        setDefaultRules(data.rules || 'Không tải được quy định mặc định.');
      } catch (e) {
        setDefaultRules('Không tải được quy định mặc định.');
      }
    }
    setShowDefaultRules(true);
  };

  const handleMainDocumentChange = (e) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setMainDocument(files[0]);
    }
  };

  const handleReferenceDocumentsChange = (e) => {
    const files = Array.from(e.target.files || []);
    setReferenceDocuments(prev => [...prev, ...files]);
  };

  const handleRuleDocumentsChange = (e) => {
    const files = Array.from(e.target.files || []);
    setRuleDocuments(prev => [...prev, ...files]);
  };

  const handleHistoryDocumentsChange = (e) => {
    const files = Array.from(e.target.files || []);
    setHistoryDocuments(prev => [...prev, ...files]);
  };

  const removeFile = (index, type) => {
    if (type === 'reference') {
      setReferenceDocuments(prev => prev.filter((_, i) => i !== index));
    } else if (type === 'rule') {
      setRuleDocuments(prev => prev.filter((_, i) => i !== index));
    } else if (type === 'history') {
      setHistoryDocuments(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleUpload = async () => {
    if (!mainDocument) {
      toast.error('Vui lòng chọn tài liệu cần thẩm định', { autoClose: 3000 });
      return;
    }

    const hasAnySource =
      referenceDocuments.length ||
      ruleDocuments.length ||
      selectedRefPresets.length ||
      selectedRulePresets.length;
    if (!hasAnySource) {
      toast.info(
        'Không chọn sở cứ/quy định — hệ thống sẽ dùng bộ mặc định (NĐ 86 + quy định chung).',
        { autoClose: 5000 }
      );
    }

    setLoading(true);
    const formData = new FormData();

    // Add main document
    formData.append('mainDocument', mainDocument);

    // Add reference documents
    referenceDocuments.forEach(doc => {
      formData.append('referenceDocuments', doc);
    });

    // Add rule documents
    ruleDocuments.forEach(doc => {
      formData.append('ruleDocuments', doc);
    });

    // Add history documents (old YCKT → lookup store for the chatbot)
    historyDocuments.forEach(doc => {
      formData.append('historyDocuments', doc);
    });

    // Add selected presets (reused from the library)
    selectedRefPresets.forEach((name) => formData.append('referencePresets', name));
    selectedRulePresets.forEach((name) => formData.append('rulePresets', name));

    // Save the just-uploaded files as presets
    if (savePresets) {
      formData.append('savePresets', 'true');
    }

    try {
      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || 'Upload failed');
      }

      toast.success('✓ Tải lên và phân tích thành công!', { autoClose: 3000 });
      
      // Call callback with session ID and errors
      if (onUploadComplete) {
        onUploadComplete(data.sessionId, data.results?.errors || []);
      }

    } catch (error) {
      console.error('Upload error:', error);
      toast.error(`✗ Lỗi: ${error.message}`, { autoClose: 3000 });
    } finally {
      setLoading(false);
    }
  };

  const docCount = (referenceDocuments.length + ruleDocuments.length);

  return (
    <div className="upload-simplified">
      <div className="upload-card">
        <h1>Thẩm Định Tài Liệu</h1>
        <p className="subtitle">
          Sử dụng RAG để phân tích và phát hiện lỗi trong tài liệu
        </p>

        {/* Main Document Upload */}
        <div className="upload-section">
          <h2 className="section-title">
            📄 Tài Liệu Cần Thẩm Định <span className="required">*</span>
          </h2>
          <p className="section-hint">
            Chọn tài liệu DOCX cần kiểm tra
          </p>

          <div 
            className={`upload-box main-upload ${mainDocument ? 'loaded' : ''}`}
            onClick={() => fileInputMain.current?.click()}
          >
            {mainDocument ? (
              <div className="file-info">
                <span className="file-icon">📋</span>
                <span className="file-name">{mainDocument.name}</span>
                <span className="file-size">
                  {(mainDocument.size / 1024).toFixed(1)} KB
                </span>
              </div>
            ) : (
              <>
                <span className="upload-icon">📤</span>
                <p className="upload-text">
                  Nhấp để chọn tài liệu hoặc kéo thả
                </p>
                <p className="upload-format">DOCX, DOC (tối đa 50 MB)</p>
              </>
            )}
          </div>
          <input
            ref={fileInputMain}
            type="file"
            accept=".docx,.doc"
            onChange={handleMainDocumentChange}
            style={{ display: 'none' }}
          />
        </div>

        {/* Reference Documents */}
        <div className="upload-section">
          <h2 className="section-title">
            📚 Tài Liệu Sở Cứ <span className="optional">(Tùy chọn)</span>
          </h2>
          <p className="section-hint">
            Tài liệu tham khảo (NĐ, tiêu chuẩn...) để xây dựng cơ sở tri thức RAG. Nếu bỏ
            trống, hệ thống dùng sở cứ mặc định (Nghị định 86/2012).
          </p>

          <div 
            className="upload-box"
            onClick={() => fileInputRef.current?.click()}
          >
            <span className="upload-icon">📚</span>
            <p className="upload-text">Thêm tài liệu sở cứ</p>
            <p className="upload-format">Chọn nhiều file DOCX</p>
          </div>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".docx,.doc"
            onChange={handleReferenceDocumentsChange}
            style={{ display: 'none' }}
          />

          {referenceDocuments.length > 0 && (
            <div className="file-list">
              <p className="file-list-title">Tài liệu sở cứ ({referenceDocuments.length}):</p>
              {referenceDocuments.map((file, idx) => (
                <div key={idx} className="file-item reference-item">
                  <span className="file-info-small">
                    📄 {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                  <button
                    className="remove-btn"
                    onClick={() => removeFile(idx, 'reference')}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          {presets.references.length > 0 && (
            <div className="preset-library">
              <p className="preset-title">📂 Hoặc dùng lại từ thư viện sở cứ:</p>
              {presets.references.map((p) => (
                <label
                  key={p.name}
                  className={`preset-chip ${selectedRefPresets.includes(p.name) ? 'selected' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedRefPresets.includes(p.name)}
                    onChange={() => togglePreset('reference', p.name)}
                  />
                  <span className="preset-name">📄 {p.name}</span>
                  <span className="preset-size">{formatSize(p.size)}</span>
                  {!p.protected && (
                    <span
                      className="preset-del"
                      title="Xoá khỏi thư viện"
                      onClick={(e) => {
                        e.preventDefault();
                        deletePreset('reference', p.name);
                      }}
                    >
                      🗑️
                    </span>
                  )}
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Rule Documents */}
        <div className="upload-section">
          <h2 className="section-title">
            ⚖️ Quy Định / Tiêu Chuẩn <span className="optional">(Tùy chọn)</span>
          </h2>
          <p className="section-hint">
            Tải lên file quy định thẩm định (vd: <code>quy_dinh_chung.md</code>). Đây là các
            quy tắc LLM dùng để bắt lỗi. Nếu bỏ trống, hệ thống dùng quy định mặc định.
          </p>

          <button type="button" className="link-btn" onClick={toggleDefaultRules}>
            {showDefaultRules ? '▼ Ẩn quy định mặc định' : '▶ Xem quy định mặc định đang dùng'}
          </button>
          {showDefaultRules && (
            <pre className="default-rules-preview">{defaultRules ?? 'Đang tải...'}</pre>
          )}

          <div
            className="upload-box"
            onClick={() => fileInputRule.current?.click()}
          >
            <span className="upload-icon">⚖️</span>
            <p className="upload-text">Thêm quy định / tiêu chuẩn</p>
            <p className="upload-format">MD, TXT, DOCX</p>
          </div>
          <input
            ref={fileInputRule}
            type="file"
            multiple
            accept=".md,.txt,.docx,.doc"
            onChange={handleRuleDocumentsChange}
            style={{ display: 'none' }}
          />

          {ruleDocuments.length > 0 && (
            <div className="file-list">
              <p className="file-list-title">Quy định ({ruleDocuments.length}):</p>
              {ruleDocuments.map((file, idx) => (
                <div key={idx} className="file-item rule-item">
                  <span className="file-info-small">
                    ⚖️ {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                  <button
                    className="remove-btn"
                    onClick={() => removeFile(idx, 'rule')}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}

          {presets.rules.length > 0 && (
            <div className="preset-library">
              <p className="preset-title">📂 Hoặc dùng lại từ thư viện quy định:</p>
              {presets.rules.map((p) => (
                <label
                  key={p.name}
                  className={`preset-chip ${selectedRulePresets.includes(p.name) ? 'selected' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedRulePresets.includes(p.name)}
                    onChange={() => togglePreset('rule', p.name)}
                  />
                  <span className="preset-name">⚖️ {p.name}</span>
                  <span className="preset-size">{formatSize(p.size)}</span>
                  {!p.protected && (
                    <span
                      className="preset-del"
                      title="Xoá khỏi thư viện"
                      onClick={(e) => {
                        e.preventDefault();
                        deletePreset('rule', p.name);
                      }}
                    >
                      🗑️
                    </span>
                  )}
                </label>
              ))}
            </div>
          )}
        </div>

        {/* History Documents (old YCKT → Q&A chatbot) */}
        <div className="upload-section">
          <h2 className="section-title">
            🗂️ YCKT Tham Khảo Trước Đây <span className="optional">(Tùy chọn)</span>
          </h2>
          <p className="section-hint">
            Các tài liệu YCKT đã duyệt trước đây. Dùng làm kho tra cứu cho chatbot hỏi-đáp
            (xem một thông số đã từng dùng giá trị nào, có tham khảo được không). Không
            ảnh hưởng tới kết quả thẩm định lỗi.
          </p>

          <div
            className="upload-box"
            onClick={() => fileInputHistory.current?.click()}
          >
            <span className="upload-icon">🗂️</span>
            <p className="upload-text">Thêm YCKT tham khảo</p>
            <p className="upload-format">Chọn nhiều file DOCX/HTML</p>
          </div>
          <input
            ref={fileInputHistory}
            type="file"
            multiple
            accept=".docx,.doc,.html"
            onChange={handleHistoryDocumentsChange}
            style={{ display: 'none' }}
          />

          {historyDocuments.length > 0 && (
            <div className="file-list">
              <p className="file-list-title">YCKT tham khảo ({historyDocuments.length}):</p>
              {historyDocuments.map((file, idx) => (
                <div key={idx} className="file-item reference-item">
                  <span className="file-info-small">
                    🗂️ {file.name} ({(file.size / 1024).toFixed(1)} KB)
                  </span>
                  <button
                    className="remove-btn"
                    onClick={() => removeFile(idx, 'history')}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Save as preset */}
        {(referenceDocuments.length > 0 || ruleDocuments.length > 0) && (
          <label className="save-preset-toggle">
            <input
              type="checkbox"
              checked={savePresets}
              onChange={(e) => setSavePresets(e.target.checked)}
            />
            💾 Lưu các file vừa tải lên vào thư viện để tái dùng lần sau
          </label>
        )}

        {/* Summary */}
        {(mainDocument || docCount > 0 ||
          selectedRefPresets.length > 0 || selectedRulePresets.length > 0) && (
          <div className="upload-summary">
            <p>
              ✓ Tài liệu cần thẩm định: <strong>{mainDocument?.name || 'Chưa chọn'}</strong>
            </p>
            <p>
              ✓ Sở cứ: <strong>{referenceDocuments.length + selectedRefPresets.length}</strong>{' '}
              · Quy định: <strong>{ruleDocuments.length + selectedRulePresets.length}</strong>
            </p>
          </div>
        )}

        {/* Upload Button */}
        <button
          className={`btn btn-upload ${loading ? 'loading' : ''} ${!mainDocument ? 'disabled' : ''}`}
          onClick={handleUpload}
          disabled={!mainDocument || loading}
        >
          {loading ? (
            <>
              <span className="spinner"></span>
              Đang thẩm định...
            </>
          ) : (
            '🚀 Bắt Đầu Thẩm Định'
          )}
        </button>

        {/* Info Box */}
        <div className="info-box">
          <strong>ℹ️ Cách hoạt động:</strong>
          <ul>
            <li>
              <strong>Tài liệu cần thẩm định (*):</strong> Bắt buộc — file DOCX cần kiểm tra.
            </li>
            <li>
              <strong>Sở cứ → cơ sở tri thức:</strong> được embed &amp; lập chỉ mục RAG để
              hệ thống truy xuất căn cứ. Bỏ trống ⇒ dùng NĐ 86/2012 mặc định.
            </li>
            <li>
              <strong>Quy định → luật chấm lỗi:</strong> nội dung được đưa thẳng vào prompt
              để LLM bắt lỗi. Bỏ trống ⇒ dùng <code>quy_dinh_chung.md</code> mặc định.
            </li>
            <li>
              Quá trình thẩm định có thể mất vài phút tùy kích thước tài liệu &amp; sở cứ.
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default DocumentUploadSimplified;
