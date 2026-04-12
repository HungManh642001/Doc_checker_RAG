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
  const fileInputMain = React.useRef(null);
  const fileInputRef = React.useRef(null);
  const fileInputRule = React.useRef(null);

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

  const removeFile = (index, type) => {
    if (type === 'reference') {
      setReferenceDocuments(prev => prev.filter((_, i) => i !== index));
    } else if (type === 'rule') {
      setRuleDocuments(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleUpload = async () => {
    if (!mainDocument) {
      toast.error('Vui lòng chọn tài liệu cần thẩm định', { autoClose: 3000 });
      return;
    }

    if (referenceDocuments.length === 0 && ruleDocuments.length === 0) {
      toast.warning(
        'Khuyến nghị: Hãy tải lên ít nhất một tài liệu sở cứ hoặc quy định để cải thiện độ chính xác.',
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
            Tải lên tài liệu tham khảo để xây dựng cơ sở tri thức
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
        </div>

        {/* Rule Documents */}
        <div className="upload-section">
          <h2 className="section-title">
            ⚖️ Quy Định / Tiêu Chuẩn <span className="optional">(Tùy chọn)</span>
          </h2>
          <p className="section-hint">
            Tải lên các tài liệu quy định để cải thiện độ chính xác thẩm định
          </p>

          <div 
            className="upload-box"
            onClick={() => fileInputRule.current?.click()}
          >
            <span className="upload-icon">⚖️</span>
            <p className="upload-text">Thêm quy định / tiêu chuẩn</p>
            <p className="upload-format">Chọn nhiều file DOCX</p>
          </div>
          <input
            ref={fileInputRule}
            type="file"
            multiple
            accept=".docx,.doc"
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
        </div>

        {/* Summary */}
        {(mainDocument || docCount > 0) && (
          <div className="upload-summary">
            <p>
              ✓ Tài liệu cần thẩm định: <strong>{mainDocument?.name || 'Chưa chọn'}</strong>
            </p>
            <p>
              ✓ Tài liệu sở cứ/quy định: <strong>{docCount}</strong> file
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
          <strong>ℹ️ Lưu ý:</strong>
          <ul>
            <li>
              <strong>Tài liệu cần thẩm định (*):</strong> Bắt buộc - DOCX file cần kiểm tra
            </li>
            <li>
              <strong>Tài liệu sở cứ:</strong> Từ 0+ DOCX files để xây dựng RAG index
            </li>
            <li>
              <strong>Quy định/Tiêu chuẩn:</strong> Từ 0+ DOCX files với các quy tắc
            </li>
            <li>
              Hệ thống sẽ xây dựng RAG index từ các tài liệu sở cứ
            </li>
            <li>
              Sau đó phân tích tài liệu chính dựa trên index này
            </li>
            <li>
              Quá trình có thể mất vài phút tùy thuộc vào kích thước file
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default DocumentUploadSimplified;
