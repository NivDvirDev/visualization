import React, { useState, useCallback } from 'react';
import { GoogleOAuthProvider, GoogleLogin, CredentialResponse } from '@react-oauth/google';
import { login, register, googleLogin } from '../../../api';
import { User } from '../../../types';
import { WellspringLogo } from '../../brand/WellspringLogo/WellspringLogo';
import './LoginPage.css';

interface LoginPageProps {
  onLogin: (user: User, token: string) => void;
  googleClientId: string | null;
}

const LoginPage: React.FC<LoginPageProps> = ({ onLogin, googleClientId }) => {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (mode === 'register') {
        if (!username.trim()) {
          setError('Username is required');
          setLoading(false);
          return;
        }
        const { user, token } = await register(username.trim(), email.trim(), password);
        onLogin(user, token);
      } else {
        const { user, token } = await login(email.trim(), password);
        onLogin(user, token);
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
      setLoading(false);
    }
  }, [mode, username, email, password, onLogin]);

  const handleGoogleSuccess = useCallback(async (response: CredentialResponse) => {
    if (!response.credential) {
      setError('Google sign-in failed: no credential received');
      return;
    }
    setError('');
    setLoading(true);
    try {
      const { user, token } = await googleLogin(response.credential);
      onLogin(user, token);
    } catch (err: any) {
      setError(err.message || 'Google sign-in failed');
      setLoading(false);
    }
  }, [onLogin]);

  const handleGoogleError = useCallback(() => {
    setError('Google sign-in was cancelled or failed');
  }, []);

  const toggleMode = useCallback(() => {
    setMode((m) => (m === 'login' ? 'register' : 'login'));
    setError('');
  }, []);

  return (
    <div className="login-page">
      <div className="login-card">
        <WellspringLogo size={80} className="login-logo" />
        <h1 className="login-title">The Wellspring</h1>
        <p className="login-tagline">
          Rate audio visualizations. Earn badges. Compete globally.<br />
          Your ratings help train AI to understand visual music.
        </p>
        <p className="login-subtitle">
          {mode === 'login' ? 'Sign in to start rating' : 'Create your account'}
        </p>

        {googleClientId && (
          <GoogleOAuthProvider clientId={googleClientId}>
            <div className="google-signin-section">
              <div className="google-btn-wrapper">
                <GoogleLogin
                  onSuccess={handleGoogleSuccess}
                  onError={handleGoogleError}
                  size="large"
                  width="336"
                  text={mode === 'login' ? 'signin_with' : 'signup_with'}
                  theme="filled_black"
                  shape="rectangular"
                />
              </div>
              <div className="login-divider">
                <span className="login-divider-line" />
                <span className="login-divider-text">or</span>
                <span className="login-divider-line" />
              </div>
            </div>
          </GoogleOAuthProvider>
        )}

        <form onSubmit={handleSubmit} className="login-form">
          {mode === 'register' && (
            <div className="login-field">
              <label htmlFor="username">Username</label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Choose a username"
                autoComplete="username"
              />
            </div>
          )}

          <div className="login-field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
            />
          </div>

          <div className="login-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={mode === 'register' ? 'Min 6 characters' : 'Your password'}
              autoComplete={mode === 'register' ? 'new-password' : 'current-password'}
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="btn btn-login" disabled={loading}>
            {loading ? 'Please wait...' : mode === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        <div className="login-switch">
          {mode === 'login' ? (
            <span>
              Don't have an account?{' '}
              <button className="login-link" onClick={toggleMode}>
                Register
              </button>
            </span>
          ) : (
            <span>
              Already have an account?{' '}
              <button className="login-link" onClick={toggleMode}>
                Sign In
              </button>
            </span>
          )}
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
