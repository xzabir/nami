import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiRequest, clearToken } from '../api';

const STYLE_LABELS = {
  formal: 'Formal',
  sarcastic: 'Sarcastic',
  humorous_tech: 'Humorous · Tech',
  humorous_non_tech: 'Humorous · Non-tech',
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [userEmail, setUserEmail] = useState('');
  const [jobs, setJobs] = useState([]);
  const [videoUrl, setVideoUrl] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [submitError, setSubmitError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const fileInputRef = useRef(null);

  // Load User
  useEffect(() => {
    apiRequest('/auth/me')
      .then(user => setUserEmail(user.email))
      .catch(() => {
        clearToken();
        navigate('/login');
      });
  }, [navigate]);

  // Initial fetch
  useEffect(() => {
    apiRequest('/captions')
      .then(setJobs)
      .catch(console.error);
  }, []);

  // Polling Jobs
  useEffect(() => {
    const hasActive = jobs.some(j => j.status === 'pending' || j.status === 'processing');
    if (!hasActive) return;

    const timer = setInterval(() => {
      apiRequest('/captions')
        .then(setJobs)
        .catch(console.error);
    }, 4000);

    return () => clearInterval(timer);
  }, [jobs]);

  const handleLogout = () => {
    clearToken();
    navigate('/login');
  };

  const handleFileClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setVideoUrl('');
    } else {
      setSelectedFile(null);
    }
  };

  const handleUrlChange = (e) => {
    setVideoUrl(e.target.value);
    if (e.target.value.trim()) {
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async () => {
    setSubmitError('');
    if (!videoUrl.trim() && !selectedFile) {
      setSubmitError('Choose a video file or enter a video URL first.');
      return;
    }

    setIsSubmitting(true);
    try {
      if (selectedFile) {
        const formData = new FormData();
        formData.append('file', selectedFile);
        await apiRequest('/captions/upload', { method: 'POST', body: formData });
        
        setSelectedFile(null);
        if (fileInputRef.current) fileInputRef.current.value = '';
      } else {
        await apiRequest('/captions', { method: 'POST', body: { video_url: videoUrl } });
        setVideoUrl('');
      }
      
      // Instantly trigger a refresh instead of waiting for the poll
      const newJobs = await apiRequest('/captions');
      setJobs(newJobs);
    } catch (err) {
      setSubmitError(err.message || 'Could not submit clip.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCancel = async (jobId) => {
    try {
      await apiRequest(`/captions/${jobId}/cancel`, { method: 'POST' });
      const newJobs = await apiRequest('/captions');
      setJobs(newJobs);
    } catch (err) {
      alert(err.message || 'Could not cancel job.');
    }
  };

  const handleDelete = async (jobId) => {
    if (!window.confirm('Are you sure you want to delete this clip and its captions?')) return;
    try {
      await apiRequest(`/captions/${jobId}`, { method: 'DELETE' });
      const newJobs = await apiRequest('/captions');
      setJobs(newJobs);
    } catch (err) {
      alert(err.message || 'Could not delete job.');
    }
  };

  const getStatusLabel = (status) => {
    if (status === 'pending') return <><span className="spinner"></span>Queued</>;
    if (status === 'processing') return <><span className="spinner"></span>Captioning</>;
    if (status === 'done') return 'Done';
    if (status === 'failed') return 'Failed';
    if (status === 'cancelled') return 'Cancelled';
    return status;
  };

  return (
    <>
      <div className="dash-header">
        <div className="brand"><span className="dot"></span> Nami</div>
        <div className="nav-links">
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.8rem', color: 'var(--paper-dim)' }}>
            {userEmail}
          </span>
          <button className="btn btn-ghost" onClick={handleLogout}>Log out</button>
        </div>
      </div>

      <main className="dash-body">
        <section className="submit-panel">
          <h2>Submit a clip</h2>
          <p className="hint">Upload a video from your device or paste a direct video URL (30s–2min works best). Fireworks AI will sample frames and write all four styles in one pass.</p>
          
          {submitError && <div className="form-msg error">{submitError}</div>}
          
          <div className="submit-row upload-container">
            <div className="input-group">
              <input 
                type="url" 
                placeholder="https://storage.example.com/clips/clip1.mp4" 
                value={videoUrl}
                onChange={handleUrlChange}
              />
              <span className="or-separator">OR</span>
              <button type="button" className="btn btn-ghost file-label" onClick={handleFileClick}>
                <span className="file-icon">📁</span> Choose File
              </button>
              <input 
                type="file" 
                accept="video/*" 
                style={{ display: 'none' }} 
                ref={fileInputRef}
                onChange={handleFileChange}
              />
              <span className="file-name-display">
                {selectedFile ? selectedFile.name : 'No file chosen'}
              </span>
            </div>
            <button className="btn btn-primary" onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? 'Submitting…' : 'Generate captions'}
            </button>
          </div>
        </section>

        <div className="jobs-head">
          <h2>Your clips</h2>
          <span>{jobs.length} clip{jobs.length !== 1 && 's'}</span>
        </div>

        <div>
          {jobs.length === 0 ? (
            <div className="empty-state">
              <h3>No clips yet</h3>
              <p>Upload a video or paste a URL above to get your first four takes.</p>
            </div>
          ) : (
            jobs.map(job => (
              <div key={job.id} className="job-card">
                <div className="job-top">
                  <div className="job-url">{job.video_url}</div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span className={`status-pill status-${job.status}`}>
                      {getStatusLabel(job.status)}
                    </span>
                    {(job.status === 'pending' || job.status === 'processing') ? (
                      <button className="btn btn-ghost btn-xs cancel-btn" onClick={() => handleCancel(job.id)}>Stop</button>
                    ) : (
                      <button className="btn btn-ghost btn-xs delete-btn" style={{ color: 'var(--rec)', borderColor: 'rgba(194,91,69,0.3)' }} onClick={() => handleDelete(job.id)}>Delete</button>
                    )}
                  </div>
                </div>
                
                {job.captions && (
                  <div className="caption-grid">
                    {Object.entries(job.captions).map(([style, text]) => (
                      <div key={style} className="caption-item">
                        <div className="tag">{STYLE_LABELS[style] || style}</div>
                        <div className="text">{text || <span style={{ color: 'var(--paper-dim)' }}>No caption generated</span>}</div>
                      </div>
                    ))}
                  </div>
                )}
                
                {job.error && (
                  <p style={{ marginTop: '12px', fontSize: '0.85rem', color: '#E8998A' }}>{job.error}</p>
                )}
              </div>
            ))
          )}
        </div>
      </main>
    </>
  );
}
