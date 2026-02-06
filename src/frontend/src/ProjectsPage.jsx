import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { projectsAPI, resumeAPI } from './services/api';
import Navigation from './components/Navigation';

export default function ProjectsPage() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true); // loading projects list
  const [detailsLoading, setDetailsLoading] = useState(false); // loading resume/portfolio details
  const [error, setError] = useState('');
  const [deletingAll, setDeletingAll] = useState(false);
  const [storedResumes, setStoredResumes] = useState([]);
  const [selectedResumeId, setSelectedResumeId] = useState('');
  const [selectedResumeItemIds, setSelectedResumeItemIds] = useState([]);
  const [addingItems, setAddingItems] = useState(false);


  // track per-project delete loading
  const [deletingIds, setDeletingIds] = useState({}); // { [projectId]: true/false }

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
    loadStoredResumes();
  }, [isAuthenticated, navigate, user]);

  const loadStoredResumes = async () => {
    try {
      const data = await resumeAPI.listStoredResumes();
      setStoredResumes(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading stored resumes:', err);
    }
  };

  const toggleResumeItemSelection = (itemId) => {
    setSelectedResumeItemIds((prev) => {
      if (prev.includes(itemId)) {
        return prev.filter((id) => id !== itemId);
      }
      return [...prev, itemId];
    });
  };

  const handleAddSelectedItems = async () => {
    if (!selectedResumeId) {
      setError('Select a stored resume to add bullets.');
      return;
    }
    if (selectedResumeItemIds.length === 0) {
      setError('Select at least one bullet to add.');
      return;
    }

    try {
      setAddingItems(true);
      setError('');
      await resumeAPI.addItemsToResume(selectedResumeId, selectedResumeItemIds);
      setSelectedResumeItemIds([]);
    } catch (err) {
      console.error('Error adding bullets:', err);
      setError(err.response?.data?.detail || 'Failed to add bullets to resume');
    } finally {
      setAddingItems(false);
    }
  };

  async function handleDeleteProject(projectId, projectName) {
    const name = projectName || 'this project';
    const ok = window.confirm(`Delete "${name}"?\n\nThis will remove the project and its saved resume bullets/summary from your account.`);
    if (!ok) return;

    setError('');
    setDeletingIds((prev) => ({ ...prev, [projectId]: true }));

    try {
      await projectsAPI.deleteProject(projectId);

      // remove from UI immediately
      setProjects((prev) => prev.filter((p) => p.id !== projectId));
    } catch (e) {
      console.error('Delete project failed:', e);
      const msg = e?.response?.data?.detail || e?.message || 'Failed to delete project';
      setError(msg);
    } finally {
      setDeletingIds((prev) => {
        const copy = { ...prev };
        delete copy[projectId];
        return copy;
      });
    }
  }
  async function handleDeleteAllProjects() {
    if (deletingAll) return;
  
    const count = projects.length;
    const ok = window.confirm(
      `Delete ALL your projects? (${count})\n\nThis will remove every project and its saved resume bullets/summary from your account. This cannot be undone.`
    );
    if (!ok) return;
  
    setError('');
    setDeletingAll(true);
  
    try {
      await projectsAPI.deleteAllProjects();
  
      // clear UI immediately
      setProjects([]);
      setDeletingIds({});
    } catch (e) {
      console.error('Delete all projects failed:', e);
      const msg = e?.response?.data?.detail || e?.message || 'Failed to delete all projects';
      setError(msg);
    } finally {
      setDeletingAll(false);
    }
  }  

  // --- Shared styles to match Dashboard look ---
  const pageStyles = {
    minHeight: '100vh',
    backgroundColor: '#fafafa',
  };

  const containerStyles = {
    maxWidth: '1400px',
    margin: '0 auto',
    padding: '48px 32px',
  };

  const cardStyles = {
    backgroundColor: 'white',
    border: '1px solid #e5e5e5',
    borderRadius: '16px',
  };

  const secondaryText = { color: '#737373' };
  const headingText = { color: '#1a1a1a' };

  return (
    <div style={pageStyles}>
      <Navigation />

      <div style={containerStyles}>
        {/* Header (Dashboard-style) */}
        <div
          style={{
            marginBottom: '32px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '16px',
          }}
        >
          <div>
            <h1
              style={{
                fontSize: '36px',
                fontWeight: '600',
                margin: '0 0 12px 0',
                ...headingText,
                letterSpacing: '-0.5px',
              }}
            >
              My Projects
            </h1>
            <p style={{ fontSize: '16px', margin: 0, ...secondaryText }}>
              View your analyzed projects, summaries, and resume bullets
            </p>
          </div>

          <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
            <select
              value={selectedResumeId || ''}
              onChange={(e) => setSelectedResumeId(e.target.value)}
              style={{
                padding: '8px 12px',
                fontSize: '14px',
                border: '1px solid #d1d5db',
                borderRadius: '6px',
                backgroundColor: 'white',
                minWidth: '220px',
              }}
            >
              <option value="">Select stored resume</option>
              {storedResumes.map((resume) => (
                <option key={resume.id} value={resume.id}>
                  {resume.title}
                </option>
              ))}
            </select>

            <button
              onClick={handleAddSelectedItems}
              disabled={addingItems}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 14px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap',
              }}
            >
              {addingItems ? 'Adding...' : 'Add selected bullets'}
            </button>

            <button
              onClick={() => navigate('/dashboard')}
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
                whiteSpace: 'nowrap',
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
              <span style={{ opacity: 0.8 }}>←</span>
              <span>Back to Dashboard</span>
            </button>
          </div>
        </div>

        {/* Top stat card (Dashboard-style) */}
        <div
          style={{
            ...cardStyles,
            padding: '28px',
            marginBottom: '24px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '16px',
          }}
        >
          <div>
            <h3
              style={{
                fontSize: '14px',
                fontWeight: '500',
                margin: '0 0 12px 0',
                ...secondaryText,
              }}
            >
              Total Projects
            </h3>
            <p
              style={{
                fontSize: '40px',
                fontWeight: '600',
                margin: 0,
                letterSpacing: '-1px',
                ...headingText,
              }}
            >
              {projects.length}
            </p>

            {!loading && detailsLoading && (
              <p style={{ margin: '10px 0 0 0', fontSize: '13px', color: '#a3a3a3' }}>
                Loading resume + summary details...
              </p>
            )}
          </div>

          <div style={{ fontSize: '18px', opacity: 0.35 }}>📁</div>
        </div>

        {/* Loading */}
        {loading && (
          <div
            style={{
              ...cardStyles,
              padding: '24px',
              textAlign: 'center',
            }}
          >
            <p style={{ margin: 0, fontSize: '16px', ...secondaryText }}>Loading projects...</p>
          </div>
        )}

        {/* Error */}
        {error && (
          <div
            style={{
              padding: '16px 18px',
              backgroundColor: '#FEE2E2',
              color: '#B91C1C',
              borderRadius: '12px',
              border: '1px solid #fecaca',
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
              ...cardStyles,
              padding: '40px',
              textAlign: 'center',
            }}
          >
            <p style={{ fontSize: '18px', ...secondaryText, margin: 0 }}>No projects found.</p>

            <button
              onClick={() => navigate('/dashboard')}
              style={{
                marginTop: '16px',
                padding: '10px 20px',
                fontSize: '14px',
                fontWeight: '500',
                color: '#1a1a1a',
                backgroundColor: 'white',
                border: '1px solid #e5e5e5',
                borderRadius: '8px',
                cursor: 'pointer',
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
              Go to Dashboard
            </button>
          </div>
        )}

        {/* Projects list */}
        {!loading && !error && projects.length > 0 && (
          <div>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                gap: '12px',
                margin: '0 0 16px 0',
              }}
            >
              <p
                style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  margin: 0,
                  ...headingText,
                }}
              >
                Found project(s)
              </p>

              <button
                disabled={deletingAll}
                onClick={handleDeleteAllProjects}
                style={{
                  padding: '10px 14px',
                  fontSize: '13px',
                  fontWeight: '700',
                  borderRadius: '10px',
                  cursor: deletingAll ? 'not-allowed' : 'pointer',
                  border: '1px solid #fecaca',
                  backgroundColor: '#fee2e2',
                  color: '#991b1b',
                  transition: 'all 0.2s',
                  whiteSpace: 'nowrap',
                }}
                onMouseEnter={(e) => {
                  if (deletingAll) return;
                  e.currentTarget.style.backgroundColor = '#fecaca';
                  e.currentTarget.style.borderColor = '#fca5a5';
                }}
                onMouseLeave={(e) => {
                  if (deletingAll) return;
                  e.currentTarget.style.backgroundColor = '#fee2e2';
                  e.currentTarget.style.borderColor = '#fecaca';
                }}
              >
                {deletingAll ? 'Deleting all…' : 'Delete all projects'}
              </button>
            </div>
            
            <div style={{ display: 'grid', gap: '20px' }}>
              {projects.map((p) => {
                const isDeleting = !!deletingIds[p.id];

                return (
                  <div
                    key={p.id}
                    style={{
                      ...cardStyles,
                      padding: '24px',
                      transition: 'transform 0.2s, box-shadow 0.2s',
                      opacity: isDeleting ? 0.65 : 1,
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.transform = 'translateY(-2px)';
                      e.currentTarget.style.boxShadow = '0 10px 20px rgba(0, 0, 0, 0.06)';
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.transform = 'translateY(0)';
                      e.currentTarget.style.boxShadow = 'none';
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', gap: '12px' }}>
                      <div style={{ minWidth: 0 }}>
                        <strong
                          style={{
                            fontSize: '20px',
                            color: '#1a1a1a',
                            display: 'block',
                            marginBottom: '8px',
                            letterSpacing: '-0.2px',
                          }}
                        >
                          {p.project_name || 'Unnamed Project'}
                        </strong>

                        <div style={{ color: '#525252', marginBottom: '4px', fontSize: '14px' }}>
                          Primary language: <strong>{p.primary_language || 'Unknown'}</strong>
                        </div>
                        <div style={{ color: '#525252', marginBottom: '4px', fontSize: '14px' }}>
                          Total files: <strong>{p.total_files || 0}</strong>
                        </div>
                        <div style={{ color: '#525252', marginBottom: '4px', fontSize: '14px' }}>
                          Has tests: <strong>{p.has_tests ? 'Yes' : 'No'}</strong>
                        </div>
                        <div style={{ color: '#525252', fontSize: '14px' }}>
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
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '10px' }}>
                        <div style={{ fontSize: '18px', opacity: 0.3 }}>📦</div>

                        {/* Delete button */}
                        <button
                          disabled={isDeleting || deletingAll}
                          onClick={() => handleDeleteProject(p.id, p.project_name)}
                          style={{
                            padding: '8px 12px',
                            fontSize: '13px',
                            fontWeight: '600',
                            borderRadius: '10px',
                            cursor: isDeleting || deletingAll ? 'not-allowed' : 'pointer',
                            border: '1px solid #fecaca',
                            backgroundColor: '#fee2e2',
                            color: '#991b1b',
                            transition: 'all 0.2s',
                            whiteSpace: 'nowrap',
                          }}
                          onMouseEnter={(e) => {
                            if (isDeleting || deletingAll) return;
                            e.currentTarget.style.backgroundColor = '#fecaca';
                            e.currentTarget.style.borderColor = '#fca5a5';
                          }}
                          onMouseLeave={(e) => {
                            if (isDeleting || deletingAll) return;
                            e.currentTarget.style.backgroundColor = '#fee2e2';
                            e.currentTarget.style.borderColor = '#fecaca';
                          }}
                        >
                          {isDeleting ? 'Deleting…' : 'Delete project'}
                        </button>
                      </div>
                    </div>

                    {/* Details warning (per project) */}
                    {p.details_error && (
                      <div
                        style={{
                          marginTop: '14px',
                          padding: '12px 14px',
                          backgroundColor: '#FEF3C7',
                          color: '#92400E',
                          borderRadius: '12px',
                          border: '1px solid #fde68a',
                          fontSize: '13px',
                        }}
                      >
                        <strong>Details warning:</strong> {p.details_error}
                      </div>
                    )}

                    {/* Summary */}
                    <div style={{ marginTop: '18px' }}>
                      <div
                        style={{
                          fontSize: '13px',
                          fontWeight: '600',
                          color: '#525252',
                          marginBottom: '8px',
                          textTransform: 'uppercase',
                          letterSpacing: '0.4px',
                        }}
                      >
                        Summary
                      </div>

                      {p.portfolio && p.portfolio.text_summary ? (
                        <div style={{ color: '#262626', lineHeight: 1.55, fontSize: '14px' }}>
                          {p.portfolio.text_summary}
                        </div>
                      ) : (
                        <div style={{ color: '#737373', fontSize: '14px' }}>
                          No summary found for this project yet.
                        </div>
                      )}
                    </div>

                    {/* Resume bullets */}
                    <div style={{ marginTop: '18px' }}>
                      <div
                        style={{
                          fontSize: '13px',
                          fontWeight: '600',
                          color: '#525252',
                          marginBottom: '8px',
                          textTransform: 'uppercase',
                          letterSpacing: '0.4px',
                        }}
                      >
                        Resume bullets
                      </div>

                      {p.resume_items === null ? (
                        <div style={{ color: '#737373', fontSize: '14px' }}>
                          Loading resume bullets...
                        </div>
                      ) : p.resume_items.length > 0 ? (
                        <ul style={{ margin: 0, paddingLeft: '18px', color: '#262626' }}>
                          {p.resume_items.map((ri) => (
                            <li key={ri.id} style={{ marginBottom: '6px', lineHeight: 1.45 }}>
                              <label style={{ display: 'flex', gap: '8px', alignItems: 'flex-start' }}>
                                <input
                                  type="checkbox"
                                  checked={selectedResumeItemIds.includes(ri.id)}
                                  onChange={() => toggleResumeItemSelection(ri.id)}
                                  style={{ marginTop: '3px' }}
                                />
                                <span>{ri.resume_text}</span>
                              </label>
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <div style={{ color: '#737373', fontSize: '14px' }}>
                          No resume bullets found for this project yet.
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
