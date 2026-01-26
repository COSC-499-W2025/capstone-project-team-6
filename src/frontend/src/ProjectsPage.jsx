import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { projectsAPI } from './services/api';
import Navigation from './components/Navigation';

export default function ProjectsPage() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);        // loading projects list
  const [detailsLoading, setDetailsLoading] = useState(false); // loading resume/portfolio details
  const [error, setError] = useState('');

  useEffect(() => {
    console.log('ProjectsPage - Auth status:', { isAuthenticated, user });
    console.log('ProjectsPage - Token:', localStorage.getItem('access_token'));

    if (!isAuthenticated) {
      console.log('Not authenticated, redirecting to login');
      navigate('/login');
      return;
    }

    async function loadProjectsAndDetails() {
      setLoading(true);
      setError('');

      try {
        console.log('Fetching projects...');
        const baseProjects = await projectsAPI.getProjects();
        console.log('Projects received:', baseProjects);

        // Put base projects on screen ASAP
        // Add placeholders for details so UI doesn't explode
        const withPlaceholders = baseProjects.map((p) => ({
          ...p,
          resume_items: null,
          portfolio: null,
          details_error: null,
        }));
        setProjects(withPlaceholders);

        // Now fetch details (resume + portfolio) for each project
        setDetailsLoading(true);

        const enriched = await Promise.all(
          withPlaceholders.map(async (p) => {
            try {
              const resumeItems = await projectsAPI.getResumeItems(p.id);
              const portfolio = await projectsAPI.getPortfolioItem(p.id);

              return {
                ...p,
                resume_items: Array.isArray(resumeItems) ? resumeItems : [],
                portfolio: portfolio && Object.keys(portfolio).length > 0 ? portfolio : null,
                details_error: null,
              };
            } catch (err) {
              console.error('Error loading details for project:', p.id, err);
              return {
                ...p,
                resume_items: [],
                portfolio: null,
                details_error:
                  err?.response?.data?.detail || err?.message || 'Failed to load project details',
              };
            }
          })
        );

        setProjects(enriched);
      } catch (e) {
        console.error('Error loading projects:', e);
        console.error('Error response:', e?.response);
        const errorMsg = e?.response?.data?.detail || e?.message || 'Failed to load projects';
        setError(errorMsg);
      } finally {
        setDetailsLoading(false);
        setLoading(false);
      }
    }

    loadProjectsAndDetails();
  }, [isAuthenticated, navigate, user]);

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#f5f5f5',
        padding: '20px',
      }}
    >
      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header card */}
        <div
          style={{
            backgroundColor: 'white',
            padding: '32px',
            borderRadius: '12px',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h1
            style={{
              fontSize: '28px',
              fontWeight: '700',
              margin: 0,
              color: '#1a1a1a',
            }}
          >
            My Projects
          </h1>

          <button
            onClick={() => navigate('/dashboard')}
            style={{
              padding: '12px 24px',
              fontSize: '14px',
              fontWeight: '600',
              color: 'white',
              backgroundColor: '#3B82F6',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              transition: 'background-color 0.2s',
            }}
            onMouseEnter={(e) => (e.target.style.backgroundColor = '#2563EB')}
            onMouseLeave={(e) => (e.target.style.backgroundColor = '#3B82F6')}
          >
            Back to Dashboard
          </button>
        </div>

        {/* Debug card */}
        <div
          style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '12px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.06)',
            marginBottom: '24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <h3
              style={{
                margin: '0 0 4px 0',
                fontSize: '14px',
                fontWeight: '600',
                color: '#666',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
              }}
            >
              Total Projects
            </h3>
            <p
              style={{
                margin: 0,
                fontSize: '28px',
                fontWeight: '700',
                color: '#1a1a1a',
              }}
            >
              {projects.length}
            </p>
            {!loading && detailsLoading && (
              <p style={{ margin: '8px 0 0 0', fontSize: '12px', color: '#666' }}>
                Loading resume + summary details...
              </p>
            )}
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div
            style={{
              backgroundColor: 'white',
              padding: '24px',
              borderRadius: '12px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.06)',
              textAlign: 'center',
            }}
          >
            <p style={{ margin: 0, fontSize: '16px', color: '#666' }}>Loading projects...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            style={{
              padding: '20px',
              backgroundColor: '#FEE2E2',
              color: '#B91C1C',
              borderRadius: '12px',
              boxShadow: '0 2px 4px rgba(0,0,0,0.06)',
              marginBottom: '24px',
            }}
          >
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* No projects */}
        {!loading && !error && projects.length === 0 && (
          <div
            style={{
              backgroundColor: 'white',
              padding: '40px',
              borderRadius: '12px',
              textAlign: 'center',
              boxShadow: '0 4px 6px rgba(0,0,0,0.05)',
            }}
          >
            <p style={{ fontSize: '18px', color: '#666' }}>No projects found.</p>

            <button
              onClick={() => navigate('/dashboard')}
              style={{
                marginTop: '16px',
                padding: '12px 24px',
                fontSize: '14px',
                fontWeight: '600',
                color: 'white',
                backgroundColor: '#1a1a1a',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                transition: 'background-color 0.2s',
              }}
              onMouseEnter={(e) => (e.target.style.backgroundColor = '#333')}
              onMouseLeave={(e) => (e.target.style.backgroundColor = '#1a1a1a')}
            >
              Go to Dashboard
            </button>
          </div>
        )}

        {/* Projects list */}
        {!loading && !error && projects.length > 0 && (
          <div>
            <p
              style={{
                fontSize: '16px',
                fontWeight: '600',
                marginBottom: '16px',
                color: '#1a1a1a',
              }}
            >
              Found project(s)
            </p>

            <div style={{ display: 'grid', gap: '20px' }}>
              {projects.map((p) => (
                <div
                  key={p.id}
                  style={{
                    backgroundColor: 'white',
                    padding: '24px',
                    borderRadius: '12px',
                    boxShadow: '0 4px 6px rgba(0,0,0,0.08)',
                  }}
                >
                  <strong
                    style={{
                      fontSize: '20px',
                      color: '#1a1a1a',
                      display: 'block',
                      marginBottom: '8px',
                    }}
                  >
                    {p.project_name || 'Unnamed Project'}
                  </strong>

                  <div style={{ color: '#555', marginBottom: '4px' }}>
                    Primary language: <strong>{p.primary_language || 'Unknown'}</strong>
                  </div>
                  <div style={{ color: '#555', marginBottom: '4px' }}>
                    Total files: <strong>{p.total_files || 0}</strong>
                  </div>
                  <div style={{ color: '#555', marginBottom: '4px' }}>
                    Has tests: <strong>{p.has_tests ? 'Yes' : 'No'}</strong>
                  </div>
                  <div style={{ color: '#555' }}>
                    Last modified:{' '}
                    <strong>
                      {p.last_modified_date
                        ? new Date(p.last_modified_date).toLocaleString('en-US', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: 'numeric',
                            minute: '2-digit',
                          })
                        : 'N/A'}
                    </strong>
                  </div>

                  {/* Details error (per project) */}
                  {p.details_error && (
                    <div
                      style={{
                        marginTop: '14px',
                        padding: '12px',
                        backgroundColor: '#FEF3C7',
                        color: '#92400E',
                        borderRadius: '10px',
                        fontSize: '13px',
                      }}
                    >
                      <strong>Details warning:</strong> {p.details_error}
                    </div>
                  )}

                  {/* Portfolio summary */}
                  <div style={{ marginTop: '18px' }}>
                    <div
                      style={{
                        fontSize: '13px',
                        fontWeight: '700',
                        color: '#111',
                        marginBottom: '6px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.4px',
                      }}
                    >
                      Summary
                    </div>

                    {p.portfolio && p.portfolio.text_summary ? (
                      <div style={{ color: '#333', lineHeight: 1.55, fontSize: '14px' }}>
                        {p.portfolio.text_summary}
                      </div>
                    ) : (
                      <div style={{ color: '#666', fontSize: '14px' }}>
                        No summary found for this project yet.
                      </div>
                    )}
                  </div>

                  {/* Resume items */}
                  <div style={{ marginTop: '18px' }}>
                    <div
                      style={{
                        fontSize: '13px',
                        fontWeight: '700',
                        color: '#111',
                        marginBottom: '8px',
                        textTransform: 'uppercase',
                        letterSpacing: '0.4px',
                      }}
                    >
                      Resume bullets
                    </div>

                    {p.resume_items === null ? (
                      <div style={{ color: '#666', fontSize: '14px' }}>
                        Loading resume bullets...
                      </div>
                    ) : p.resume_items.length > 0 ? (
                      <ul style={{ margin: 0, paddingLeft: '18px', color: '#333' }}>
                        {p.resume_items.map((ri) => (
                          <li key={ri.id} style={{ marginBottom: '6px', lineHeight: 1.45 }}>
                            {ri.resume_text}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div style={{ color: '#666', fontSize: '14px' }}>
                        No resume bullets found for this project yet.
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
