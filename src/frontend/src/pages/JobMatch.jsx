import { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import { resumeAPI } from '../services/api';

const ScoreBadge = ({ score, label, color }) => {
  const r = 34;
  const circ = 2 * Math.PI * r;
  const offset = circ * (1 - score / 100);
  return (
    <div style={{ textAlign: 'center' }}>
      <svg width="88" height="88" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="44" cy="44" r={r} fill="none" stroke="#e5e7eb" strokeWidth="6" />
        <circle
          cx="44" cy="44" r={r} fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={circ} strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.8s ease' }}
        />
        <text
          x="44" y="44" textAnchor="middle" dominantBaseline="central"
          fill={color} fontSize="15" fontWeight="700"
          style={{ transform: 'rotate(90deg)', transformOrigin: '44px 44px' }}
        >
          {score}%
        </text>
      </svg>
      <div style={{ fontSize: '13px', color: '#666', fontWeight: '500', marginTop: '4px' }}>{label}</div>
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

const JobMatch = () => {
  const [jobDescription, setJobDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [showProgress, setShowProgress] = useState(false);

  useEffect(() => {
    if (!loading) return;
    setLoadingProgress(0);
    setShowProgress(true);
    const interval = setInterval(() => {
      setLoadingProgress(prev => {
        if (prev >= 90) return prev;
        const remaining = 90 - prev;
        return prev + remaining * 0.06 + Math.random() * 2;
      });
    }, 400);
    return () => clearInterval(interval);
  }, [loading]);

  useEffect(() => {
    if (loading) return;
    if (!showProgress) return;
    setLoadingProgress(100);
    const timer = setTimeout(() => setShowProgress(false), 600);
    return () => clearTimeout(timer);
  }, [loading]);

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
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const scoreColor = (score) => {
    if (score >= 75) return '#16a34a';
    if (score >= 50) return '#d97706';
    return '#dc2626';
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
            }}
          />
          {error && (
            <p style={{ color: '#dc2626', fontSize: '13px', marginTop: '8px' }}>{error}</p>
          )}
          {!loading && (
            <div style={{ marginTop: '16px' }}>
              <button
                onClick={handleAnalyze}
                style={{
                  padding: '10px 24px',
                  backgroundColor: '#1a1a1a',
                  color: 'white',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '600',
                  cursor: 'pointer',
                }}
              >
                Analyze Match
              </button>
            </div>
          )}

          {/* Loading progress bar */}
          {showProgress && (
            <div style={{ marginTop: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                <span style={{ fontSize: '13px', color: '#666' }}>
                  {loadingProgress < 100 ? 'Analyzing your resume against the job description...' : 'Done!'}
                </span>
                <span style={{ fontSize: '13px', fontWeight: '600', color: '#1a1a1a' }}>
                  {Math.round(loadingProgress)}%
                </span>
              </div>
              <div style={{ height: '8px', backgroundColor: '#e5e7eb', borderRadius: '999px', overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${loadingProgress}%`,
                  backgroundColor: '#1a1a1a',
                  borderRadius: '999px',
                  transition: 'width 0.4s ease',
                }} />
              </div>
            </div>
          )}
        </div>

        {/* Results section */}
        {result && (
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            border: '1px solid #e5e5e5',
            padding: '28px',
          }}>
            {/* Score overview */}
            <div style={{
              display: 'flex',
              gap: '40px',
              justifyContent: 'center',
              paddingBottom: '28px',
              marginBottom: '28px',
              borderBottom: '1px solid #f0f0f0',
            }}>
              <ScoreBadge
                score={result.overall_score}
                label="Overall Match"
                color={scoreColor(result.overall_score)}
              />
              <ScoreBadge
                score={result.skills_score}
                label="Skills Match"
                color={scoreColor(result.skills_score)}
              />
              <ScoreBadge
                score={result.experience_score}
                label="Experience Match"
                color={scoreColor(result.experience_score)}
              />
            </div>

            {/* Summary */}
            {result.summary && (
              <Section title="Summary">
                <p style={{ fontSize: '14px', color: '#374151', lineHeight: '1.6', margin: 0 }}>
                  {result.summary}
                </p>
              </Section>
            )}

            {/* Skills */}
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

            {/* Requirements */}
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

            {/* Recommendations */}
            {result.recommendations?.length > 0 && (
              <Section title="Recommendations">
                <BulletList items={result.recommendations} prefix="💡" />
              </Section>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default JobMatch;
