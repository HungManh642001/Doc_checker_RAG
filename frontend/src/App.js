import React from 'react';
import './App.css';
import DocumentUpload from './components/DocumentUpload';
import DocumentPreview from './components/DocumentPreview';
import ErrorViewer from './components/ErrorViewer';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';


function App() {
  const [sessionId, setSessionId] = React.useState(null);
  const [step, setStep] = React.useState('upload'); // 'upload', 'preview', 'review', 'edit'
  const [errors, setErrors] = React.useState([]);
  const [documentContent, setDocumentContent] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [errorStatus, setErrorStatus] = React.useState({}); // Track status of each error

  const handleUploadComplete = (newSessionId) => {
    setSessionId(newSessionId);
    setStep('preview');
  };

  const handleAnalyzeComplete = (analysisErrors) => {
    setErrors(analysisErrors);
    setStep('review');
  };

  const handleErrorStatusChange = (errorId, status, value) => {
    setErrorStatus(prev => ({
      ...prev,
      [errorId]: { status, value }
    }));
  };

  const handlePreviewClose = () => {
    setStep('review');
  };

  const handleBackToPreview = () => {
    setStep('preview');
  };

  const loadDocumentContent = async (sessionIdParam) => {
    try {
      const res = await fetch(`/api/document/${sessionIdParam}`);
      const data = await res.json();
      setDocumentContent(data.content);
    } catch (err) {
      console.error('Error loading document:', err);
    }
  };

  // Load document content when entering preview step
  React.useEffect(() => {
    if (step === 'preview' && sessionId && !documentContent) {
      loadDocumentContent(sessionId);
    }
  }, [step, sessionId]);

  // Auto-analyze when document is loaded
  React.useEffect(() => {
    if (step === 'preview' && documentContent && sessionId) {
      setLoading(true);
      fetch(`/api/analyze/${sessionId}`, { method: 'POST' })
        .then(res => res.json())
        .then(data => {
          setErrors(data.errors);
          setLoading(false);
          setStep('preview');
        })
        .catch(err => {
          console.error('Error analyzing:', err);
          setLoading(false);
        });
    }
  }, [documentContent]);

  const handleApplySuggestions = (acceptedErrors) => {
    setLoading(true);
    
    // Filter errors based on status from preview: only apply accepted/edited, skip rejected
    const applicableErrors = acceptedErrors.map(err => {
      const errStatus = errorStatus[err.id];
      if (errStatus && errStatus.status === 'rejected') {
        return null; // Skip rejected errors
      }
      return {
        ...err,
        fixedValue: errStatus?.value || err.suggestion // Use custom value if edited
      };
    }).filter(Boolean);

    fetch(`/api/apply-suggestions/${sessionId}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        acceptedSuggestions: applicableErrors
      })
    })
    .then(res => res.json())
    .then(data => {
      setLoading(false);
      if (data.downloadUrl) {
        window.location.href = data.downloadUrl;
        setStep('complete');
      }
    })
    .catch(err => {
      setLoading(false);
      console.error(err);
    });
  };

  const handleReset = () => {
    setSessionId(null);
    setStep('upload');
    setErrors([]);
    setDocumentContent(null);
    localStorage.removeItem('contentUpdates');
  };

  const handleSaveAndReupload = async () => {
    if (!sessionId) return;
    
    setLoading(true);
    try {
      const contentUpdates = JSON.parse(localStorage.getItem('contentUpdates') || '{}');
      
      const res = await fetch(`/api/save-and-reupload/${sessionId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ contentUpdates })
      });
      
      const data = await res.json();
      setErrors(data.errors || []);
      setDocumentContent({ ...documentContent, paragraphs: data.content?.paragraphs || documentContent.paragraphs });
      setLoading(false);
      
      alert(`Tái thẩm định hoàn tất! Phát hiện ${data.errors?.length || 0} lỗi mới.`);
    } catch (err) {
      setLoading(false);
      console.error('Error reupload:', err);
      alert('Lỗi khi tái thẩm định: ' + err.message);
    }
  };

  return (
    <div className="App">
      <header className="app-header">
        <h1>📄 Hệ thống Thẩm định Tài liệu</h1>
        <p>Phát hiện lỗi, đề xuất sửa chữa, và viện dẫn sở cứ</p>
      </header>

      <main className="app-container">
        {step === 'upload' && (
          <DocumentUpload 
            onUploadComplete={handleUploadComplete}
          />
        )}

        {step === 'preview' && documentContent && (
          <DocumentPreview 
            content={documentContent}
            errors={errors}
            sessionId={sessionId}
            onClose={() => setStep('review')}
            onErrorStatusChange={handleErrorStatusChange}
          />
        )}

        {step === 'review' && (
          <ErrorViewer 
            errors={errors}
            sessionId={sessionId}
            onApplySuggestions={handleApplySuggestions}
            onReset={handleReset}
            loading={loading}
            onPreview={handleBackToPreview}
            onReupload={handleSaveAndReupload}
          />
        )}

        {step === 'complete' && (
          <div className="completion-screen">
            <div className="success-message">
              <h2>✓ Tài liệu đã được xử lý thành công!</h2>
              <p>File đã được tải về với tất cả các sửa chữa được chấp nhận.</p>
              <button className="btn btn-primary" onClick={handleReset}>
                ← Xử lý tài liệu mới
              </button>
            </div>
          </div>
        )}
      </main>

      <ToastContainer 
        position="bottom-right"
        autoClose={3000}
        newestOnTop={true}
      />
    </div>
  );
}

export default App;
