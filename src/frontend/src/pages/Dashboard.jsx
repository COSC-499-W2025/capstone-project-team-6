import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import { projectsAPI } from '../services/api';
import api from '../services/api';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    totalProjects: 0,
    analyzedProjects: 0,
    totalLinesOfCode: 0,
    skillsDetected: 0,
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch projects data
        const projectsResponse = await projectsAPI.getProjects();
        const projects = projectsResponse.projects || [];

        // Fetch skills data
        const skillsResponse = await api.get('/skills');
        const totalSkills = skillsResponse.data.total_skills || 0;

        // Calculate total lines of code
        let totalLines = 0;
        projects.forEach(project => {
          const metadata = project.metadata || {};
          totalLines += metadata.total_lines || 0;
        });

        setStats({
          totalProjects: projects.length,
          analyzedProjects: projects.length,
          totalLinesOfCode: totalLines,
          skillsDetected: totalSkills,
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };

    fetchDashboardData();
  }, []);

  const quickActions = [
    {
      title: 'Upload Project',
      description: 'Analyze a new project',
      icon: '📤',
      onClick: () => navigate('/upload'),
    },
    {
      title: 'View Projects',
      description: `${stats.totalProjects} projects`,
      icon: '📁',
      onClick: () => navigate('/projects'),
    },
    {
      title: 'Generate Portfolio',
      description: 'Create your showcase',
      icon: '🎨',
      onClick: () => navigate('/portfolio'),
    },
    {
      title: 'Generate Resume',
      description: 'Build your CV',
      icon: '📄',
      onClick: () => navigate('/resume'),
    },
  ];

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#fafafa',
    }}>
      <Navigation />

      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        padding: '48px 32px'
      }}>
        <div style={{
          marginBottom: '48px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
        }}>
          <div>
            <h1 style={{
              fontSize: '36px',
              fontWeight: '600',
              margin: '0 0 12px 0',
              color: '#1a1a1a',
              letterSpacing: '-0.5px'
            }}>
              Welcome back, {user?.username}!
            </h1>
            <p style={{
              fontSize: '16px',
              color: '#737373',
              margin: 0
            }}>
              Manage your projects and generate professional portfolios
            </p>
          </div>
          <button
            onClick={async () => {
              await logout();
              navigate('/login');
            }}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              backgroundColor: 'white',
              color: '#1a1a1a',
              border: '1px solid #e5e5e5',
              borderRadius: '8px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '500',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = '#f5f5f5';
              e.currentTarget.style.borderColor = '#d4d4d4';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'white';
              e.currentTarget.style.borderColor = '#e5e5e5';
            }}
          >
            <span>↗</span>
            <span>Logout</span>
          </button>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '20px',
          marginBottom: '56px'
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '28px',
            borderRadius: '16px',
            border: '1px solid #e5e5e5',
            display: 'flex',
            flexDirection: 'column',
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '16px'
            }}>
              <h3 style={{
                fontSize: '14px',
                fontWeight: '500',
                color: '#737373',
                margin: 0,
              }}>
                Total Projects
              </h3>
              <span style={{
                fontSize: '18px',
                opacity: 0.4
              }}>📁</span>
            </div>
            <p style={{
              fontSize: '40px',
              fontWeight: '600',
              color: '#1a1a1a',
              margin: 0,
              letterSpacing: '-1px'
            }}>
              {stats.totalProjects}
            </p>
          </div>

          <div style={{
            backgroundColor: 'white',
            padding: '28px',
            borderRadius: '16px',
            border: '1px solid #e5e5e5',
            display: 'flex',
            flexDirection: 'column',
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '16px'
            }}>
              <h3 style={{
                fontSize: '14px',
                fontWeight: '500',
                color: '#737373',
                margin: 0,
              }}>
                Analyzed Projects
              </h3>
              <span style={{
                fontSize: '18px',
                opacity: 0.4
              }}>📊</span>
            </div>
            <p style={{
              fontSize: '40px',
              fontWeight: '600',
              color: '#1a1a1a',
              margin: '0 0 4px 0',
              letterSpacing: '-1px'
            }}>
              {stats.analyzedProjects}
            </p>
            <p style={{
              fontSize: '13px',
              color: '#a3a3a3',
              margin: 0
            }}>
              0 with AI
            </p>
          </div>

          <div style={{
            backgroundColor: 'white',
            padding: '28px',
            borderRadius: '16px',
            border: '1px solid #e5e5e5',
            display: 'flex',
            flexDirection: 'column',
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '16px'
            }}>
              <h3 style={{
                fontSize: '14px',
                fontWeight: '500',
                color: '#737373',
                margin: 0,
              }}>
                Total Lines of Code
              </h3>
              <span style={{
                fontSize: '18px',
                opacity: 0.4
              }}>📄</span>
            </div>
            <p style={{
              fontSize: '40px',
              fontWeight: '600',
              color: '#1a1a1a',
              margin: 0,
              letterSpacing: '-1px'
            }}>
              {stats.totalLinesOfCode.toLocaleString()}
            </p>
          </div>

          <div style={{
            backgroundColor: 'white',
            padding: '28px',
            borderRadius: '16px',
            border: '1px solid #e5e5e5',
            display: 'flex',
            flexDirection: 'column',
          }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              marginBottom: '16px'
            }}>
              <h3 style={{
                fontSize: '14px',
                fontWeight: '500',
                color: '#737373',
                margin: 0,
              }}>
                Skills Detected
              </h3>
              <span style={{
                fontSize: '18px',
                opacity: 0.4
              }}>🎯</span>
            </div>
            <p style={{
              fontSize: '40px',
              fontWeight: '600',
              color: '#1a1a1a',
              margin: 0,
              letterSpacing: '-1px'
            }}>
              {stats.skillsDetected}
            </p>
          </div>
        </div>

        <div>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: '#1a1a1a',
            margin: '0 0 20px 0',
          }}>
            Quick Actions
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '24px'
          }}>
            {quickActions.map((action, index) => (
              <div
                key={index}
                onClick={action.onClick}
                style={{
                  backgroundColor: 'white',
                  padding: '32px 24px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                  textAlign: 'center',
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.transform = 'translateY(-4px)';
                  e.currentTarget.style.boxShadow = '0 8px 16px rgba(0, 0, 0, 0.1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'translateY(0)';
                  e.currentTarget.style.boxShadow = 'none';
                }}
              >
                <div style={{
                  fontSize: '36px',
                  marginBottom: '16px',
                  opacity: 0.7
                }}>
                  {action.icon}
                </div>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: '0 0 6px 0'
                }}>
                  {action.title}
                </h3>
                <p style={{
                  fontSize: '14px',
                  color: '#737373',
                  margin: 0
                }}>
                  {action.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
