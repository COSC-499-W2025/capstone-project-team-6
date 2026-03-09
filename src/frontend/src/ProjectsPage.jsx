import { useEffect, useState, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { projectsAPI, curationAPI } from './services/api';
import Navigation from './components/Navigation';

export default function ProjectsPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, isAuthenticated } = useAuth();

  const [showcaseFilter, setShowcaseFilter] = useState(location.state?.showcaseProjectId || null);

  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [error, setError] = useState('');
  const [deletingAll, setDeletingAll] = useState(false);

  const [filters, setFilters] = useState({
    searchTerm: '',
    language: 'all',
    hasTests: 'all',
    sortBy: 'date',
  });

  const [showcaseRanks, setShowcaseRanks] = useState(new Map());
  const [customProjectOrder, setCustomProjectOrder] = useState([]);
  const [deletingIds, setDeletingIds] = useState({});
  const [thumbnailUrls, setThumbnailUrls] = useState({});
  const [thumbnailLoading, setThumbnailLoading] = useState({});
  const [thumbnailErrors, setThumbnailErrors] = useState({});

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    async function loadProjectsAndDetails() {
      setLoading(true);
      setError('');

      try {
        const baseProjects = await projectsAPI.getProjects();

        const projectsArray = Array.isArray(baseProjects?.projects)
          ? baseProjects.projects
          : Array.isArray(baseProjects)
            ? baseProjects
            : [];

        const withPlaceholders = projectsArray.map((p) => {
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
    loadCurationSettings();
  }, [isAuthenticated, navigate, user]);

  const loadCurationSettings = async () => {
    try {
      const settings = await curationAPI.getSettings();
      const ids = settings?.showcase_project_ids ?? [];
      const map = new Map();
      ids.forEach((id, i) => map.set(id, i + 1));
      setShowcaseRanks(map);
      setCustomProjectOrder(settings?.custom_project_order ?? []);
    } catch (err) {
      console.error('Error loading curation settings:', err);
    }
  };

  async function handleDeleteProject(projectId, projectName) {
    const name = projectName || 'this project';
    const ok = window.confirm(
      `Delete "${name}"?\n\nThis will remove the project and its saved resume bullets/summary from your account.`
    );
    if (!ok) return;

    setError('');
    setDeletingIds((prev) => ({ ...prev, [projectId]: true }));

    try {
      await projectsAPI.deleteProject(projectId);
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

  const getFilteredAndSortedProjects = () => {
    let filtered = projects.filter((p) => {
      if (showcaseFilter && p.id !== showcaseFilter) return false;

      if (filters.searchTerm) {
        const searchLower = filters.searchTerm.toLowerCase();
        const nameMatch = p.project_name?.toLowerCase().includes(searchLower);
        const langMatch = p.primary_language?.toLowerCase().includes(searchLower);
        if (!nameMatch && !langMatch) return false;
      }

      if (filters.language !== 'all' && p.primary_language !== filters.language) {
        return false;
      }

      if (filters.hasTests === 'yes' && !p.has_tests) return false;
      if (filters.hasTests === 'no' && p.has_tests) return false;

      return true;
    });

    filtered.sort((a, b) => {
      switch (filters.sortBy) {
        case 'name':
          return (a.project_name || '').localeCompare(b.project_name || '');
        case 'language':
          return (a.primary_language || '').localeCompare(b.primary_language || '');
        case 'files':
          return (b.total_files || 0) - (a.total_files || 0);
        case 'curated': {
          if (customProjectOrder.length === 0) return 0;
          const aIdx = customProjectOrder.indexOf(a.id);
          const bIdx = customProjectOrder.indexOf(b.id);
          if (aIdx === -1 && bIdx === -1) return 0;
          if (aIdx === -1) return 1;
          if (bIdx === -1) return -1;
          return aIdx - bIdx;
        }
        case 'date':
        default: {
          const dateA = a.last_modified_date || '';
          const dateB = b.last_modified_date || '';
          return dateB.localeCompare(dateA);
        }
      }
    });

    return filtered;
  };

  const filteredProjects = getFilteredAndSortedProjects();
  const uniqueLanguages = [...new Set(projects.map((p) => p.primary_language).filter(Boolean))].sort();

  async function handleThumbnailDelete(projectId, compositeId) {
    const apiId = compositeId || projectId;
    if (!apiId || !String(apiId).includes(':')) return;

    setThumbnailLoading((prev) => ({ ...prev, [projectId]: true }));
    setThumbnailErrors((prev) => ({ ...prev, [projectId]: null }));

    try {
      await projectsAPI.deleteThumbnail(apiId);
      setThumbnailUrls((prev) => {
        if (prev[projectId]) URL.revokeObjectURL(prev[projectId]);
        return { ...prev, [projectId]: null };
      });
    } catch (e) {
      setThumbnailErrors((prev) => ({ ...prev, [projectId]: 'Failed to remove thumbnail' }));
    } finally {
      setThumbnailLoading((prev) => ({ ...prev, [projectId]: false }));
    }
  }

  async function handleThumbnailUpload(projectId, compositeId, file) {
    if (!file) return;

    const apiId = compositeId || projectId;

    if (!apiId || !String(apiId).includes(':')) {
      console.error('Invalid composite_id for thumbnail upload:', { projectId, compositeId, apiId });
      setThumbnailErrors((prev) => ({
        ...prev,
        [projectId]: 'Unable to upload: missing project identifier. Please refresh the page.',
      }));
      return;
    }

    const allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!allowedTypes.includes(file.type)) {
      setThumbnailErrors((prev) => ({
        ...prev,
        [projectId]: 'Please select a valid image (JPG, PNG, GIF, or WebP)',
      }));
      return;
    }

    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      setThumbnailErrors((prev) => ({ ...prev, [projectId]: 'Image must be less than 5MB' }));
      return;
    }

    setThumbnailLoading((prev) => ({ ...prev, [projectId]: true }));
    setThumbnailErrors((prev) => ({ ...prev, [projectId]: null }));

    try {
      await projectsAPI.uploadThumbnail(apiId, file);
      const blobUrl = await projectsAPI.getThumbnail(apiId);
      setThumbnailUrls((prev) => {
        if (prev[projectId]) {
          URL.revokeObjectURL(prev[projectId]);
        }
        return { ...prev, [projectId]: blobUrl };
      });
    } catch (e) {
      console.error('Thumbnail upload failed:', e);
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
            if (blobUrl) loadedUrls.push(blobUrl);
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

    return () => {
      isCancelled = true;
      loadedUrls.forEach((url) => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, [projects]);

  const thumbnailUrlsRef = useRef(thumbnailUrls);
  useEffect(() => {
    thumbnailUrlsRef.current = thumbnailUrls;
  }, [thumbnailUrls]);

  useEffect(() => {
    return () => {
      Object.values(thumbnailUrlsRef.current).forEach((url) => {
        if (url) URL.revokeObjectURL(url);
      });
    };
  }, []);

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
    borderRadius: '20px',
    boxShadow: '0 6px 18px rgba(0, 0, 0, 0.04)',
  };

  const sectionCardStyles = {
    backgroundColor: '#fafafa',
    border: '1px solid #ededed',
    borderRadius: '16px',
    padding: '18px 20px',
  };

  const metaPillStyles = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '6px',
    padding: '10px 14px',
    backgroundColor: '#f7f7f8',
    border: '1px solid #ececec',
    borderRadius: '999px',
    fontSize: '14px',
    color: '#404040',
    fontWeight: '500',
  };

  const secondaryText = { color: '#737373' };
  const headingText = { color: '#171717' };

  return (
    <div style={pageStyles}>
      <Navigation />

      <div style={containerStyles}>
        <div
          style={{
            marginBottom: '32px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '16px',
            flexWrap: 'wrap',
          }}
        >
          <div>
            <h1
              style={{
                fontSize: '38px',
                fontWeight: '700',
                margin: '0 0 12px 0',
                ...headingText,
                letterSpacing: '-0.8px',
              }}
            >
              My Projects
            </h1>
            <p style={{ fontSize: '17px', margin: 0, ...secondaryText }}>
              View your analyzed projects, summaries, and resume bullets
            </p>
          </div>

          <button
            onClick={() => navigate('/dashboard')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '11px 20px',
              backgroundColor: 'white',
              color: '#1a1a1a',
              border: '1px solid #e5e5e5',
              borderRadius: '10px',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: '600',
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

        <div
          style={{
            ...cardStyles,
            padding: '30px',
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
                fontWeight: '600',
                margin: '0 0 10px 0',
                ...secondaryText,
                textTransform: 'uppercase',
                letterSpacing: '0.4px',
              }}
            >
              Total Projects
            </h3>
            <p
              style={{
                fontSize: '42px',
                fontWeight: '700',
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

          <div style={{ fontSize: '20px', opacity: 0.35 }}>📁</div>
        </div>

        {!loading && projects.length > 0 && (
          <div
            style={{
              ...cardStyles,
              padding: '20px',
              marginBottom: '24px',
            }}
          >
            <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
              <input
                type="text"
                placeholder="Search projects by name or language..."
                value={filters.searchTerm}
                onChange={(e) => setFilters({ ...filters, searchTerm: e.target.value })}
                style={{
                  flex: '1 1 280px',
                  padding: '12px 15px',
                  fontSize: '14px',
                  border: '1px solid #e5e5e5',
                  borderRadius: '10px',
                  outline: 'none',
                  transition: 'border-color 0.2s',
                  backgroundColor: '#fff',
                }}
                onFocus={(e) => (e.currentTarget.style.borderColor = '#a3a3a3')}
                onBlur={(e) => (e.currentTarget.style.borderColor = '#e5e5e5')}
              />

              <select
                value={filters.language}
                onChange={(e) => setFilters({ ...filters, language: e.target.value })}
                style={{
                  padding: '12px 14px',
                  fontSize: '14px',
                  border: '1px solid #e5e5e5',
                  borderRadius: '10px',
                  backgroundColor: 'white',
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="all">All Languages</option>
                {uniqueLanguages.map((lang) => (
                  <option key={lang} value={lang}>
                    {lang}
                  </option>
                ))}
              </select>

              <select
                value={filters.hasTests}
                onChange={(e) => setFilters({ ...filters, hasTests: e.target.value })}
                style={{
                  padding: '12px 14px',
                  fontSize: '14px',
                  border: '1px solid #e5e5e5',
                  borderRadius: '10px',
                  backgroundColor: 'white',
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="all">All Projects</option>
                <option value="yes">With Tests</option>
                <option value="no">Without Tests</option>
              </select>

              <select
                value={filters.sortBy}
                onChange={(e) => setFilters({ ...filters, sortBy: e.target.value })}
                style={{
                  padding: '12px 14px',
                  fontSize: '14px',
                  border: '1px solid #e5e5e5',
                  borderRadius: '10px',
                  backgroundColor: 'white',
                  cursor: 'pointer',
                  outline: 'none',
                }}
              >
                <option value="date">Sort by Date</option>
                <option value="name">Sort by Name</option>
                <option value="language">Sort by Language</option>
                <option value="files">Sort by File Count</option>
                {customProjectOrder.length > 0 && <option value="curated">Sort by Curated Order</option>}
              </select>

              {(filters.searchTerm ||
                filters.language !== 'all' ||
                filters.hasTests !== 'all' ||
                filters.sortBy !== 'date') && (
                <button
                  onClick={() =>
                    setFilters({
                      searchTerm: '',
                      language: 'all',
                      hasTests: 'all',
                      sortBy: 'date',
                    })
                  }
                  style={{
                    padding: '12px 14px',
                    fontSize: '13px',
                    fontWeight: '600',
                    border: '1px solid #e5e5e5',
                    borderRadius: '10px',
                    backgroundColor: 'white',
                    color: '#737373',
                    cursor: 'pointer',
                    whiteSpace: 'nowrap',
                  }}
                >
                  Clear Filters
                </button>
              )}
            </div>

            {showcaseFilter && (
              <div
                style={{
                  marginTop: '12px',
                  padding: '10px 16px',
                  backgroundColor: '#fffbeb',
                  border: '1px solid #f59e0b',
                  borderRadius: '10px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  fontSize: '14px',
                  color: '#92400e',
                }}
              >
                <span>⭐ Showing showcase project only</span>
                <button
                  onClick={() => setShowcaseFilter(null)}
                  style={{
                    padding: '5px 12px',
                    borderRadius: '8px',
                    border: '1px solid #f59e0b',
                    backgroundColor: 'white',
                    color: '#b45309',
                    cursor: 'pointer',
                    fontSize: '13px',
                    fontWeight: '700',
                  }}
                >
                  Show All Projects
                </button>
              </div>
            )}

            {!showcaseFilter && filteredProjects.length < projects.length && (
              <div style={{ marginTop: '12px', fontSize: '13px', color: '#737373' }}>
                Showing {filteredProjects.length} of {projects.length} projects
              </div>
            )}
          </div>
        )}

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
                fontWeight: '600',
                color: '#1a1a1a',
                backgroundColor: 'white',
                border: '1px solid #e5e5e5',
                borderRadius: '10px',
                cursor: 'pointer',
              }}
            >
              Go to Dashboard
            </button>
          </div>
        )}

        {!loading && !error && projects.length > 0 && (
          <div>
            {filteredProjects.length === 0 ? (
              <div
                style={{
                  ...cardStyles,
                  padding: '40px',
                  textAlign: 'center',
                }}
              >
                <p style={{ fontSize: '18px', ...secondaryText, margin: 0 }}>
                  No projects match your filters.
                </p>
                <button
                  onClick={() =>
                    setFilters({
                      searchTerm: '',
                      language: 'all',
                      hasTests: 'all',
                      sortBy: 'date',
                    })
                  }
                  style={{
                    marginTop: '16px',
                    padding: '10px 20px',
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#1a1a1a',
                    backgroundColor: 'white',
                    border: '1px solid #e5e5e5',
                    borderRadius: '10px',
                    cursor: 'pointer',
                  }}
                >
                  Clear Filters
                </button>
              </div>
            ) : (
              <>
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
                      fontSize: '18px',
                      fontWeight: '700',
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
                  >
                    {deletingAll ? 'Deleting all…' : 'Delete all projects'}
                  </button>
                </div>

                <div style={{ display: 'grid', gap: '24px' }}>
                  {filteredProjects.map((p) => {
                    const isDeleting = !!deletingIds[p.id];
                    const showcaseRank = showcaseRanks.get(p.id);
                    const isShowcase = !!showcaseRank;

                    return (
                      <div
                        key={p.id}
                        style={{
                          ...cardStyles,
                          padding: '28px',
                          opacity: isDeleting ? 0.65 : 1,
                          border: isShowcase ? '2px solid #f59e0b' : '1px solid #e5e5e5',
                          position: 'relative',
                          transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                        }}
                        onMouseEnter={(e) => {
                          e.currentTarget.style.transform = 'translateY(-2px)';
                          e.currentTarget.style.boxShadow = '0 12px 28px rgba(0, 0, 0, 0.06)';
                        }}
                        onMouseLeave={(e) => {
                          e.currentTarget.style.transform = 'translateY(0)';
                          e.currentTarget.style.boxShadow = '0 6px 18px rgba(0, 0, 0, 0.04)';
                        }}
                      >
                        <div
                          style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr auto',
                            gap: '24px',
                            alignItems: 'start',
                          }}
                        >
                          <div style={{ minWidth: 0 }}>
                            <div
                              style={{
                                display: 'flex',
                                alignItems: 'center',
                                gap: '10px',
                                flexWrap: 'wrap',
                                marginBottom: '16px',
                              }}
                            >
                              <h2
                                style={{
                                  fontSize: '32px',
                                  lineHeight: 1.1,
                                  fontWeight: '700',
                                  color: '#171717',
                                  margin: 0,
                                  letterSpacing: '-0.8px',
                                }}
                              >
                                {p.project_name || 'Unnamed Project'}
                              </h2>

                              {isShowcase && (
                                <span
                                  style={{
                                    padding: '6px 12px',
                                    borderRadius: '999px',
                                    backgroundColor: '#fef3c7',
                                    color: '#b45309',
                                    fontSize: '12px',
                                    fontWeight: '700',
                                  }}
                                >
                                  ⭐ Top {showcaseRank}
                                </span>
                              )}
                            </div>

                            <div
                              style={{
                                display: 'flex',
                                flexWrap: 'wrap',
                                gap: '12px',
                                marginBottom: '22px',
                              }}
                            >
                              <div style={metaPillStyles}>
                                <span style={{ color: '#737373' }}>Language:</span>
                                <span style={{ color: '#171717', fontWeight: '700' }}>
                                  {p.primary_language || 'Unknown'}
                                </span>
                              </div>

                              <div style={metaPillStyles}>
                                <span style={{ color: '#737373' }}>Files:</span>
                                <span style={{ color: '#171717', fontWeight: '700' }}>
                                  {p.total_files || 0}
                                </span>
                              </div>

                              <div style={metaPillStyles}>
                                <span style={{ color: '#737373' }}>Tests:</span>
                                <span style={{ color: '#171717', fontWeight: '700' }}>
                                  {p.has_tests ? 'Yes' : 'No'}
                                </span>
                              </div>

                              <div style={metaPillStyles}>
                                <span style={{ color: '#737373' }}>Updated:</span>
                                <span style={{ color: '#171717', fontWeight: '700' }}>
                                  {p.last_modified_date
                                    ? new Date(p.last_modified_date).toLocaleString('en-US', {
                                        year: 'numeric',
                                        month: 'short',
                                        day: 'numeric',
                                        hour: 'numeric',
                                        minute: '2-digit',
                                      })
                                    : 'N/A'}
                                </span>
                              </div>
                            </div>
                          </div>

                          <div
                            style={{
                              display: 'flex',
                              flexDirection: 'column',
                              alignItems: 'center',
                              gap: '10px',
                              minWidth: '140px',
                            }}
                          >
                            <div style={{ position: 'relative' }}>
                              <input
                                type="file"
                                accept="image/jpeg,image/png,image/gif,image/webp"
                                onChange={(e) => {
                                  const file = e.target.files?.[0];
                                  if (file) handleThumbnailUpload(p.id, p.composite_id, file);
                                  e.target.value = '';
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
                                  width: '132px',
                                  height: '132px',
                                  borderRadius: '18px',
                                  border: '2px dashed #d4d4d4',
                                  backgroundColor: '#fafafa',
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  overflow: 'hidden',
                                  transition: 'all 0.2s',
                                  cursor: 'pointer',
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
                                      gap: '6px',
                                      color: '#a3a3a3',
                                      fontSize: '11px',
                                      textAlign: 'center',
                                      pointerEvents: 'none',
                                    }}
                                  >
                                    <span style={{ fontSize: '24px' }}>📷</span>
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
                                    marginTop: '6px',
                                    fontSize: '11px',
                                    color: '#B91C1C',
                                    whiteSpace: 'nowrap',
                                  }}
                                >
                                  {thumbnailErrors[p.id]}
                                </div>
                              )}
                            </div>

                            {thumbnailUrls[p.id] && !thumbnailLoading[p.id] && (
                              <button
                                onClick={() => handleThumbnailDelete(p.id, p.composite_id)}
                                style={{
                                  background: 'none',
                                  border: 'none',
                                  padding: 0,
                                  fontSize: '12px',
                                  color: '#737373',
                                  cursor: 'pointer',
                                  textDecoration: 'underline',
                                }}
                              >
                                Remove
                              </button>
                            )}
                          </div>
                        </div>

                        {p.details_error && (
                          <div
                            style={{
                              marginTop: '18px',
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

                        <div
                          style={{
                            marginTop: '20px',
                            display: 'grid',
                            gap: '16px',
                          }}
                        >
                          <div style={sectionCardStyles}>
                            <div
                              style={{
                                fontSize: '13px',
                                fontWeight: '700',
                                color: '#525252',
                                marginBottom: '10px',
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                              }}
                            >
                              Summary
                            </div>

                            {p.portfolio && p.portfolio.text_summary ? (
                              <div
                                style={{
                                  color: '#262626',
                                  lineHeight: 1.7,
                                  fontSize: '15px',
                                }}
                              >
                                {p.portfolio.text_summary}
                              </div>
                            ) : (
                              <div style={{ color: '#737373', fontSize: '15px' }}>
                                No summary found for this project yet.
                              </div>
                            )}
                          </div>

                          <div style={sectionCardStyles}>
                            <div
                              style={{
                                fontSize: '13px',
                                fontWeight: '700',
                                color: '#525252',
                                marginBottom: '12px',
                                textTransform: 'uppercase',
                                letterSpacing: '0.5px',
                              }}
                            >
                              Resume bullets
                            </div>

                            {p.resume_items === null ? (
                              <div style={{ color: '#737373', fontSize: '15px' }}>
                                Loading resume bullets...
                              </div>
                            ) : p.resume_items.length > 0 ? (
                              <ul
                                style={{
                                  margin: 0,
                                  paddingLeft: '22px',
                                  color: '#262626',
                                  display: 'grid',
                                  gap: '10px',
                                }}
                              >
                                {p.resume_items.map((ri) => (
                                  <li
                                    key={ri.id}
                                    style={{
                                      lineHeight: 1.65,
                                      fontSize: '15px',
                                    }}
                                  >
                                    {ri.resume_text}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <div style={{ color: '#737373', fontSize: '15px' }}>
                                No resume bullets found for this project yet.
                              </div>
                            )}
                          </div>
                        </div>

                        <div
                          style={{
                            marginTop: '18px',
                            paddingTop: '18px',
                            borderTop: '1px solid #efefef',
                            display: 'flex',
                            justifyContent: 'flex-end',
                          }}
                        >
                          <button
                            disabled={isDeleting || deletingAll}
                            onClick={() => handleDeleteProject(p.id, p.project_name)}
                            style={{
                              padding: '10px 16px',
                              fontSize: '13px',
                              fontWeight: '700',
                              borderRadius: '12px',
                              cursor: isDeleting || deletingAll ? 'not-allowed' : 'pointer',
                              border: '1px solid #fecaca',
                              backgroundColor: '#fee2e2',
                              color: '#991b1b',
                              whiteSpace: 'nowrap',
                            }}
                          >
                            {isDeleting ? 'Deleting…' : 'Delete project'}
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}