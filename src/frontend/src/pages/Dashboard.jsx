import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import { projectsAPI, portfoliosAPI, curationAPI } from '../services/api';
import api from '../services/api';

const Dashboard = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [stats, setStats] = useState({
    totalProjects: 0,
    analyzedProjects: 0,
    totalFiles: 0,
    skillsDetected: 0,
    aiAnalyzedProjects: 0,
  });

  const [showcaseProjects, setShowcaseProjects] = useState([]);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // Fetch projects data
        const projectsData = await projectsAPI.getProjects();
        // Handle both array and object with projects property
        const projects = Array.isArray(projectsData) ? projectsData : (projectsData?.projects || []);

        // Fetch skills data
        const skillsResponse = await api.get('/skills');
        const totalSkills = skillsResponse.data.total_skills || 0;

        // Fetch portfolios to get AI analysis count
        const portfolios = await portfoliosAPI.listPortfolios();
        const aiAnalyzedCount = (portfolios || [])
          .filter(p => p.analysis_type === 'llm')
          .reduce((sum, p) => sum + (p.total_projects || 0), 0);

        // Calculate total files across all projects
        let totalFiles = 0;
        projects.forEach(project => {
          totalFiles += project.total_files || 0;
        });

        setStats({
          totalProjects: projects.length,
          analyzedProjects: projects.length,
          totalFiles: totalFiles,
          skillsDetected: totalSkills,
          aiAnalyzedProjects: aiAnalyzedCount,
        });
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      }
    };

    fetchDashboardData();

    // Fetch showcase projects
    curationAPI.getShowcase()
      .then((data) => setShowcaseProjects(Array.isArray(data) ? data : []))
      .catch(() => setShowcaseProjects([]));
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
              {stats.aiAnalyzedProjects} with AI
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
                Total Files
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
              {stats.totalFiles.toLocaleString()}
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

        {/* Showcase Projects */}
        <div style={{ marginTop: '48px' }}>
          <h2 style={{
            fontSize: '24px',
            fontWeight: '600',
            color: '#1a1a1a',
            margin: '0 0 20px 0',
          }}>
             Showcase Projects
          </h2>

          {showcaseProjects.length > 0 ? (
            <div style={{
              display: 'grid',
              gridTemplateColumns: `repeat(${Math.min(showcaseProjects.length, 3)}, 1fr)`,
              gap: '24px',
            }}>
              {showcaseProjects.map((project, index) => (
                <div
                  key={project.id}
                  onClick={() => navigate('/projects', { state: { showcaseProjectId: project.id } })}
                  style={{
                    backgroundColor: 'white',
                    padding: '24px',
                    borderRadius: '16px',
                    border: '2px solid #f59e0b',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.transform = 'translateY(-4px)';
                    e.currentTarget.style.boxShadow = '0 8px 20px rgba(245, 158, 11, 0.15)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }}
                >
                  <span style={{
                    position: 'absolute',
                    top: '-10px',
                    right: '14px',
                    padding: '2px 10px',
                    borderRadius: '999px',
                    backgroundColor: '#f59e0b',
                    color: 'white',
                    fontSize: '12px',
                    fontWeight: '700',
                  }}>⭐ Top {index + 1}</span>

                  <h3 style={{
                    fontSize: '18px',
                    fontWeight: '600',
                    color: '#1a1a1a',
                    margin: '0 0 8px 0',
                  }}>
                    {project.project_name || 'Unnamed Project'}
                  </h3>

                  <div style={{ fontSize: '14px', color: '#525252', marginBottom: '4px' }}>
                    {project.primary_language || 'Unknown language'}
                  </div>
                  <div style={{ fontSize: '13px', color: '#737373' }}>
                    {project.total_files ?? 0} files
                    {project.has_tests ? ' • Has tests' : ''}
                  </div>

                  {(project.frameworks?.length > 0) && (
                    <div style={{
                      marginTop: '10px',
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '6px',
                    }}>
                      {project.frameworks.slice(0, 3).map((fw) => (
                        <span key={fw} style={{
                          padding: '2px 8px',
                          borderRadius: '999px',
                          backgroundColor: '#fef3c7',
                          color: '#92400e',
                          fontSize: '11px',
                          fontWeight: '600',
                        }}>{fw}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div style={{
              backgroundColor: 'white',
              padding: '32px',
              borderRadius: '12px',
              border: '1px solid #e5e5e5',
              textAlign: 'center',
            }}>
              <p style={{ color: '#737373', margin: '0 0 12px 0' }}>
                No showcase projects selected yet.
              </p>
              <button
                onClick={() => navigate('/curate')}
                style={{
                  padding: '8px 20px',
                  borderRadius: '8px',
                  border: '1px solid #f59e0b',
                  backgroundColor: '#fffbeb',
                  color: '#b45309',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '600',
                }}
              >
                Select your top projects →
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
