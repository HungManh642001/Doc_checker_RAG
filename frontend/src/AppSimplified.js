import React from 'react';
import './AppSimplified.css';
import DocumentUploadSimplified from './components/DocumentUploadSimplified';
import ErrorViewer from './components/ErrorViewer';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

/**
 * AppSimplified - Luồng thẩm định RAG đơn giản hoá
 *
 * Flow:
 * 1. Upload tài liệu chính + sở cứ + quy định
 * 2. Hệ thống RAG thẩm định ngay
 * 3. ErrorViewer hiển thị lỗi, người dùng chấp nhận/từ chối/sửa
 * 4. Ghi file đã sửa → tải về
 */
function App() {
  const [sessionId, setSessionId] = React.useState(null);
  const [step, setStep] = React.useState('upload'); // 'upload' | 'results' | 'complete'
  const [errors, setErrors] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [errorCount, setErrorCount] = React.useState(0);
  const [appliedCount, setAppliedCount] = React.useState(0);
  const [downloadUrl, setDownloadUrl] = React.useState(null);

  const handleUploadComplete = (newSessionId, analysisErrors) => {
    setSessionId(newSessionId);
    setErrors(analysisErrors || []);
    setErrorCount(analysisErrors?.length || 0);

    if (analysisErrors && analysisErrors.length > 0) {
      toast.success(`✓ Thẩm định hoàn tất! Phát hiện ${analysisErrors.length} lỗi.`, {
        position: 'top-right',
        autoClose: 5000,
      });
    } else {
      toast.info('✓ Tài liệu hợp lệ - không có lỗi phát hiện.', {
        position: 'top-right',
        autoClose: 5000,
      });
    }
    setStep('results');
  };

  /**
   * Áp dụng các sửa chữa. `updates` đến trực tiếp từ ErrorViewer:
   *   [{ errorId, action: 'accept'|'reject', fixedValue }]
   */
  const handleApplySuggestions = (updates) => {
    setLoading(true);

    fetch(`/api/session/${sessionId}/apply-suggestions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ updates }),
    })
      .then((res) => res.json())
      .then((data) => {
        setLoading(false);
        if (data.success) {
          setAppliedCount(data.appliedCount || 0);
          setDownloadUrl(data.downloadUrl || null);
          toast.success(`✓ Đã ghi ${data.appliedCount || 0} sửa chữa.`, { autoClose: 3000 });
          // Tự động tải file đã sửa (nếu có)
          if (data.downloadUrl) {
            window.location.href = data.downloadUrl;
          }
          setStep('complete');
        } else {
          toast.error(data.error || 'Ghi file thất bại', { autoClose: 3000 });
        }
      })
      .catch((err) => {
        setLoading(false);
        toast.error(`✗ Lỗi: ${err.message}`, { autoClose: 3000 });
      });
  };

  const handleReset = () => {
    if (sessionId) {
      fetch(`/api/session/${sessionId}/cleanup`, { method: 'DELETE' }).catch((err) =>
        console.error('Cleanup error:', err)
      );
    }
    setSessionId(null);
    setStep('upload');
    setErrors([]);
    setErrorCount(0);
    setAppliedCount(0);
    setDownloadUrl(null);
  };

  const renderStep = () => {
    switch (step) {
      case 'upload':
        return (
          <div className="app-container upload-container">
            <DocumentUploadSimplified
              onUploadComplete={handleUploadComplete}
              loading={loading}
              setLoading={setLoading}
            />
          </div>
        );

      case 'results':
        return (
          <div className="app-container results-container">
            {errors.length > 0 ? (
              <ErrorViewer
                errors={errors}
                onApplySuggestions={handleApplySuggestions}
                onReset={handleReset}
                loading={loading}
              />
            ) : (
              <div className="no-errors-screen">
                <h1>✅ Tài liệu hợp lệ</h1>
                <p>Không phát hiện lỗi nào theo quy định &amp; sở cứ hiện tại.</p>
                <button className="btn btn-secondary" onClick={handleReset}>
                  ← Thẩm định tài liệu khác
                </button>
              </div>
            )}
          </div>
        );

      case 'complete':
        return (
          <div className="app-container complete-container">
            <div className="complete-message">
              <h1>✓ Hoàn tất</h1>
              <p>Đã ghi {appliedCount} sửa chữa vào tài liệu.</p>
              {downloadUrl && (
                <p>
                  Nếu file chưa tự tải,{' '}
                  <a href={downloadUrl} className="download-link">
                    bấm vào đây để tải lại
                  </a>
                  .
                </p>
              )}
              <button className="btn btn-primary" onClick={handleReset}>
                Thẩm định tài liệu khác
              </button>
            </div>
          </div>
        );

      default:
        return <div>Error: Unknown step</div>;
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>📄 Hệ thống AI Thẩm định Tài liệu YCKT</h1>
        <p>Phát hiện lỗi · Đề xuất sửa chữa · Viện dẫn sở cứ</p>
      </header>
      <ToastContainer />
      {renderStep()}
    </div>
  );
}

export default App;
