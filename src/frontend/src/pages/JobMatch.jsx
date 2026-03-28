import React, { useState, useEffect, useCallback } from 'react';
import Navigation from '../components/Navigation';
import { resumeAPI } from '../services/api';
import { useNavigationBlock } from '../contexts/NavigationBlockContext';

const ScoreBadge = ({ score, label, color, size = 'large' }) => {
  const dim = size === 'small' ? '52px' : '80px';
  const fontSize = size === 'small' ? '16px' : '22px';
  const labelSize = size === 'small' ? '11px' : '13px';
  const border = size === 'small' ? '4px' : '5px';
  return (
    <div style={{ textAlign: 'center' }}>
      <div style={{
        width: dim,
        height: dim,
        borderRadius: '50%',
        border: `${border} solid ${color}`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        margin: '0 auto 8px',
        fontSize,
        fontWeight: '700',
        color,
      }}>
        {score}
      </div>
      <div style={{ fontSize: labelSize, color: '#666', fontWeight: '500' }}>{label}</div>
    </div>
  );
};

const PillList = ({ items, color, bg }) => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
    {items.map((item, i) => (
      <span key={i} style={{
        padding: '4px 12px',
        borderRadius: '999px',
        backgroundColor: bg,
        color,
        fontSize: '13px',
        fontWeight: '500',
      }}>
        {item}
      </span>
    ))}
  </div>
);

const BulletList = ({ items, prefix }) => (
  <ul style={{ margin: 0, paddingLeft: '20px' }}>
    {items.map((item, i) => (
      <li key={i} style={{ fontSize: '14px', color: '#374151', marginBottom: '4px' }}>
        {prefix} {item}
      </li>
    ))}
  </ul>
);

const Section = ({ title, children }) => (
  <div style={{ marginBottom: '24px' }}>
    <h3 style={{ fontSize: '15px', fontWeight: '600', color: '#1a1a1a', marginBottom: '10px' }}>
      {title}
    </h3>
    {children}
  </div>
);

const scoreColor = (score) => {
  if (score >= 75) return '#16a34a';
  if (score >= 50) return '#d97706';
  return '#dc2626';
};

const AnalysisDetail = ({ result }) => (
  <div>
    <div style={{
      display: 'flex',
      gap: '40px',
      justifyContent: 'center',
      paddingBottom: '28px',
      marginBottom: '28px',
      borderBottom: '1px solid #f0f0f0',
    }}>
      <ScoreBadge score={result.overall_score} label="Overall Match" color={scoreColor(result.overall_score)} />
      <ScoreBadge score={result.skills_score} label="Skills Match" color={scoreColor(result.skills_score)} />
      <ScoreBadge score={result.experience_score} label="Experience Match" color={scoreColor(result.experience_score)} />
    </div>

    {result.summary && (
      <Section title="Summary">
        <p style={{ fontSize: '14px', color: '#374151', lineHeight: '1.6', margin: 0 }}>
          {result.summary}
        </p>
      </Section>
    )}

    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
      {result.matched_skills?.length > 0 && (
        <Section title="Matched Skills">
          <PillList items={result.matched_skills} color="#15803d" bg="#dcfce7" />
        </Section>
      )}
      {result.missing_skills?.length > 0 && (
        <Section title="Skills to Develop">
          <PillList items={result.missing_skills} color="#b45309" bg="#fef3c7" />
        </Section>
      )}
    </div>

    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
      {result.matched_requirements?.length > 0 && (
        <Section title="Requirements You Meet">
          <BulletList items={result.matched_requirements} prefix="✓" />
        </Section>
      )}
      {result.unmet_requirements?.length > 0 && (
        <Section title="Requirements to Address">
          <BulletList items={result.unmet_requirements} prefix="✗" />
        </Section>
      )}
    </div>

    {result.recommendations?.length > 0 && (
      <Section title="Recommendations">
        <BulletList items={result.recommendations} prefix="💡" />
      </Section>
    )}
  </div>
);

const SavedMatchCard = ({ match, isExpanded, onToggle, onDelete }) => {
  const snippet = match.job_description
    ? match.job_description.length > 120
      ? match.job_description.slice(0, 120) + '...'
      : match.job_description
    : 'No description';

  const date = match.created_at
    ? new Date(match.created_at + (match.created_at.endsWith('Z') ? '' : 'Z')).toLocaleDateString('en-US', {
        month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit',
      })
    : '';

  return (
    <div style={{
      backgroundColor: 'white',
      borderRadius: '12px',
      border: isExpanded ? '2px solid #1a1a1a' : '1px solid #e5e5e5',
      overflow: 'hidden',
      transition: 'border-color 0.2s',
    }}>
      <div
        onClick={onToggle}
        style={{
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          cursor: 'pointer',
          userSelect: 'none',
        }}
      >
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '50%',
          border: `3px solid ${scoreColor(match.overall_score)}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '15px',
          fontWeight: '700',
          color: scoreColor(match.overall_score),
          flexShrink: 0,
        }}>
          {match.overall_score}
        </div>

        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontSize: '14px', color: '#1a1a1a', fontWeight: '500', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {snippet}
          </div>
          <div style={{ fontSize: '12px', color: '#999', marginTop: '2px' }}>{date}</div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          <button
            onClick={(e) => { e.stopPropagation(); onDelete(); }}
            title="Delete match"
            style={{
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontSize: '16px',
              color: '#999',
              padding: '4px 6px',
              borderRadius: '4px',
              lineHeight: 1,
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = '#dc2626'; e.currentTarget.style.backgroundColor = '#fef2f2'; }}
            onMouseLeave={(e) => { e.currentTarget.style.color = '#999'; e.currentTarget.style.backgroundColor = 'transparent'; }}
          >
            ✕
          </button>
          <span style={{ fontSize: '18px', color: '#999', transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
            ▾
          </span>
        </div>
      </div>

      {isExpanded && (
        <div style={{ padding: '0 20px 20px', borderTop: '1px solid #f0f0f0' }}>
          <div style={{ paddingTop: '20px' }}>
            <AnalysisDetail result={match} />
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', paddingTop: '8px' }}>
            <button
              onClick={onToggle}
              style={{
                padding: '6px 16px',
                backgroundColor: '#f5f5f5',
                color: '#666',
                border: 'none',
                borderRadius: '6px',
                fontSize: '13px',
                cursor: 'pointer',
                fontWeight: '500',
              }}
              onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#e5e5e5'; }}
              onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#f5f5f5'; }}
            >
              Minimize
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

const JobMatch = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [savedMatches, setSavedMatches] = useState([]);
  const [expandedId, setExpandedId] = useState(null);
  const [loadingMatches, setLoadingMatches] = useState(true);
  const { setNavigationBlocked } = useNavigationBlock();

  useEffect(() => {
    setNavigationBlocked(loading);
    return () => setNavigationBlocked(false);
  }, [loading, setNavigationBlocked]);

  useEffect(() => {
    if (loading) {
      const handler = (e) => {
        e.preventDefault();
        e.returnValue = '';
      };
      window.addEventListener('beforeunload', handler);
      return () => window.removeEventListener('beforeunload', handler);
    }
  }, [loading]);

  const fetchSavedMatches = useCallback(async () => {
    try {
      const data = await resumeAPI.listJobMatches();
      setSavedMatches(data);
    } catch {
      // silently ignore load errors
    } finally {
      setLoadingMatches(false);
    }
  }, []);

  useEffect(() => {
    fetchSavedMatches();
  }, [fetchSavedMatches]);

  const handleAnalyze = async () => {
    if (jobDescription.trim().length < 50) {
      setError('Please paste a longer job description (at least 50 characters).');
      return;
    }
    setError('');
    setLoading(true);
    setResult(null);
    try {
      const data = await resumeAPI.analyzeJobMatch(jobDescription);
      setResult(data);
      setSavedMatches((prev) => [data, ...prev]);
      setJobDescription('');
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (matchId) => {
    try {
      await resumeAPI.deleteJobMatch(matchId);
      setSavedMatches((prev) => prev.filter((m) => m.id !== matchId));
      if (expandedId === matchId) setExpandedId(null);
      if (result?.id === matchId) setResult(null);
    } catch {
      // silently ignore delete errors
    }
  };

  const handleToggle = (matchId) => {
    setExpandedId((prev) => (prev === matchId ? null : matchId));
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#fafafa' }}>
      <Navigation />
      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '32px 24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: '700', color: '#1a1a1a', marginBottom: '4px' }}>
          Job Description Match
        </h1>
        <p style={{ color: '#666', fontSize: '14px', marginBottom: '28px' }}>
          Paste a job description below to see how well your skills and projects align with the role.
        </p>

        {/* Input section */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          border: '1px solid #e5e5e5',
          padding: '24px',
          marginBottom: '24px',
        }}>
          <label style={{ display: 'block', fontSize: '14px', fontWeight: '600', color: '#374151', marginBottom: '8px' }}>
            Job Description
          </label>
          <textarea
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the full job description here..."
            rows={12}
            disabled={loading}
            style={{
              width: '100%',
              padding: '12px',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '14px',
              fontFamily: 'inherit',
              resize: 'vertical',
              outline: 'none',
              boxSizing: 'border-box',
              color: '#1a1a1a',
              lineHeight: '1.5',
              opacity: loading ? 0.6 : 1,
            }}
          />
          {error && (
            <p style={{ color: '#dc2626', fontSize: '13px', marginTop: '8px' }}>{error}</p>
          )}
          <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button
              onClick={handleAnalyze}
              disabled={loading}
              style={{
                padding: '10px 24px',
                backgroundColor: loading ? '#9ca3af' : '#1a1a1a',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                fontWeight: '600',
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? 'Analyzing...' : 'Analyze Match'}
            </button>
            {loading && (
              <span style={{ fontSize: '13px', color: '#666' }}>
                This may take up to 30 seconds...
              </span>
            )}
          </div>
        </div>

        {/* Current analysis result */}
        {result && (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e5e5e5',
            padding: '28px',
            marginBottom: '32px',
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '17px', fontWeight: '600', color: '#1a1a1a', margin: 0 }}>Latest Analysis</h2>
              <button
                onClick={() => setResult(null)}
                style={{
                  padding: '4px 12px',
                  backgroundColor: '#f5f5f5',
                  color: '#666',
                  border: 'none',
                  borderRadius: '6px',
                  fontSize: '13px',
                  cursor: 'pointer',
                  fontWeight: '500',
                }}
                onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = '#e5e5e5'; }}
                onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = '#f5f5f5'; }}
              >
                Dismiss
              </button>
            </div>
            <AnalysisDetail result={result} />
          </div>
        )}

        {/* Saved matches */}
        {!loadingMatches && savedMatches.length > 0 && (
          <div>
            <h2 style={{ fontSize: '17px', fontWeight: '600', color: '#1a1a1a', marginBottom: '16px' }}>
              Saved Matches ({savedMatches.length})
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {savedMatches.map((match) => (
                <SavedMatchCard
                  key={match.id}
                  match={match}
                  isExpanded={expandedId === match.id}
                  onToggle={() => handleToggle(match.id)}
                  onDelete={() => handleDelete(match.id)}
                />
              ))}
            </div>
          </div>
        )}

        {!loadingMatches && savedMatches.length === 0 && !result && (
          <div style={{
            textAlign: 'center',
            padding: '40px 20px',
            color: '#999',
            fontSize: '14px',
          }}>
            No saved job matches yet. Analyze a job description to get started.
          </div>
        )}
      </div>
    </div>
  );
};

export default JobMatch;
