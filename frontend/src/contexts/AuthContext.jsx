import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { AuthContext } from './authState';

const decodeJwtPayload = (token) => {
  try {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map((c) => `%${`00${c.charCodeAt(0).toString(16)}`.slice(-2)}`)
        .join('')
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = () => {
      const token = localStorage.getItem('token');
      const userJson = localStorage.getItem('user');

      if (token) {
        try {
          if (userJson) {
            setUser(JSON.parse(userJson));
          } else {
            const payload = decodeJwtPayload(token);
            const fallbackUser = {
              id: payload?.uid || null,
              username: payload?.sub || 'admin',
              role: payload?.role || 'admin',
            };
            localStorage.setItem('user', JSON.stringify(fallbackUser));
            setUser(fallbackUser);
          }
        } catch (e) {
          console.error('Failed to restore auth state', e);
          localStorage.removeItem('token');
          localStorage.removeItem('user');
        }
      }
      setLoading(false);
    };

    initializeAuth();
  }, []);

  const login = async (credentials) => {
    setLoading(true);
    try {
      const response = await api.post('/auth/token', {
        username: credentials.username,
        password: credentials.password,
      });

      const token = response.data.access_token;
      const payload = decodeJwtPayload(token);
      const userData = {
        id: payload?.uid || null,
        username: payload?.sub || credentials.username,
        role: payload?.role || 'admin',
      };

      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(userData));
      setUser(userData);
    } catch (error) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await api.post('/auth/logout');
    } catch (error) {
      console.warn('Logout request failed, clearing local session anyway', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
      window.location.href = '/login';
    }
  };

  if (loading) {
    return null;
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};