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

  const getStatusBadge = (status) => {
    if (status === 'pending') return <span className="badge badge-neutral"><span className="spinner" style={{ width: '10px', height: '10px', marginRight: '6px' }}></span>Queued</span>;
    if (status === 'processing') return <span className="badge badge-neutral" style={{ borderColor: 'var(--accent)', color: 'var(--accent)' }}><span className="spinner" style={{ width: '10px', height: '10px', marginRight: '6px' }}></span>Captioning</span>;
    if (status === 'done') return <span className="badge badge-success">Done</span>;
    if (status === 'failed') return <span className="badge badge-danger">Failed</span>;
    if (status === 'cancelled') return <span className="badge badge-neutral">Cancelled</span>;
    return <span className="badge badge-neutral">{status}</span>;
  };

  return (
    <>
      <nav className="nav container mb-8">
        <div className="flex items-center justify-between">
          <div className="brand">
            <span className="dot"></span> Nami
          </div>
          <div className="flex items-center gap-6">
            <span className="font-mono text-xs text-muted">
              {userEmail}
            </span>
            <button className="btn btn-ghost text-sm" onClick={handleLogout}>Log out</button>
          </div>
        </div>
      </nav>

      <main className="container">
        <section className="card mb-12">
          <h2>Submit a clip</h2>
          <p className="text-muted text-sm mb-6">
            Upload a video from your device or paste a direct video URL (30s–2min works best). Fireworks AI will sample frames and write all four styles in one pass.
          </p>
          
          {submitError && <div className="mb-4 text-sm" style={{ color: 'var(--danger)' }}>{submitError}</div>}
          
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-4 flex-wrap">
              <input 
                type="url" 
                className="input flex-1"
                placeholder="https://storage.example.com/clips/clip1.mp4" 
                value={videoUrl}
                onChange={handleUrlChange}
              />
              <span className="font-mono text-xs uppercase text-muted">OR</span>
              <button type="button" className="btn btn-outline" onClick={handleFileClick}>
                Choose File
              </button>
              <input 
                type="file" 
                accept="video/*" 
                style={{ display: 'none' }} 
                ref={fileInputRef}
                onChange={handleFileChange}
              />
              {selectedFile && (
                <span className="font-mono text-xs text-muted truncate" style={{ maxWidth: '200px' }}>
                  {selectedFile.name}
                </span>
              )}
            </div>
            <button className="btn btn-primary" style={{ alignSelf: 'flex-start' }} onClick={handleSubmit} disabled={isSubmitting}>
              {isSubmitting ? 'Submitting…' : 'Generate captions'}
            </button>
          </div>
        </section>

        <div className="flex justify-between items-baseline mb-6">
          <h2>Your clips</h2>
          <span className="font-mono text-xs text-muted">{jobs.length} clip{jobs.length !== 1 && 's'}</span>
        </div>

        <div className="flex flex-col gap-6">
          {jobs.length === 0 ? (
            <div className="card text-center py-12" style={{ borderStyle: 'dashed' }}>
              <h3 className="mb-2">No clips yet</h3>
              <p className="text-muted text-sm">Upload a video or paste a URL above to get your first four takes.</p>
            </div>
          ) : (
            jobs.map(job => (
              <div key={job.id} className="card" style={{ padding: '24px' }}>
                <div className="flex justify-between items-start flex-wrap gap-4 mb-6">
                  <div className="font-mono text-sm" style={{ wordBreak: 'break-all', maxWidth: '70ch' }}>
                    {job.video_url}
                  </div>
                  <div className="flex items-center gap-3">
                    {getStatusBadge(job.status)}
                    {(job.status === 'pending' || job.status === 'processing') ? (
                      <button className="btn btn-ghost text-xs py-1 px-2" onClick={() => handleCancel(job.id)}>Stop</button>
                    ) : (
                      <button className="btn btn-ghost text-xs py-1 px-2" style={{ color: 'var(--danger)' }} onClick={() => handleDelete(job.id)}>Delete</button>
                    )}
                  </div>
                </div>
                
                {job.captions && (
                  <div className="grid grid-cols-2 gap-4">
                    {Object.entries(job.captions).map(([style, text]) => (
                      <div key={style} className="p-4 rounded-lg" style={{ background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px' }}>
                        <div className="font-mono text-xs uppercase mb-2" style={{ color: 'var(--accent)', letterSpacing: '0.05em' }}>
                          {STYLE_LABELS[style] || style}
                        </div>
                        <div className="text-sm">
                          {text || <span className="text-muted">No caption generated</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
                
                {job.error && (
                  <p className="mt-4 text-sm" style={{ color: 'var(--danger)' }}>{job.error}</p>
                )}
              </div>
            ))
          )}
        </div>
      </main>
    </>
  );
}
