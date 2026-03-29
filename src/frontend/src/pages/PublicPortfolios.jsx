import { useEffect, useMemo, useState } from 'react';
import Navigation from '../components/Navigation';
import { portfoliosAPI } from '../services/api';

const PAGE_SIZE = 12;

const PublicPortfolios = () => {
  const [query, setQuery] = useState('');
  const [usernameFilter, setUsernameFilter] = useState('');
  const [projectTypeFilter, setProjectTypeFilter] = useState('');
  const [languageFilter, setLanguageFilter] = useState('');
  const [hasTestsFilter, setHasTestsFilter] = useState('all');
  const [sort, setSort] = useState('newest');
  const [page, setPage] = useState(1);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);

  const [selectedId, setSelectedId] = useState(null);
  const [selectedDetail, setSelectedDetail] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  useEffect(() => {
    const timeout = setTimeout(async () => {
      setLoading(true);
      setError('');
      try {
        const hasTests =
          hasTestsFilter === 'all' ? undefined : hasTestsFilter === 'yes';
        const response = await portfoliosAPI.listPublicPortfolios({
          q: query || undefined,
          username: usernameFilter || undefined,
          project_type: projectTypeFilter || undefined,
          language: languageFilter || undefined,
          has_tests: hasTests,
          sort,
          page,
          page_size: PAGE_SIZE,
        });
        setItems(Array.isArray(response?.items) ? response.items : []);
        setTotal(response?.total ?? 0);
      } catch (err) {
        setItems([]);
        setTotal(0);
        setError(err?.response?.data?.detail || err?.message || 'Failed to load public portfolios');
      } finally {
        setLoading(false);
      }
    }, 300);

    return () => clearTimeout(timeout);
  }, [query, usernameFilter, projectTypeFilter, languageFilter, hasTestsFilter, sort, page]);

  useEffect(() => {
    if (!selectedId) {
      setSelectedDetail(null);
      return;
    }

    let cancelled = false;
    setDetailLoading(true);
    portfoliosAPI
      .getPublicPortfolioDetail(selectedId)
      .then((detail) => {
        if (!cancelled) setSelectedDetail(detail);
      })
      .catch(() => {
        if (!cancelled) setSelectedDetail(null);
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  const resetFilters = () => {
    setQuery('');
    setUsernameFilter('');
    setProjectTypeFilter('');
    setLanguageFilter('');
    setHasTestsFilter('all');
    setSort('newest');
    setPage(1);
  };

  const pageLabel = useMemo(() => {
    const start = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
    const end = Math.min(total, page * PAGE_SIZE);
    return `${start}-${end} of ${total}`;
  }, [page, total]);

  const selectedProjects = selectedDetail?.projects || [];
  const selectedSettings = selectedDetail?.portfolio_settings || {};
  const roleAssessment = useMemo(() => {
    const roles = selectedProjects
      .map((p) => p?.curated_role || p?.predicted_role)
      .filter(Boolean);
    if (roles.length === 0) return null;
    const freq = roles.reduce((acc, role) => {
      acc[role] = (acc[role] || 0) + 1;
      return acc;
    }, {});
    const [role, count] = Object.entries(freq).sort((a, b) => b[1] - a[1])[0];
    return { role, count, total: roles.length };
  }, [selectedProjects]);

  const topLanguages = useMemo(() => {
    const freq = {};
    selectedProjects.forEach((p) => {
      const lang = p?.primary_language;
      if (!lang) return;
      freq[lang] = (freq[lang] || 0) + 1;
    });
    return Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 5);
  }, [selectedProjects]);

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#fafafa' }}>
      <Navigation />
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 24px 48px' }}>
        <div style={{ marginBottom: '20px' }}>
          <h1 style={{ margin: 0, fontSize: '30px', color: '#111827' }}>Community Portfolios</h1>
          <p style={{ margin: '8px 0 0', color: '#6b7280' }}>
            Browse portfolios that users have explicitly published.
          </p>
          <p style={{ margin: '8px 0 0', color: '#2563eb', fontSize: '13px', fontWeight: '600' }}>
            Only portfolios marked Public by their owners are shown here.
          </p>
        </div>

        <section
          style={{
            backgroundColor: 'white',
            borderRadius: '14px',
            border: '1px solid #e5e7eb',
            padding: '16px',
            marginBottom: '20px',
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '2fr repeat(4, 1fr)', gap: '10px' }}>
            <input
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setPage(1);
              }}
              placeholder="Search users, projects, skills..."
              style={{ padding: '10px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}
            />
            <input
              value={usernameFilter}
              onChange={(e) => {
                setUsernameFilter(e.target.value);
                setPage(1);
              }}
              placeholder="User"
              style={{ padding: '10px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}
            />
            <input
              value={projectTypeFilter}
              onChange={(e) => {
                setProjectTypeFilter(e.target.value);
                setPage(1);
              }}
              placeholder="Project type / role"
              style={{ padding: '10px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}
            />
            <input
              value={languageFilter}
              onChange={(e) => {
                setLanguageFilter(e.target.value);
                setPage(1);
              }}
              placeholder="Language"
              style={{ padding: '10px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}
            />
            <select
              value={hasTestsFilter}
              onChange={(e) => {
                setHasTestsFilter(e.target.value);
                setPage(1);
              }}
              style={{ padding: '10px 12px', borderRadius: '8px', border: '1px solid #d1d5db' }}
            >
              <option value="all">Tests: all</option>
              <option value="yes">Has tests</option>
              <option value="no">No tests</option>
            </select>
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', alignItems: 'center' }}>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <label htmlFor="community-sort" style={{ color: '#6b7280', fontSize: '14px' }}>
                Sort:
              </label>
              <select
                id="community-sort"
                value={sort}
                onChange={(e) => {
                  setSort(e.target.value);
                  setPage(1);
                }}
                style={{ padding: '8px 10px', borderRadius: '8px', border: '1px solid #d1d5db' }}
              >
                <option value="newest">Newest</option>
                <option value="oldest">Oldest</option>
                <option value="projects_desc">Most projects</option>
                <option value="username">Username</option>
              </select>
            </div>
            <button
              type="button"
              onClick={resetFilters}
              style={{
                border: '1px solid #d1d5db',
                borderRadius: '8px',
                backgroundColor: 'white',
                cursor: 'pointer',
                padding: '8px 12px',
              }}
            >
              Reset
            </button>
          </div>
        </section>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '20px' }}>
          <section
            style={{
              backgroundColor: 'white',
              borderRadius: '14px',
              border: '1px solid #e5e7eb',
              padding: '16px',
              minHeight: '300px',
            }}
          >
            {loading ? (
              <p style={{ color: '#6b7280' }}>Loading public portfolios...</p>
            ) : error ? (
              <p style={{ color: '#b91c1c' }}>{error}</p>
            ) : items.length === 0 ? (
              <p style={{ color: '#6b7280' }}>No published portfolios match your filters yet.</p>
            ) : (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, minmax(0, 1fr))', gap: '12px' }}>
                {items.map((item) => {
                  const active = item.analysis_uuid === selectedId;
                  return (
                    <button
                      key={item.analysis_uuid}
                      type="button"
                      onClick={() => setSelectedId(item.analysis_uuid)}
                      style={{
                        textAlign: 'left',
                        borderRadius: '12px',
                        border: active ? '2px solid #2563eb' : '1px solid #e5e7eb',
                        backgroundColor: active ? '#eff6ff' : '#fff',
                        padding: '14px',
                        cursor: 'pointer',
                      }}
                    >
                      <div style={{ fontSize: '15px', fontWeight: '700', color: '#111827' }}>
                        @{item.username}
                      </div>
                      <div style={{ marginTop: '4px', color: '#4b5563', fontSize: '13px' }}>
                        {item.total_projects} project{item.total_projects !== 1 ? 's' : ''} • {item.analysis_type.toUpperCase()}
                      </div>
                      <div style={{ marginTop: '8px', color: '#6b7280', fontSize: '12px' }}>
                        {(item.project_names || []).slice(0, 3).join(', ') || 'No named projects'}
                      </div>
                      {(item.top_languages || []).length > 0 && (
                        <div style={{ marginTop: '8px', display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                          {item.top_languages.slice(0, 3).map((lang) => (
                            <span
                              key={`${item.analysis_uuid}-${lang}`}
                              style={{
                                fontSize: '11px',
                                borderRadius: '999px',
                                padding: '2px 8px',
                                backgroundColor: '#f3f4f6',
                                color: '#374151',
                              }}
                            >
                              {lang}
                            </span>
                          ))}
                        </div>
                      )}
                    </button>
                  );
                })}
              </div>
            )}

            <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <span style={{ color: '#6b7280', fontSize: '13px' }}>{pageLabel}</span>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    backgroundColor: 'white',
                    cursor: page <= 1 ? 'not-allowed' : 'pointer',
                  }}
                >
                  Prev
                </button>
                <button
                  type="button"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  style={{
                    padding: '8px 12px',
                    borderRadius: '8px',
                    border: '1px solid #d1d5db',
                    backgroundColor: 'white',
                    cursor: page >= totalPages ? 'not-allowed' : 'pointer',
                  }}
                >
                  Next
                </button>
              </div>
            </div>
          </section>

        </div>

        {!selectedId ? (
          <section style={{
            backgroundColor: 'white', borderRadius: '14px', border: '1px solid #e5e7eb',
            padding: '24px', marginTop: '20px', textAlign: 'center',
          }}>
            <p style={{ color: '#6b7280' }}>Select a portfolio card above to view the developer profile.</p>
          </section>
        ) : detailLoading ? (
          <section style={{
            backgroundColor: 'white', borderRadius: '14px', border: '1px solid #e5e7eb',
            padding: '24px', marginTop: '20px', textAlign: 'center',
          }}>
            <p style={{ color: '#6b7280' }}>Loading developer profile...</p>
          </section>
        ) : !selectedDetail ? (
          <section style={{
            backgroundColor: 'white', borderRadius: '14px', border: '1px solid #e5e7eb',
            padding: '24px', marginTop: '20px', textAlign: 'center',
          }}>
            <p style={{ color: '#b91c1c' }}>Unable to load portfolio details.</p>
          </section>
        ) : (
          <div style={{ marginTop: '20px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
            {/* Developer Profile Header */}
            <section style={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              borderRadius: '20px', padding: '36px', color: 'white',
              position: 'relative', overflow: 'hidden',
            }}>
              <div style={{
                position: 'absolute', top: 0, right: 0, width: '100%', height: '100%', opacity: 0.05,
                background: 'url("data:image/svg+xml,%3Csvg width=\'60\' height=\'60\' viewBox=\'0 0 60 60\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cg fill=\'none\' fill-rule=\'evenodd\'%3E%3Cg fill=\'%23ffffff\' fill-opacity=\'1\'%3E%3Ccircle cx=\'30\' cy=\'30\' r=\'4\'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")',
              }} />
              <div style={{ position: 'relative', zIndex: 2 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '28px', flexWrap: 'wrap', gap: '16px' }}>
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: '600', letterSpacing: '0.1em', textTransform: 'uppercase', opacity: 0.8, marginBottom: '6px' }}>
                      Developer Profile
                    </div>
                    <h2 style={{ margin: 0, fontSize: '32px', fontWeight: '800' }}>
                      @{selectedDetail.username}
                    </h2>
                  </div>
                  <div style={{
                    padding: '14px 22px', backgroundColor: 'rgba(255,255,255,0.15)',
                    borderRadius: '14px', textAlign: 'center', backdropFilter: 'blur(10px)',
                    border: '1px solid rgba(255,255,255,0.2)',
                  }}>
                    <div style={{ fontSize: '22px', fontWeight: '700', marginBottom: '2px' }}>
                      {selectedDetail.total_projects}
                    </div>
                    <div style={{ fontSize: '11px', opacity: 0.8, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Projects Analyzed
                    </div>
                  </div>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                  gap: '20px',
                }}>
                  {/* Primary Role Card */}
                  {(selectedSettings.showProfileSummary ?? true) && roleAssessment && (
                    <div style={{
                      backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '14px', padding: '20px',
                      backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.2)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                        <div style={{
                          width: '36px', height: '36px', borderRadius: '50%', backgroundColor: 'rgba(255,255,255,0.2)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px',
                        }}>
                          🎯
                        </div>
                        <div>
                          <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '600' }}>Primary Role</h4>
                          <p style={{ margin: 0, fontSize: '12px', opacity: 0.7 }}>
                            Based on {roleAssessment.total} project{roleAssessment.total !== 1 ? 's' : ''}
                          </p>
                        </div>
                      </div>
                      <div style={{ fontSize: '18px', fontWeight: '700' }}>{roleAssessment.role}</div>
                    </div>
                  )}

                  {/* Core Skills Card */}
                  {(selectedSettings.showSkills ?? true) && (selectedDetail.skills || []).length > 0 && (
                    <div style={{
                      backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '14px', padding: '20px',
                      backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.2)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                        <div style={{
                          width: '36px', height: '36px', borderRadius: '50%', backgroundColor: 'rgba(255,255,255,0.2)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px',
                        }}>
                          ⚡
                        </div>
                        <div>
                          <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '600' }}>Core Skills</h4>
                          <p style={{ margin: 0, fontSize: '12px', opacity: 0.7 }}>
                            Top {Math.min(selectedDetail.skills.length, 8)} across all projects
                          </p>
                        </div>
                      </div>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                        {selectedDetail.skills.slice(0, 8).map((skill, idx) => {
                          const label = skill?.skill || skill?.name || String(skill);
                          return (
                            <span key={`profile-skill-${idx}`} style={{
                              fontSize: '12px', padding: '4px 10px', borderRadius: '999px',
                              backgroundColor: 'rgba(255,255,255,0.2)', border: '1px solid rgba(255,255,255,0.3)',
                            }}>
                              {label}
                            </span>
                          );
                        })}
                        {selectedDetail.skills.length > 8 && (
                          <span style={{ fontSize: '12px', opacity: 0.7, alignSelf: 'center' }}>
                            +{selectedDetail.skills.length - 8} more skills
                          </span>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Languages Card */}
                  {topLanguages.length > 0 && (
                    <div style={{
                      backgroundColor: 'rgba(255,255,255,0.1)', borderRadius: '14px', padding: '20px',
                      backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.2)',
                    }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
                        <div style={{
                          width: '36px', height: '36px', borderRadius: '50%', backgroundColor: 'rgba(255,255,255,0.2)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '18px',
                        }}>
                          💻
                        </div>
                        <div>
                          <h4 style={{ margin: 0, fontSize: '15px', fontWeight: '600' }}>Languages</h4>
                          <p style={{ margin: 0, fontSize: '12px', opacity: 0.7 }}>Primary technologies</p>
                        </div>
                      </div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {topLanguages.map(([language, count]) => (
                          <div key={`profile-lang-${language}`} style={{
                            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                            backgroundColor: 'rgba(255,255,255,0.08)', borderRadius: '8px', padding: '6px 12px',
                          }}>
                            <span style={{ fontSize: '13px', fontWeight: '500' }}>{language}</span>
                            <span style={{
                              fontSize: '11px', opacity: 0.8, backgroundColor: 'rgba(255,255,255,0.15)',
                              padding: '2px 8px', borderRadius: '999px',
                            }}>
                              {count} project{count !== 1 ? 's' : ''}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* Profile Summary */}
            {(selectedSettings.showProfileSummary ?? true) && selectedDetail.summary && (
              <section style={{
                backgroundColor: 'white', borderRadius: '14px', border: '1px solid #e5e7eb', padding: '20px',
              }}>
                <h3 style={{ margin: '0 0 10px', fontSize: '16px', color: '#0f172a' }}>Profile Summary</h3>
                <p style={{ margin: 0, fontSize: '14px', color: '#374151', lineHeight: 1.6 }}>
                  {selectedDetail.summary?.analysis_summary ||
                    selectedDetail.summary?.text_summary ||
                    'Summary shared by portfolio owner.'}
                </p>
              </section>
            )}

            {/* Projects + Portfolio Highlights side by side */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
              {(selectedSettings.showProjects ?? true) && (selectedDetail.projects || []).length > 0 && (
                <section style={{
                  backgroundColor: 'white', borderRadius: '14px', border: '1px solid #e5e7eb', padding: '20px',
                }}>
                  <h3 style={{ margin: '0 0 12px', fontSize: '16px', color: '#0f172a' }}>Projects</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {(selectedDetail.projects || []).slice(0, 20).map((project, idx) => (
                      <div key={`project-${selectedDetail.analysis_uuid}-${idx}`} style={{
                        padding: '10px 14px', borderRadius: '10px', border: '1px solid #e5e7eb', backgroundColor: '#f9fafb',
                      }}>
                        <div style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>
                          {project?.project_name || project?.name || 'Unnamed project'}
                        </div>
                        <div style={{ fontSize: '12px', color: '#6b7280', marginTop: '4px' }}>
                          {project?.primary_language || 'Language unknown'}
                          {project?.total_files ? ` • ${project.total_files} files` : ''}
                          {(project?.curated_role || project?.predicted_role) && (
                            <span style={{
                              marginLeft: '8px', padding: '1px 8px', borderRadius: '999px',
                              backgroundColor: project?.curated_role ? '#f0fdf4' : '#eef2ff',
                              color: project?.curated_role ? '#166534' : '#3730a3',
                              fontSize: '11px', fontWeight: '600',
                              border: `1px solid ${project?.curated_role ? '#bbf7d0' : '#c7d2fe'}`,
                            }}>
                              {project?.curated_role || project?.predicted_role}
                            </span>
                          )}
                        </div>
                        {project?.summary && (
                          <p style={{ margin: '6px 0 0', fontSize: '12px', color: '#374151', lineHeight: 1.45 }}>
                            {project.summary}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}

              {(selectedSettings.showPortfolioItems ?? true) && (selectedDetail.portfolio_items || []).length > 0 && (
                <section style={{
                  backgroundColor: 'white', borderRadius: '14px', border: '1px solid #e5e7eb', padding: '20px',
                }}>
                  <h3 style={{ margin: '0 0 12px', fontSize: '16px', color: '#0f172a' }}>Portfolio Highlights</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                    {selectedDetail.portfolio_items.slice(0, 6).map((item, idx) => (
                      <div key={`item-${selectedDetail.analysis_uuid}-${idx}`} style={{
                        borderRadius: '10px', border: '1px solid #e5e7eb', backgroundColor: '#f9fafb', padding: '12px',
                      }}>
                        <div style={{ fontSize: '13px', fontWeight: '600', color: '#111827' }}>
                          {item.title || item.project_name || `Highlight ${idx + 1}`}
                        </div>
                        {item.text_summary && (
                          <p style={{ margin: '6px 0 0', fontSize: '12px', color: '#374151', lineHeight: 1.45 }}>
                            {item.text_summary}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </section>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PublicPortfolios;
