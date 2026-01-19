import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
      padding: '20px'
    }}>
      <div style={{
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <div style={{
          backgroundColor: 'white',
          padding: '32px',
          borderRadius: '12px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          marginBottom: '24px'
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <h1 style={{
                fontSize: '32px',
                fontWeight: 'bold',
                margin: '0 0 8px 0',
                color: '#1a1a1a'
              }}>
                Welcome, {user?.username}!
              </h1>
              <p style={{
                fontSize: '16px',
                color: '#666',
                margin: 0
              }}>
                MDA Portfolio Generator Dashboard
              </p>
            </div>
            <button
              onClick={handleLogout}
              style={{
                padding: '12px 24px',
                fontSize: '14px',
                fontWeight: '600',
                color: 'white',
                backgroundColor: '#EF4444',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.backgroundColor = '#DC2626'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#EF4444'}
            >
              Logout
            </button>
          </div>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '24px',
          marginBottom: '24px'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#666',
              margin: '0 0 8px 0',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Total Projects
            </h3>
            <p style={{
              fontSize: '36px',
              fontWeight: 'bold',
              color: '#1a1a1a',
              margin: 0
            }}>
              0
            </p>
          </div>

          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#666',
              margin: '0 0 8px 0',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Skills Identified
            </h3>
            <p style={{
              fontSize: '36px',
              fontWeight: 'bold',
              color: '#1a1a1a',
              margin: 0
            }}>
              0
            </p>
          </div>

          <div style={{
            backgroundColor: 'white',
            padding: '24px',
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
          }}>
            <h3 style={{
              fontSize: '14px',
              fontWeight: '600',
              color: '#666',
              margin: '0 0 8px 0',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Last Analysis
            </h3>
            <p style={{
              fontSize: '20px',
              fontWeight: '600',
              color: '#1a1a1a',
              margin: 0
            }}>
              Never
            </p>
          </div>
        </div>

        <div style={{
          backgroundColor: 'white',
          padding: '32px',
          borderRadius: '12px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          textAlign: 'center'
        }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: '#1a1a1a',
            margin: '0 0 16px 0'
          }}>
            Get Started
          </h2>
          <p style={{
            fontSize: '16px',
            color: '#666',
            margin: '0 0 24px 0'
          }}>
            Upload your first project to start building your portfolio
          </p>
          <button
            style={{
              padding: '14px 32px',
              fontSize: '16px',
              fontWeight: '600',
              color: 'white',
              backgroundColor: '#1a1a1a',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => e.target.style.backgroundColor = '#333'}
            onMouseLeave={(e) => e.target.style.backgroundColor = '#1a1a1a'}
          >
            Analyze New Project
          </button>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
