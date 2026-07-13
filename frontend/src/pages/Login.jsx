import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiRequest, setToken } from '../api';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', email);
      formData.append('password', password);

      const res = await apiRequest('/auth/token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });
      
      setToken(res.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.message || 'Login failed');
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen px-4" style={{ minHeight: '100vh' }}>
      <div className="card w-full" style={{ maxWidth: '400px' }}>
        <div className="flex justify-center mb-6">
          <div className="brand">
            <span className="dot"></span> Nami
          </div>
        </div>
        
        <h1 className="text-center text-2xl mb-2">Welcome back</h1>
        <p className="text-center text-sm text-muted mb-8">Sign in to your account</p>

        {error && <div className="mb-6 text-sm text-center p-3 rounded" style={{ background: 'var(--danger-bg)', color: 'var(--danger)' }}>{error}</div>}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="label">Email address</label>
            <input 
              type="email" 
              className="input"
              value={email} 
              onChange={e => setEmail(e.target.value)} 
              required 
            />
          </div>
          <div>
            <label className="label">Password</label>
            <input 
              type="password" 
              className="input"
              value={password} 
              onChange={e => setPassword(e.target.value)} 
              required 
            />
          </div>
          
          <button type="submit" className="btn btn-primary mt-2">Sign In</button>
        </form>

        <div className="text-center mt-6 text-sm text-muted">
          Don't have an account? <Link to="/signup" style={{ fontWeight: '500' }}>Sign up</Link>
        </div>
      </div>
    </div>
  );
}
