import { useState } from 'react';
import useStore from '../store';
import Icon from './Icon';

export default function Login() {
  const login = useStore(s => s.login);
  const signup = useStore(s => s.signup);
  const theme = useStore(s => s.theme);
  
  const [mode, setMode] = useState('login'); // 'login' or 'signup'
  const [name, setName] = useState('');
  const [role, setRole] = useState('store_manager');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    
    if (!email || !password) {
      setError('Please fill in all required fields.');
      return;
    }
    
    if (mode === 'login') {
      const success = login(email, password);
      if (!success) {
        setError('Invalid email or password. Intranet access denied.');
      }
    } else {
      if (password.length < 4) {
        setError('Password must be at least 4 characters.');
        return;
      }
      if (!name) {
        setError('Full Name is required for registration.');
        return;
      }
      const success = signup(email, password, name, role);
      if (success) {
        setSuccessMsg('Account created! You can now sign in.');
        setMode('login');
      } else {
        setError('Account with this email already exists.');
      }
    }
  };

  // Mock background pattern corresponding to the aesthetic
  const isDark = theme === 'dark';
  const bgColor = isDark ? '#0a0e1a' : '#f1f5f9';
  const cardBg = isDark ? 'rgba(17, 24, 39, 0.8)' : '#ffffff';
  const textColor = isDark ? '#f1f5f9' : '#0f172a';
  const mutedColor = isDark ? '#64748b' : '#64748b';

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: bgColor,
      fontFamily: 'var(--font-family)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Decorative background elements */}
      <div style={{
        position: 'absolute',
        top: '-10%',
        left: '-10%',
        width: '40%',
        height: '40%',
        background: 'radial-gradient(ellipse at center, rgba(37, 99, 235, 0.15), transparent 70%)',
        zIndex: 0
      }} />
      <div style={{
        position: 'absolute',
        bottom: '-10%',
        right: '-10%',
        width: '40%',
        height: '40%',
        background: 'radial-gradient(ellipse at center, rgba(8, 145, 178, 0.15), transparent 70%)',
        zIndex: 0
      }} />

      <div style={{
        background: cardBg,
        padding: '40px',
        borderRadius: '16px',
        boxShadow: 'var(--shadow-lg)',
        width: '100%',
        maxWidth: '400px',
        zIndex: 1,
        border: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.05)'}`,
        backdropFilter: 'blur(20px)'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginBottom: '32px' }}>
          <div style={{
            width: '48px',
            height: '48px',
            background: 'linear-gradient(135deg, #2563eb, #0891b2)',
            borderRadius: '12px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 800,
            fontSize: '24px',
            marginBottom: '16px',
            boxShadow: '0 4px 12px rgba(37, 99, 235, 0.3)'
          }}>
            SS
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: 800, color: textColor, margin: 0, textAlign: 'center' }}>
            Smart Store OS
          </h2>
          <p style={{ fontSize: '13px', color: mutedColor, marginTop: '4px' }}>
            {mode === 'login' ? 'Sign in to access live operations' : 'Register a new employee profile'}
          </p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.1)',
              color: '#ef4444',
              padding: '10px 12px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 600,
              border: '1px solid rgba(239, 68, 68, 0.2)'
            }}>
              {error}
            </div>
          )}
          {successMsg && (
            <div style={{
              background: 'rgba(34, 197, 94, 0.1)',
              color: '#22c55e',
              padding: '10px 12px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 600,
              border: '1px solid rgba(34, 197, 94, 0.2)'
            }}>
              {successMsg}
            </div>
          )}
          
          {mode === 'signup' && (
            <>
              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: textColor, marginBottom: '8px' }}>
                  Full Name
                </label>
                <input 
                  type="text" 
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="Jane Doe"
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '8px',
                    border: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : '#cbd5e1'}`,
                    background: isDark ? 'rgba(0,0,0,0.2)' : '#ffffff',
                    color: textColor,
                    fontSize: '14px',
                    outline: 'none',
                    fontFamily: 'inherit',
                    transition: 'border-color 0.2s, box-shadow 0.2s'
                  }}
                  onFocus={e => {
                    e.target.style.borderColor = '#2563eb';
                    e.target.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.15)';
                  }}
                  onBlur={e => {
                    e.target.style.borderColor = isDark ? 'rgba(255,255,255,0.1)' : '#cbd5e1';
                    e.target.style.boxShadow = 'none';
                  }}
                />
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: textColor, marginBottom: '8px' }}>
                  Assign Role
                </label>
                <select 
                  value={role}
                  onChange={e => setRole(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px',
                    borderRadius: '8px',
                    border: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : '#cbd5e1'}`,
                    background: isDark ? 'rgba(0,0,0,0.2)' : '#ffffff',
                    color: textColor,
                    fontSize: '14px',
                    outline: 'none',
                    fontFamily: 'inherit',
                    cursor: 'pointer'
                  }}
                >
                  <option value="admin">Administrator</option>
                  <option value="store_manager">Store Manager</option>
                  <option value="cashier">Cashier</option>
                  <option value="lp_officer">LP Officer</option>
                </select>
              </div>
            </>
          )}

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: textColor, marginBottom: '8px' }}>
              Corporate Email
            </label>
            <input 
              type="email" 
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="user@smartstore.com"
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                border: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : '#cbd5e1'}`,
                background: isDark ? 'rgba(0,0,0,0.2)' : '#ffffff',
                color: textColor,
                fontSize: '14px',
                outline: 'none',
                fontFamily: 'inherit',
                transition: 'border-color 0.2s, box-shadow 0.2s'
              }}
              onFocus={e => {
                e.target.style.borderColor = '#2563eb';
                e.target.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.15)';
              }}
              onBlur={e => {
                e.target.style.borderColor = isDark ? 'rgba(255,255,255,0.1)' : '#cbd5e1';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, color: textColor, marginBottom: '8px' }}>
              Password
            </label>
            <input 
              type="password" 
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="••••••••"
              style={{
                width: '100%',
                padding: '12px 14px',
                borderRadius: '8px',
                border: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : '#cbd5e1'}`,
                background: isDark ? 'rgba(0,0,0,0.2)' : '#ffffff',
                color: textColor,
                fontSize: '14px',
                outline: 'none',
                fontFamily: 'inherit',
                transition: 'border-color 0.2s, box-shadow 0.2s'
              }}
              onFocus={e => {
                e.target.style.borderColor = '#2563eb';
                e.target.style.boxShadow = '0 0 0 3px rgba(37, 99, 235, 0.15)';
              }}
              onBlur={e => {
                e.target.style.borderColor = isDark ? 'rgba(255,255,255,0.1)' : '#cbd5e1';
                e.target.style.boxShadow = 'none';
              }}
            />
          </div>

          <button type="submit" style={{
            width: '100%',
            padding: '14px',
            background: '#2563eb',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            fontSize: '14px',
            fontWeight: 700,
            cursor: 'pointer',
            marginTop: '8px',
            transition: 'background 0.2s',
            boxShadow: '0 4px 6px rgba(37, 99, 235, 0.2)'
          }} onMouseOver={e => e.target.style.background = '#1d4ed8'} onMouseOut={e => e.target.style.background = '#2563eb'}>
            {mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div style={{ marginTop: '24px', textAlign: 'center', fontSize: '13px', color: mutedColor }}>
          {mode === 'login' ? (
            <>
              Don't have an account?{' '}
              <button 
                onClick={() => { setMode('signup'); setError(''); setSuccessMsg(''); }}
                style={{ background: 'none', border: 'none', color: '#2563eb', fontWeight: 600, cursor: 'pointer', padding: 0 }}
              >
                Sign up
              </button>
            </>
          ) : (
            <>
              Already have an account?{' '}
              <button 
                onClick={() => { setMode('login'); setError(''); setSuccessMsg(''); }}
                style={{ background: 'none', border: 'none', color: '#2563eb', fontWeight: 600, cursor: 'pointer', padding: 0 }}
              >
                Sign in
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
