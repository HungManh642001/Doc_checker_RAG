import React, { useState } from 'react';
import axios from 'axios';
import { toast } from 'react-toastify';
import './DocumentUpload.css';


function DocumentUpload({ onUploadComplete, onAnalyzeComplete }) {
  const [mainDocument, setMainDocument] = useState(null);
  const [referenceDocuments, setReferenceDocuments] = useState([]);
  const [regulations, setRegulations] = useState([]);
  const [uploading, setUploading] = useState(false);

  const handleMainDocumentChange = (e) => {
    const file = e.target.files[0];
    if (file && file.name.endsWith('.docx')) {
      setMainDocument(file);
    } else {
      toast.error('Vui lòng chọn file DOCX');
    }
  };

  const handleReferenceDocumentsChange = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(f => f.name.endsWith('.docx'));
    setReferenceDocuments(validFiles);
  };

  const handleRegulationsChange = (e) => {
    const files = Array.from(e.target.files);
    const validFiles = files.filter(f => f.name.endsWith('.docx'));
    setRegulations(validFiles);
  };

  const handleRemoveMainDoc = () => {
    setMainDocument(null);
  };

  const handleRemoveReferenceDoc = (index) => {
    setReferenceDocuments(referenceDocuments.filter((_, i) => i !== index));
  };

  const handleRemoveRegulation = (index) => {
    setRegulations(regulations.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (!mainDocument) {
      toast.error('Vui lòng chọn tài liệu cần thẩm định');
      return;
    }

    const formData = new FormData();
    formData.append('mainDocument', mainDocument);
    referenceDocuments.forEach((doc, index) => {
      formData.append('referenceDocuments', doc);
    });
    regulations.forEach((doc, index) => {
      formData.append('regulations', doc);
    });

    setUploading(true);
    try {
      const response = await axios.post('/api/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      toast.success('Tài liệu đã được tải lên thành công!');
      const sessionId = response.data.sessionId;
      onUploadComplete(sessionId);

    } catch (error) {
      toast.error('Lỗi khi tải tài liệu: ' + error.message);
      setUploading(false);
    }
  };

  return (
    <div className="document-upload">
      <div className="upload-section">
        <div className="upload-card">
          <h2>📝 Tài liệu cần thẩm định</h2>
          <div className="file-input-wrapper">
            <input
              type="file"
              id="mainDoc"
              accept=".docx"
              onChange={handleMainDocumentChange}
              className="file-input"
            />
            <label htmlFor="mainDoc" className="file-label">
              Chọn tài liệu (DOCX)
            </label>
          </div>
          {mainDocument && (
            <div className="file-item">
              <span className="file-name">📄 {mainDocument.name}</span>
              <button onClick={handleRemoveMainDoc} className="btn-remove">✕</button>
            </div>
          )}
        </div>

        <div className="upload-card">
          <h2>📚 Văn bản sở cứ (tuỳ chọn)</h2>
          <div className="file-input-wrapper">
            <input
              type="file"
              id="refDocs"
              accept=".docx"
              multiple
              onChange={handleReferenceDocumentsChange}
              className="file-input"
            />
            <label htmlFor="refDocs" className="file-label">
              Chọn tài liệu sở cứ
            </label>
          </div>
          <div className="file-list">
            {referenceDocuments.map((doc, index) => (
              <div key={index} className="file-item">
                <span className="file-name">📄 {doc.name}</span>
                <button onClick={() => handleRemoveReferenceDoc(index)} className="btn-remove">✕</button>
              </div>
            ))}
          </div>
        </div>

        <div className="upload-card">
          <h2>⚖️ Quy định và tiêu chuẩn (tuỳ chọn)</h2>
          <div className="file-input-wrapper">
            <input
              type="file"
              id="regulations"
              accept=".docx"
              multiple
              onChange={handleRegulationsChange}
              className="file-input"
            />
            <label htmlFor="regulations" className="file-label">
              Chọn quy định
            </label>
          </div>
          <div className="file-list">
            {regulations.map((doc, index) => (
              <div key={index} className="file-item">
                <span className="file-name">📄 {doc.name}</span>
                <button onClick={() => handleRemoveRegulation(index)} className="btn-remove">✕</button>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="upload-actions">
        <button
          className="btn btn-primary btn-large"
          onClick={handleUpload}
          disabled={!mainDocument || uploading}
        >
          {uploading ? '⏳ Đang tải...' : '👁️ Tải lên và Xem trước'}
        </button>
      </div>

      <div className="info-section">
        <h3>💡 Hướng dẫn sử dụng:</h3>
        <ul>
          <li><strong>Tài liệu cần thẩm định:</strong> File DOCX chính cần kiểm tra</li>
          <li><strong>Văn bản sở cứ:</strong> Những tài liệu tham chiếu để so sánh</li>
          <li><strong>Quy định:</strong> Các quy định cần tuân thủ</li>
          <li>Hệ thống sẽ phân tích và đề xuất các sửa chữa cần thiết</li>
        </ul>
      </div>
    </div>
  );
}

export default DocumentUpload;
