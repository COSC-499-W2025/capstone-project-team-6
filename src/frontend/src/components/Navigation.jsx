import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';

const Navigation = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    {
      label: 'Dashboard',
      path: '/dashboard',
      icon: '🏠'
    },
    {
      label: 'Upload',
      path: '/upload',
      icon: '📤'
    },
    {
      label: 'Projects',
      path: '/projects',
      icon: '📁'
    },
    {
      label: 'Curate',
      path: '/curate',
      icon: '✨'
    },
    {
      label: 'Portfolio',
      path: '/portfolio',
      icon: '🎨'
    },
    {
      label: 'Resume',
      path: '/resume',
      icon: '📄'
    },
    {
      label: 'Job Match',
      path: '/job-match',
      icon: '🎯'
    },
    {
      label: 'Settings',
      path: '/settings',
      icon: '⚙️'
    },
  ];

  return (
    <nav style={{
      backgroundColor: 'white',
      padding: '16px 32px',
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      borderBottom: '1px solid #e5e5e5',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '48px',
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: '#1a1a1a',
          fontSize: '18px',
          fontWeight: '600',
        }}>
          <span>📁</span>
          <span>MDA Portfolio</span>
        </div>

        <div style={{
          display: 'flex',
          gap: '4px',
        }}>
          {navItems.map((item) => (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                padding: '10px 16px',
                backgroundColor: location.pathname === item.path ? '#1a1a1a' : 'transparent',
                color: location.pathname === item.path ? 'white' : '#666',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
              }}
              onMouseEnter={(e) => {
                if (location.pathname !== item.path) {
                  e.currentTarget.style.backgroundColor = '#f5f5f5';
                  e.currentTarget.style.color = '#1a1a1a';
                }
              }}
              onMouseLeave={(e) => {
                if (location.pathname !== item.path) {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#666';
                }
              }}
            >
              <span>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
