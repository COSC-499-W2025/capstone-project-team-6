import React, { createContext, useState, useContext, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in and token is not expired
    const token = localStorage.getItem('access_token');
    const username = localStorage.getItem('username');
    const tokenExpiry = localStorage.getItem('token_expiry');

    let logoutTimer;

    if (token && username && tokenExpiry) {
      const expiryDate = new Date(tokenExpiry);
      const now = new Date();

      if (now < expiryDate) {
        // Token is still valid
        setUser({ username, token });

        // Set up auto-logout when token expires
        const timeUntilExpiry = expiryDate.getTime() - now.getTime();
        logoutTimer = setTimeout(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('username');
          localStorage.removeItem('token_expiry');
          setUser(null);
          window.location.href = '/login';
        }, timeUntilExpiry);
      } else {
        // Token expired, clear storage
        localStorage.removeItem('access_token');
        localStorage.removeItem('username');
        localStorage.removeItem('token_expiry');
      }
    }

    setLoading(false);

    // Cleanup timer on unmount
    return () => {
      if (logoutTimer) {
        clearTimeout(logoutTimer);
      }
    };
  }, []);

  const login = async (username, password) => {
    try {
      const data = await authAPI.login(username, password);
      // Token expires in 24 hours (matching backend)
      const expiryDate = new Date();
      expiryDate.setHours(expiryDate.getHours() + 24);

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('username', data.username);
      localStorage.setItem('token_expiry', expiryDate.toISOString());
      setUser({ username: data.username, token: data.access_token });
      return { success: true };
    } catch (error) {
      console.error('Login error:', error);
      let message = 'Login failed';
      if (error.response?.data?.detail) {
        message = error.response.data.detail;
      } else if (error.message) {
        message = error.message.includes('Network Error')
          ? 'Cannot connect to server. Please ensure the backend is running on http://localhost:8000'
          : error.message;
      }
      return { success: false, error: message };
    }
  };

  const signup = async (username, password) => {
    try {
      const data = await authAPI.signup(username, password);
      // Token expires in 24 hours (matching backend)
      const expiryDate = new Date();
      expiryDate.setHours(expiryDate.getHours() + 24);

      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('username', data.username);
      localStorage.setItem('token_expiry', expiryDate.toISOString());
      setUser({ username: data.username, token: data.access_token });
      return { success: true };
    } catch (error) {
      console.error('Signup error:', error);
      let message = 'Signup failed';
      if (error.response?.data?.detail) {
        message = error.response.data.detail;
      } else if (error.message) {
        message = error.message.includes('Network Error')
          ? 'Cannot connect to server. Please ensure the backend is running on http://localhost:8000'
          : error.message;
      }
      return { success: false, error: message };
    }
  };

  const logout = async () => {
    try {
      await authAPI.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      localStorage.removeItem('token_expiry');
      setUser(null);
    }
  };

  const value = {
    user,
    login,
    signup,
    logout,
    isAuthenticated: !!user,
  };

  if (loading) {
    return <div>Loading...</div>;
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
