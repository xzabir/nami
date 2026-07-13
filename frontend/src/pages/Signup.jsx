import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { apiRequest, setToken, getToken } from '../api';

export default function Signup() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const [successMsg, setSuccessMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (getToken()) navigate('/dashboard');
  }, [navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    setSuccessMsg('');
    setLoading(true);

    try {
      const result = await apiRequest('/auth/signup', {
        method: 'POST',
        auth: false,
        body: { email, password, full_name: fullName || null },
      });
      setToken(result.access_token);
      setSuccessMsg('Success — redirecting…');
      navigate('/dashboard');
    } catch (err) {
      setErrorMsg(err.message || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="brand"><span className="dot"></span> Nami</div>
        <h1>Create an account</h1>
        <p className="sub">Start captioning your clips</p>

        {errorMsg && <div className="form-msg error">{errorMsg}</div>}
        {successMsg && <div className="form-msg success">{successMsg}</div>}

        <form onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="fullName">Name (optional)</label>
            <input 
              type="text" 
              id="fullName" 
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="email">Email</label>
            <input 
              type="email" 
              id="email" 
              required 
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="field">
            <label htmlFor="password">Password</label>
            <input 
              type="password" 
              id="password" 
              required 
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary btn-block" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>

        <div className="auth-switch">
          Already have an account? <Link to="/login">Log in</Link>
        </div>
      </div>
    </div>
  );
}
