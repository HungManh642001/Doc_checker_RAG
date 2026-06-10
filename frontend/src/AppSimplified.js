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

/**
 * AppSimplified - Luồng thẩm định RAG đơn giản hoá
 *
 * Flow:
 * 1. Upload tài liệu chính + sở cứ + quy định → hệ thống thẩm định ngay
 * 2. Kết quả: xem dưới dạng "Danh sách lỗi" (báo cáo) hoặc "Xem trên tài liệu"
 *    (sửa trực tiếp & tải file đã sửa). Xuất Excel danh sách lỗi.
 */
function App() {
  const [sessionId, setSessionId] = React.useState(null);
  const [step, setStep] = React.useState('upload'); // 'upload' | 'results'
  const [errors, setErrors] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [view, setView] = React.useState('list'); // 'list' | 'document'

  const handleUploadComplete = (newSessionId, analysisErrors) => {
    setSessionId(newSessionId);
    setErrors(analysisErrors || []);

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
                  <button className="btn btn-reset" onClick={handleReset}>
                    ← Thẩm định tài liệu khác
                  </button>

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
                  <ErrorViewer errors={errors} />
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
