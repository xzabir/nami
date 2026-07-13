import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiRequest } from '../api';

export default function Signup() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    try {
      await apiRequest('/auth/register', {
        method: 'POST',
        body: { email, password }
      });
      setSuccess('Account created! You can now log in.');
      setTimeout(() => navigate('/login'), 2000);
    } catch (err) {
      setError(err.message || 'Sign up failed');
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
        
        <h1 className="text-center text-2xl mb-2">Create an account</h1>
        <p className="text-center text-sm text-muted mb-8">Get started with Nami</p>

        {error && <div className="mb-6 text-sm text-center p-3 rounded" style={{ background: 'var(--danger-bg)', color: 'var(--danger)' }}>{error}</div>}
        {success && <div className="mb-6 text-sm text-center p-3 rounded" style={{ background: 'var(--success-bg)', color: 'var(--success)' }}>{success}</div>}

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
              minLength={4}
            />
          </div>
          
          <button type="submit" className="btn btn-primary mt-2">Sign Up</button>
        </form>

        <div className="text-center mt-6 text-sm text-muted">
          Already have an account? <Link to="/login" style={{ fontWeight: '500' }}>Log in</Link>
        </div>
      </div>
    </div>
  );
}
