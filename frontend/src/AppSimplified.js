import React from 'react';
import './AppSimplified.css';
import DocumentUploadSimplified from './components/DocumentUploadSimplified';
import ErrorViewer from './components/ErrorViewer';
import DocumentPreview from './components/DocumentPreview';
import { fetchAndSave } from './utils/download';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const XLSX_MIME =
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
const DOCX_MIME =
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document';

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
  const [view, setView] = React.useState('list'); // 'list' | 'document'

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
  const handleApplySuggestions = async (updates) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/session/${sessionId}/apply-suggestions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ updates }),
      });
      const data = await res.json();
      if (!res.ok || !data.success) {
        throw new Error(data.error || 'Ghi file thất bại');
      }

      setAppliedCount(data.appliedCount || 0);
      setDownloadUrl(data.downloadUrl || null);
      toast.success(`✓ Đã ghi ${data.appliedCount || 0} sửa chữa.`, { autoClose: 3000 });

      // Tải file đã sửa — cho người dùng chọn nơi lưu
      if (data.downloadUrl && data.appliedCount > 0) {
        try {
          await fetchAndSave(data.downloadUrl, 'tai_lieu_da_sua.docx', DOCX_MIME);
        } catch (e) {
          toast.error(`Không tải được file: ${e.message}`, { autoClose: 4000 });
        }
      }
      setStep('complete');
    } catch (err) {
      toast.error(`✗ Lỗi: ${err.message}`, { autoClose: 3000 });
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = async () => {
    try {
      await fetchAndSave(
        `/api/session/${sessionId}/report.xlsx`,
        'bao_cao_tham_dinh.xlsx',
        XLSX_MIME
      );
    } catch (e) {
      toast.error(`Không xuất được Excel: ${e.message}`, { autoClose: 4000 });
    }
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
    setView('list');
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
              <>
                <div className="results-toolbar">
                  <div className="view-switch">
                    <button
                      className={`switch-btn ${view === 'list' ? 'active' : ''}`}
                      onClick={() => setView('list')}
                    >
                      📋 Danh sách lỗi
                    </button>
                    <button
                      className={`switch-btn ${view === 'document' ? 'active' : ''}`}
                      onClick={() => setView('document')}
                    >
                      📄 Xem trên tài liệu
                    </button>
                  </div>
                  <button className="btn btn-excel" onClick={handleExportExcel}>
                    📊 Xuất Excel
                  </button>
                </div>

                {view === 'list' ? (
                  <ErrorViewer
                    errors={errors}
                    onApplySuggestions={handleApplySuggestions}
                    onReset={handleReset}
                    loading={loading}
                  />
                ) : (
                  <DocumentPreview sessionId={sessionId} errors={errors} />
                )}
              </>
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
              {downloadUrl && appliedCount > 0 && (
                <p>
                  <button
                    type="button"
                    className="download-link-btn"
                    onClick={() =>
                      fetchAndSave(downloadUrl, 'tai_lieu_da_sua.docx', DOCX_MIME).catch((e) =>
                        toast.error(`Không tải được file: ${e.message}`, { autoClose: 4000 })
                      )
                    }
                  >
                    ⬇️ Tải lại tài liệu đã sửa
                  </button>
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
