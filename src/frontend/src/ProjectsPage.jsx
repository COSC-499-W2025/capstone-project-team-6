import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { projectsAPI } from './services/api';
import Navigation from './components/Navigation';

export default function ProjectsPage() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true); // loading projects list
  const [detailsLoading, setDetailsLoading] = useState(false); // loading resume/portfolio details
  const [error, setError] = useState('');
  const [deletingAll, setDeletingAll] = useState(false);


  // track per-project delete loading
  const [deletingIds, setDeletingIds] = useState({}); // { [projectId]: true/false }

  // track per-project thumbnail state
  const [thumbnailUrls, setThumbnailUrls] = useState({}); // { [projectId]: url or null }
  const [thumbnailLoading, setThumbnailLoading] = useState({}); // { [projectId]: true/false }
  const [thumbnailErrors, setThumbnailErrors] = useState({}); // { [projectId]: error message }

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
        console.log('First project:', baseProjects[0]);
        if (baseProjects[0]) {
          console.log('Composite ID fields:', {
            composite_id: baseProjects[0].composite_id,
            analysis_uuid: baseProjects[0].analysis_uuid,
            project_path: baseProjects[0].project_path,
          });
        }

        // Put base projects on screen ASAP
        // Add placeholders for details so UI doesn't explode
        const withPlaceholders = baseProjects.map((p) => {
          // Construct composite_id if not provided but we have the parts
          // Note: project_path can be empty string "" or null for projects at root level
          let compositeId = p.composite_id;
          if (!compositeId && p.analysis_uuid) {
            const projectPath = p.project_path ?? '';
            compositeId = `${p.analysis_uuid}:${projectPath}`;
          }
          return {
            ...p,
            composite_id: compositeId,
            resume_items: null,
            portfolio: null,
            details_error: null,
          };
        });
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

  async function handleThumbnailUpload(projectId, compositeId, file) {
    if (!file) return;

    // Use composite_id for API calls (format: {analysis_uuid}:{project_path})
    const apiId = compositeId || projectId;

    // Check if we have a valid composite ID format
    if (!apiId || !String(apiId).includes(':')) {
      console.error('Invalid composite_id for thumbnail upload:', { projectId, compositeId, apiId });
      setThumbnailErrors((prev) => ({
        ...prev,
        [projectId]: 'Unable to upload: missing project identifier. Please refresh the page.'
      }));
      return;
    }

    // Validate file type
    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setThumbnailErrors((prev) => ({ ...prev, [projectId]: 'Please select a valid image (JPG, PNG, GIF, or WebP)' }));
      return;
    }

    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      setThumbnailErrors((prev) => ({ ...prev, [projectId]: 'Image must be less than 5MB' }));
      return;
    }

    setThumbnailLoading((prev) => ({ ...prev, [projectId]: true }));
    setThumbnailErrors((prev) => ({ ...prev, [projectId]: null }));

    try {
      await projectsAPI.uploadThumbnail(apiId, file);
      // Fetch the new thumbnail as blob
      const blobUrl = await projectsAPI.getThumbnail(apiId);
      setThumbnailUrls((prev) => {
        // Revoke old blob URL to prevent memory leak
        if (prev[projectId]) {
          URL.revokeObjectURL(prev[projectId]);
        }
        return { ...prev, [projectId]: blobUrl };
      });
    } catch (e) {
      console.error('Thumbnail upload failed:', e);
      // FastAPI 422 returns detail as array of error objects, not a string
      let msg = 'Failed to upload thumbnail';
      const detail = e?.response?.data?.detail;
      if (typeof detail === 'string') {
        msg = detail;
      } else if (Array.isArray(detail) && detail.length > 0) {
        msg = detail[0]?.msg || msg;
      } else if (e?.message) {
        msg = e.message;
      }
      setThumbnailErrors((prev) => ({ ...prev, [projectId]: msg }));
    } finally {
      setThumbnailLoading((prev) => ({ ...prev, [projectId]: false }));
    }
  }

  // Load thumbnails when projects load
  useEffect(() => {
    if (projects.length === 0) return;

    let isCancelled = false;
    const loadedUrls = [];

    async function loadThumbnails() {
      const results = await Promise.all(
        projects.map(async (p) => {
          const thumbnailId = p.composite_id || p.id;
          if (!thumbnailId) return { id: p.id, url: null };

          try {
            const blobUrl = await projectsAPI.getThumbnail(thumbnailId);
            loadedUrls.push(blobUrl);
            return { id: p.id, url: blobUrl };
          } catch (e) {
            return { id: p.id, url: null };
          }
        })
      );

      if (!isCancelled) {
        const urlMap = {};
        results.forEach(({ id, url }) => {
          urlMap[id] = url;
        });
        setThumbnailUrls(urlMap);
      }
    }

    loadThumbnails();

    // Cleanup: revoke blob URLs when component unmounts or projects change
    return () => {
      isCancelled = true;
      loadedUrls.forEach((url) => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, [projects]);

  // Keep a ref to thumbnailUrls for cleanup on unmount
  const thumbnailUrlsRef = useRef(thumbnailUrls);
  useEffect(() => {
    thumbnailUrlsRef.current = thumbnailUrls;
  }, [thumbnailUrls]);

  // Cleanup all blob URLs on component unmount only
  useEffect(() => {
    return () => {
      Object.values(thumbnailUrlsRef.current).forEach((url) => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, []);

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
                        {/* Thumbnail upload area */}
                        <div style={{ position: 'relative' }}>
                          <input
                            type="file"
                            accept="image/jpeg,image/png,image/gif,image/webp"
                            onChange={(e) => {
                              const file = e.target.files?.[0];
                              if (file) handleThumbnailUpload(p.id, p.composite_id, file);
                              e.target.value = ''; // Reset input
                            }}
                            style={{
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              width: '100%',
                              height: '100%',
                              opacity: 0,
                              cursor: 'pointer',
                              zIndex: 2,
                            }}
                            disabled={thumbnailLoading[p.id]}
                          />
                          <div
                            style={{
                              width: '80px',
                              height: '80px',
                              borderRadius: '12px',
                              border: '2px dashed #d4d4d4',
                              backgroundColor: '#fafafa',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              overflow: 'hidden',
                              transition: 'all 0.2s',
                              cursor: 'pointer',
                            }}
                            onMouseEnter={(e) => {
                              e.currentTarget.style.borderColor = '#a3a3a3';
                              e.currentTarget.style.backgroundColor = '#f5f5f5';
                            }}
                            onMouseLeave={(e) => {
                              e.currentTarget.style.borderColor = '#d4d4d4';
                              e.currentTarget.style.backgroundColor = '#fafafa';
                            }}
                          >
                            {thumbnailLoading[p.id] ? (
                              <span style={{ fontSize: '12px', color: '#737373' }}>Uploading...</span>
                            ) : thumbnailUrls[p.id] ? (
                              <img
                                src={thumbnailUrls[p.id]}
                                alt={`${p.project_name || 'Project'} thumbnail`}
                                style={{
                                  width: '100%',
                                  height: '100%',
                                  objectFit: 'cover',
                                }}
                              />
                            ) : (
                              <div
                                style={{
                                  display: 'flex',
                                  flexDirection: 'column',
                                  alignItems: 'center',
                                  gap: '4px',
                                  color: '#a3a3a3',
                                  fontSize: '10px',
                                  textAlign: 'center',
                                  pointerEvents: 'none',
                                }}
                              >
                                <span style={{ fontSize: '20px' }}>📷</span>
                                <span>Add image</span>
                              </div>
                            )}
                          </div>
                          {thumbnailErrors[p.id] && (
                            <div
                              style={{
                                position: 'absolute',
                                top: '100%',
                                right: 0,
                                marginTop: '4px',
                                fontSize: '11px',
                                color: '#B91C1C',
                                whiteSpace: 'nowrap',
                              }}
                            >
                              {thumbnailErrors[p.id]}
                            </div>
                          )}
                        </div>

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
                              {ri.resume_text}
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
