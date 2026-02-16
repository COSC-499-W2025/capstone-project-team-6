import { useCallback, useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import { useAuth } from '../contexts/AuthContext';
import { portfoliosAPI } from '../services/api';

const formatTimestamp = (value) => {
  if (!value) return 'N/A';
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
};

const Portfolio = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState(null);
  const [selectedPortfolioDetail, setSelectedPortfolioDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState('');
  const [detailError, setDetailError] = useState('');

  const loadPortfolios = useCallback(async () => {
    setError('');
    setLoading(true);
    setSelectedPortfolioDetail(null);
    try {
      const data = await portfoliosAPI.listPortfolios();
      setPortfolios(data ?? []);
      setSelectedPortfolioId(data?.[0]?.analysis_uuid ?? null);
    } catch (err) {
      setError(err?.response?.data?.detail || err?.message || 'Failed to load portfolios');
      setPortfolios([]);
      setSelectedPortfolioId(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }

    loadPortfolios();
  }, [isAuthenticated, navigate, loadPortfolios]);

  useEffect(() => {
    if (!selectedPortfolioId) {
      setSelectedPortfolioDetail(null);
      setDetailError('');
      return;
    }

    let cancelled = false;
    setDetailLoading(true);
    setDetailError('');
    setSelectedPortfolioDetail(null);

    portfoliosAPI
      .getPortfolioDetail(selectedPortfolioId)
      .then((detail) => {
        if (!cancelled) {
          setSelectedPortfolioDetail(detail);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setDetailError(
            err?.response?.data?.detail || err?.message || 'Unable to load portfolio details'
          );
        }
      })
      .finally(() => {
        if (!cancelled) {
          setDetailLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedPortfolioId]);

  const selectedSummaryEntry = useMemo(
    () => portfolios.find((portfolio) => portfolio.analysis_uuid === selectedPortfolioId) ?? null,
    [portfolios, selectedPortfolioId]
  );

  const totalProjects =
    selectedPortfolioDetail?.total_projects ?? selectedSummaryEntry?.total_projects ?? 0;
  const analysisType =
    selectedPortfolioDetail?.analysis_type ?? selectedSummaryEntry?.analysis_type ?? 'N/A';
  const heroTimestamp =
    selectedPortfolioDetail?.analysis_timestamp ?? selectedSummaryEntry?.analysis_timestamp ?? null;

  const displaySummary = useMemo(() => {
    const summary = selectedPortfolioDetail?.summary;
    if (!summary) return 'This portfolio does not yet have a readable summary.';
    return (
      summary.text_summary ||
      summary.analysis_summary ||
      summary.llm_summary ||
      summary.brief ||
      'This portfolio does not yet have a readable summary.'
    );
  }, [selectedPortfolioDetail]);

  const projectList = selectedPortfolioDetail?.projects ?? [];
  const portfolioItems =
    selectedPortfolioDetail?.portfolio_items ||
    selectedPortfolioDetail?.items ||
    selectedPortfolioDetail?.portfolio ||
    [];
  const skillTags = useMemo(() => {
    const rawSkills = selectedPortfolioDetail?.skills;
    if (Array.isArray(rawSkills) && rawSkills.length > 0) {
      return rawSkills;
    }

    const skillCounts = new Map();
    for (const item of portfolioItems) {
      const skills = item?.skills_exercised;
      const normalizedSkills = Array.isArray(skills)
        ? skills
        : typeof skills === 'string'
          ? skills.split(',').map((skill) => skill.trim())
          : [];
      for (const skill of normalizedSkills) {
        if (!skill) continue;
        skillCounts.set(skill, (skillCounts.get(skill) ?? 0) + 1);
      }
    }

    return [...skillCounts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 10)
      .map(([skill, count]) => ({ skill, count }));
  }, [selectedPortfolioDetail, portfolioItems]);

  const handleSelectPortfolio = (portfolioId) => {
    if (portfolioId === selectedPortfolioId) return;
    setSelectedPortfolioId(portfolioId);
  };

  const renderJsonBlock = (data) => (
    <pre
      style={{
        whiteSpace: 'pre-wrap',
        wordBreak: 'break-word',
        fontSize: '12px',
        color: '#111827',
        backgroundColor: '#f9fafb',
        padding: '12px',
        borderRadius: '10px',
        border: '1px solid #e5e7eb',
        maxHeight: '400px',
        overflow: 'auto',
      }}
    >
      {JSON.stringify(data, null, 2)}
    </pre>
  );

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#fafafa' }}>
      <Navigation />
      <div style={{ maxWidth: '1400px', margin: '0 auto', padding: '32px 24px 48px' }}>
        {loading ? (
          <div
            style={{
              backgroundColor: 'white',
              padding: '40px',
              borderRadius: '16px',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)',
              textAlign: 'center',
            }}
          >
            <p style={{ margin: 0, fontSize: '18px', color: '#4b5563' }}>Loading portfolios...</p>
          </div>
        ) : error ? (
          <div
            style={{
              backgroundColor: '#fee2e2',
              color: '#991b1b',
              padding: '24px',
              borderRadius: '16px',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)',
            }}
          >
            <p style={{ margin: 0, fontWeight: '600' }}>Error loading portfolios</p>
            <p style={{ margin: '8px 0 0' }}>{error}</p>
            <button
              type="button"
              onClick={loadPortfolios}
              style={{
                marginTop: '12px',
                padding: '8px 16px',
                borderRadius: '8px',
                border: 'none',
                backgroundColor: '#1d4ed8',
                color: 'white',
                cursor: 'pointer',
              }}
            >
              Retry
            </button>
          </div>
        ) : portfolios.length === 0 ? (
          <div
            style={{
              backgroundColor: 'white',
              padding: '40px',
              borderRadius: '16px',
              textAlign: 'center',
              boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)',
            }}
          >
            <h2 style={{ margin: '0 0 12px', fontSize: '28px', color: '#111827' }}>
              No portfolio analyses yet
            </h2>
            <p style={{ margin: 0, color: '#4b5563' }}>
              Upload your project ZIP on the dashboard to start analyzing your work.
            </p>
          </div>
        ) : (
          <div
            style={{
              display: 'grid',
              gap: '24px',
              gridTemplateColumns: '2fr 1fr',
              alignItems: 'stretch',
            }}
          >
            <section
              style={{
                backgroundColor: 'white',
                padding: '32px',
                borderRadius: '20px',
                boxShadow: '0 20px 40px rgba(15, 23, 42, 0.06)',
              }}
            >
              <div>
                <div
                  style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    letterSpacing: '0.2em',
                    textTransform: 'uppercase',
                    color: '#6366f1',
                    marginBottom: '12px',
                  }}
                >
                  Portfolio
                </div>
                <h1
                  style={{
                    margin: '0 0 8px',
                    fontSize: '36px',
                    color: '#0f172a',
                    fontWeight: '700',
                  }}
                >
                  Portfolio Snapshot
                </h1>
                <p style={{ margin: 0, color: '#4b5563' }}>
                  Latest analysis run: {formatTimestamp(heroTimestamp)}
                </p>
              </div>

              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
                  gap: '16px',
                  marginTop: '24px',
                }}
              >
                <div
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid #e5e7eb',
                    backgroundColor: '#f9fafb',
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: '12px',
                      letterSpacing: '0.2em',
                      textTransform: 'uppercase',
                      color: '#6b7280',
                    }}
                  >
                    Projects
                  </p>
                  <p style={{ margin: '8px 0 0', fontSize: '28px', fontWeight: '700', color: '#111827' }}>
                    {totalProjects}
                  </p>
                </div>
                <div
                  style={{
                    padding: '16px',
                    borderRadius: '12px',
                    border: '1px solid #e5e7eb',
                    backgroundColor: '#fdf2f8',
                  }}
                >
                  <p
                    style={{
                      margin: 0,
                      fontSize: '12px',
                      letterSpacing: '0.2em',
                      textTransform: 'uppercase',
                      color: '#be185d',
                    }}
                  >
                    Analysis Type
                  </p>
                  <p style={{ margin: '8px 0 0', fontSize: '20px', fontWeight: '600', color: '#111827' }}>
                    {analysisType.toUpperCase()}
                  </p>
                </div>
              </div>

              <div style={{ marginTop: '32px' }}>
                <h3 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>Highlighted skills</h3>
                {skillTags.length > 0 ? (
                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '10px',
                      marginTop: '12px',
                    }}
                  >
                    {skillTags.map((skill) => (
                      <span
                        key={skill.skill || skill.name}
                        style={{
                          padding: '6px 12px',
                          borderRadius: '999px',
                          backgroundColor: '#eef2ff',
                          color: '#4338ca',
                          fontSize: '13px',
                          fontWeight: '600',
                        }}
                      >
                        {skill.skill || skill.name}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p style={{ margin: '8px 0 0', color: '#6b7280' }}>
                    No skill highlights were captured for this run yet.
                  </p>
                )}
              </div>

              <div style={{ marginTop: '32px' }}>
                <h3 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>Portfolio Items</h3>
                {Array.isArray(portfolioItems) && portfolioItems.length > 0 ? (
                  <div
                    style={{
                      marginTop: '16px',
                      display: 'grid',
                      gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                      gap: '16px',
                    }}
                  >
                    {portfolioItems.map((item, idx) => (
                      (() => {
                        const qualityScore =
                          item.quality_score ?? item.project_statistics?.quality_score;
                        const sophisticationLevel =
                          item.sophistication_level ?? item.project_statistics?.sophistication_level;
                        const techStack = Array.isArray(item.tech_stack)
                          ? item.tech_stack.join(', ')
                          : item.tech_stack;
                        const skillsExercised = Array.isArray(item.skills_exercised)
                          ? item.skills_exercised.join(', ')
                          : item.skills_exercised;

                        return (
                          <div
                            key={`portfolio-item-${idx}`}
                            style={{
                              borderRadius: '14px',
                              border: '1px solid #e5e7eb',
                              padding: '16px',
                              backgroundColor: 'white',
                            }}
                          >
                            <strong style={{ display: 'block', marginBottom: '6px', color: '#0f172a' }}>
                              {item.title || item.project_name || `Item ${idx + 1}`}
                            </strong>
                            {item.text_summary && (
                              <p style={{ margin: 0, color: '#374151', fontSize: '14px', lineHeight: 1.5 }}>
                                {item.text_summary}
                              </p>
                            )}
                            {techStack && (
                              <p style={{ margin: '8px 0 0', color: '#6b7280', fontSize: '13px' }}>
                                Tech stack: {techStack}
                              </p>
                            )}
                            {skillsExercised && (
                              <p style={{ margin: '6px 0 0', color: '#6b7280', fontSize: '13px' }}>
                                Skills: {skillsExercised}
                              </p>
                            )}
                            {qualityScore !== undefined && (
                              <p style={{ margin: '6px 0 0', color: '#6b7280', fontSize: '13px' }}>
                                Quality score: {qualityScore}
                              </p>
                            )}
                            {sophisticationLevel && (
                              <p style={{ margin: '6px 0 0', color: '#6b7280', fontSize: '13px' }}>
                                Sophistication: {sophisticationLevel}
                              </p>
                            )}
                          </div>
                        );
                      })()
                    ))}
                  </div>
                ) : (
                  <p style={{ marginTop: '12px', color: '#6b7280' }}>
                    No portfolio items were returned by the backend yet.
                  </p>
                )}
              </div>

              <div style={{ marginTop: '32px' }}>
                <details style={{ border: '1px solid #e5e7eb', borderRadius: '12px', padding: '12px' }}>
                  <summary style={{ cursor: 'pointer', fontWeight: '600', color: '#0f172a' }}>
                    Full portfolio payload (debug)
                  </summary>
                  <div style={{ marginTop: '12px' }}>{renderJsonBlock(selectedPortfolioDetail)}</div>
                </details>
              </div>

              <div style={{ marginTop: '32px' }}>
                <h3 style={{ margin: 0, fontSize: '18px', color: '#0f172a' }}>Projects</h3>
                {projectList.length > 0 ? (
                  <ul
                    style={{
                      margin: '16px 0 0',
                      paddingLeft: '18px',
                      color: '#1f2937',
                      lineHeight: 1.6,
                    }}
                  >
                    {projectList.map((project, index) => (
                      <li key={`${project.project_name}-${index}`} style={{ marginBottom: '12px' }}>
                        <strong style={{ display: 'block', fontSize: '16px', color: '#0f172a' }}>
                          {project.project_name || project.name || 'Unnamed project'}
                        </strong>
                        <span style={{ fontSize: '13px', color: '#6b7280' }}>
                          {project.primary_language || 'Language unknown'} •{' '}
                          {project.total_files ?? '0'} files
                        </span>
                        {project.summary && (
                          <p style={{ margin: '6px 0 0', fontSize: '13px', color: '#374151' }}>
                            {project.summary}
                          </p>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ marginTop: '12px', color: '#6b7280' }}>
                    We have not yet extracted the individual projects for this portfolio.
                  </p>
                )}
              </div>
            </section>

            <section
              style={{
                backgroundColor: 'white',
                borderRadius: '20px',
                padding: '24px',
                boxShadow: '0 20px 40px rgba(15, 23, 42, 0.08)',
                border: '1px solid #e5e7eb',
              }}
            >
              <h2 style={{ margin: '0 0 16px', color: '#0f172a' }}>Available analyses</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {portfolios.map((portfolio) => {
                  const isActive = portfolio.analysis_uuid === selectedPortfolioId;
                  const projectNames = Array.isArray(portfolio.project_names)
                    ? portfolio.project_names.filter(Boolean)
                    : [];
                  return (
                    <button
                      data-testid={`portfolio-card-${portfolio.analysis_uuid}`}
                      key={portfolio.analysis_uuid}
                      type="button"
                      onClick={() => handleSelectPortfolio(portfolio.analysis_uuid)}
                      style={{
                        textAlign: 'left',
                        padding: '16px',
                        borderRadius: '12px',
                        border: isActive ? '2px solid #2563eb' : '1px solid #e5e7eb',
                        backgroundColor: isActive ? '#e0e7ff' : '#f8fafc',
                        cursor: 'pointer',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '4px',
                      }}
                    >
                      <span style={{ fontSize: '14px', fontWeight: '600', color: '#111827' }}>
                        {projectNames.length > 0 ? projectNames.join(', ') : 'Unnamed project'}
                      </span>
                      <span style={{ fontSize: '13px', color: '#4b5563' }}>
                        {formatTimestamp(portfolio.analysis_timestamp)}
                      </span>
                      <span style={{ fontSize: '14px', color: '#2563eb' }}>
                        {portfolio.total_projects ?? 0} projects
                      </span>
                    </button>
                  );
                })}
              </div>
            </section>
          </div>
        )}
      </div>
    </div>
  );
};

export default Portfolio;
