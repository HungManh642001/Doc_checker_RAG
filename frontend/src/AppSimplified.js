import React from 'react';
import './AppSimplified.css';
import DocumentUploadSimplified from './components/DocumentUploadSimplified';
import ErrorViewer from './components/ErrorViewer';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

/**
 * AppSimplified - Simplified RAG-based document analysis
 * 
 * Flow:
 * 1. Upload main document + reference documents
 * 2. RAG system analyzes immediately
 * 3. Display errors with ErrorViewer
 * 4. Apply suggestions (optional)
 */
function App() {
  const [sessionId, setSessionId] = React.useState(null);
  const [step, setStep] = React.useState('upload'); // 'upload', 'results', 'complete'
  const [errors, setErrors] = React.useState([]);
  const [loading, setLoading] = React.useState(false);
  const [errorStatus, setErrorStatus] = React.useState({}); // Track error status
  const [errorCount, setErrorCount] = React.useState(0);

  /**
   * Handle upload - directly triggers analysis
   */
  const handleUploadComplete = (newSessionId, analysisErrors) => {
    setSessionId(newSessionId);
    setErrors(analysisErrors || []);
    setErrorCount(analysisErrors?.length || 0);
    
    if (analysisErrors && analysisErrors.length > 0) {
      toast.success(`✓ Thẩm định hoàn tất! Phát hiện ${analysisErrors.length} lỗi.`, {
        position: 'top-right',
        autoClose: 5000
      });
    } else {
      toast.info('✓ Tài liệu hợp lệ - không có lỗi phát hiện.', {
        position: 'top-right',
        autoClose: 5000
      });
    }
    
    setStep('results');
  };

  /**
   * Handle error status change (accept/reject/edit)
   */
  const handleErrorStatusChange = (errorId, status, value) => {
    setErrorStatus(prev => ({
      ...prev,
      [errorId]: { status, value }
    }));
  };

  /**
   * Apply accepted suggestions
   */
  const handleApplySuggestions = (acceptedErrors) => {
    setLoading(true);
    
    const updates = acceptedErrors.map(err => {
      const errStatus = errorStatus[err.id];
      return {
        errorId: err.id,
        action: errStatus?.status || 'accept',
        customSuggestion: errStatus?.value
      };
    });

    fetch(`/api/session/${sessionId}/apply-suggestions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ updates })
    })
    .then(res => res.json())
    .then(data => {
      setLoading(false);
      if (data.success) {
        toast.success('✓ Ghi lại các sửa chữa', { autoClose: 3000 });
        setStep('complete');
      }
    })
    .catch(err => {
      setLoading(false);
      toast.error(`✗ Lỗi: ${err.message}`, { autoClose: 3000 });
    });
  };

  /**
   * Reset and start over
   */
  const handleReset = () => {
    if (sessionId) {
      // Cleanup session on server
      fetch(`/api/session/${sessionId}/cleanup`, { method: 'DELETE' })
        .catch(err => console.error('Cleanup error:', err));
    }
    
    setSessionId(null);
    setStep('upload');
    setErrors([]);
    setErrorStatus({});
    setErrorCount(0);
  };

  /**
   * Render current step
   */
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
            <div className="results-header">
              <h1>Kết Quả Thẩm Định</h1>
              <p className="error-summary">
                Phát hiện <span className="error-count">{errorCount}</span> lỗi
              </p>
            </div>
            
            {errors.length > 0 ? (
              <>
                <ErrorViewer 
                  errors={errors}
                  onErrorStatusChange={handleErrorStatusChange}
                  errorStatus={errorStatus}
                />
                
                <div className="results-actions">
                  <button 
                    className="btn btn-primary"
                    onClick={() => handleApplySuggestions(errors)}
                    disabled={loading}
                  >
                    {loading ? 'Đang ghi lại...' : 'Ghi Lại Sửa Chữa'}
                  </button>
                  
                  <button 
                    className="btn btn-secondary"
                    onClick={handleReset}
                  >
                    Thẩm Định Tài Liệu Khác
                  </button>
                </div>
              </>
            ) : (
              <div className="no-errors">
                <p>✓ Tài liệu hợp lệ - không có lỗi phát hiện.</p>
                <button 
                  className="btn btn-secondary"
                  onClick={handleReset}
                >
                  Thẩm Định Tài Liệu Khác
                </button>
              </div>
            )}
          </div>
        );
      
      case 'complete':
        return (
          <div className="app-container complete-container">
            <div className="complete-message">
              <h1>✓ Hoàn Tất</h1>
              <p>Các sửa chữa đã được ghi lại thành công.</p>
              <button 
                className="btn btn-primary"
                onClick={handleReset}
              >
                Thẩm Định Tài Liệu Khác
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
      <ToastContainer />
      {renderStep()}
    </div>
  );
}

export default App;
