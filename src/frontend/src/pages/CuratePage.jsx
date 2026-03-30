import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { curationAPI } from '../services/api';
import Navigation from '../components/Navigation';

const SUPPORTED_COMPARISON_ATTRIBUTE_KEYS = new Set([
  'primary_language',
  'total_files',
  'has_tests',
  'has_readme',
  'has_ci_cd',
  'has_docker',
  'total_commits',
  'project_active_days',
  'test_coverage_estimate',
]);

export default function CuratePage() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  const [activeTab, setActiveTab] = useState(() => {
    // Restore active tab from localStorage
    return localStorage.getItem('curateActiveTab') || 'showcase';
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Data
  const [projects, setProjects] = useState([]);
  const [settings, setSettings] = useState(null);
  const [availableSkills, setAvailableSkills] = useState([]);
  const [availableAttributes, setAvailableAttributes] = useState([]);

  // Working state
  const [selectedShowcase, setSelectedShowcase] = useState([]);
  const [selectedAttributes, setSelectedAttributes] = useState([]);
  const [selectedSkills, setSelectedSkills] = useState([]);
  const [chronologyEdits, setChronologyEdits] = useState({});

  // Persist active tab to localStorage
  useEffect(() => {
    localStorage.setItem('curateActiveTab', activeTab);
  }, [activeTab]);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/login');
      return;
    }
    loadData();
  }, [isAuthenticated, navigate]);

  async function loadData() {
    setLoading(true);
    setError('');
    try {
      const [projectsData, settingsData, skillsData, attributesData] = await Promise.all([
        curationAPI.getProjects(),
        curationAPI.getSettings(),
        curationAPI.getSkills(),
        curationAPI.getAttributes(),
      ]);

      setProjects(projectsData);
      setSettings(settingsData);
      setAvailableSkills(skillsData);
      const filteredAttributes = (attributesData || []).filter((attr) =>
        SUPPORTED_COMPARISON_ATTRIBUTE_KEYS.has(attr.key)
      );
      setAvailableAttributes(filteredAttributes);

      // Initialize working state
      setSelectedShowcase(settingsData.showcase_project_ids || []);
      const initialAttributes = (settingsData.comparison_attributes || []).filter((key) =>
        SUPPORTED_COMPARISON_ATTRIBUTE_KEYS.has(key)
      );
      setSelectedAttributes(initialAttributes);
      setSelectedSkills(settingsData.highlighted_skills || []);
      
    } catch (e) {
      console.error('Error loading curation data:', e);
      setError(e?.response?.data?.detail || e?.message || 'Failed to load curation data');
    } finally {
      setLoading(false);
    }
  }

  async function saveShowcase() {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await curationAPI.saveShowcase(selectedShowcase);
      setSuccess('Showcase projects saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to save showcase projects');
    } finally {
      setSaving(false);
    }
  }

  async function saveAttributes() {
    if (selectedAttributes.length === 0) {
      setError('Select at least 1 comparison field.');
      setSuccess('');
      return;
    }
    if (selectedAttributes.length > 6) {
      setError('Select at most 6 comparison fields.');
      setSuccess('');
      return;
    }
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await curationAPI.saveAttributes(selectedAttributes);
      setSuccess('Comparison fields saved. Updated on Portfolio.');
      setTimeout(() => setSuccess(''), 3000);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to save attributes');
    } finally {
      setSaving(false);
    }
  }

  async function saveSkills() {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      await curationAPI.saveSkills(selectedSkills);
      setSuccess('Highlighted skills saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to save skills');
    } finally {
      setSaving(false);
    }
  }

  async function saveChronology(projectId) {
    setSaving(true);
    setError('');
    setSuccess('');
    try {
      const dates = chronologyEdits[projectId] || {};
      await curationAPI.saveChronology(projectId, dates);
      setSuccess('Chronology saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
      // Reload projects to show updated dates
      const projectsData = await curationAPI.getProjects();
      setProjects(projectsData);
      // Clear edit for this project
      const newEdits = { ...chronologyEdits };
      delete newEdits[projectId];
      setChronologyEdits(newEdits);
    } catch (e) {
      setError(e?.response?.data?.detail || e?.message || 'Failed to save chronology');
    } finally {
      setSaving(false);
    }
  }

  function toggleShowcase(projectId) {
    if (selectedShowcase.includes(projectId)) {
      setSelectedShowcase(selectedShowcase.filter((id) => id !== projectId));
    } else if (selectedShowcase.length < 3) {
      setSelectedShowcase([...selectedShowcase, projectId]);
    }
  }

  function toggleAttribute(attrKey) {
    if (selectedAttributes.includes(attrKey)) {
      setSelectedAttributes(selectedAttributes.filter((key) => key !== attrKey));
    } else {
      setSelectedAttributes([...selectedAttributes, attrKey]);
    }
  }

  function toggleSkill(skill) {
    if (selectedSkills.includes(skill)) {
      setSelectedSkills(selectedSkills.filter((s) => s !== skill));
    } else if (selectedSkills.length < 10) {
      setSelectedSkills([...selectedSkills, skill]);
    }
  }

  // Styles
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

  const tabStyles = (isActive) => ({
    padding: '12px 24px',
    fontSize: '14px',
    fontWeight: '500',
    border: 'none',
    borderBottom: isActive ? '2px solid #1a1a1a' : '2px solid transparent',
    backgroundColor: 'transparent',
    color: isActive ? '#1a1a1a' : '#737373',
    cursor: 'pointer',
    transition: 'all 0.2s',
  });

  const buttonStyles = {
    padding: '10px 20px',
    fontSize: '14px',
    fontWeight: '500',
    border: '1px solid #1a1a1a',
    borderRadius: '8px',
    backgroundColor: '#1a1a1a',
    color: 'white',
    cursor: 'pointer',
    transition: 'all 0.2s',
  };

  return (
    <div style={pageStyles}>
      <Navigation />

      <div style={containerStyles}>
        {/* Header */}
        <div style={{ marginBottom: '32px' }}>
          <h1
            style={{
              fontSize: '36px',
              fontWeight: '600',
              margin: '0 0 12px 0',
              color: '#1a1a1a',
              letterSpacing: '-0.5px',
            }}
          >
            Curate Your Portfolio
          </h1>
          <p style={{ fontSize: '16px', margin: 0, color: '#737373' }}>
            Customize what appears on your Portfolio page. Each tab below explains where your changes show up.
          </p>
        </div>

        <div
          style={{
            ...cardStyles,
            padding: '16px 18px',
            marginBottom: '24px',
            backgroundColor: '#f8fafc',
          }}
        >
          <div style={{ fontSize: '14px', color: '#374151', lineHeight: 1.6 }}>
            <strong>What each section controls:</strong><br />
            Showcase: highlights top projects on Portfolio cards and lists.<br />
            Project Comparison Fields: controls columns in Portfolio&apos;s Project Comparison table.<br />
            Highlighted Skills: controls prominent skills shown in the Portfolio profile section.<br />
            Chronology Correction: fixes project date timelines used in portfolio insights.
          </div>
        </div>

        {/* Success/Error Messages */}
        {success && (
          <div
            style={{
              padding: '16px 18px',
              backgroundColor: '#D1FAE5',
              color: '#065F46',
              borderRadius: '12px',
              border: '1px solid #A7F3D0',
              marginBottom: '24px',
            }}
          >
            {success}
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
            {error}
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div style={{ ...cardStyles, padding: '40px', textAlign: 'center' }}>
            <p style={{ margin: 0, fontSize: '16px', color: '#737373' }}>Loading curation options...</p>
          </div>
        )}

        {/* Main Content */}
        {!loading && (
          <div style={cardStyles}>
            {/* Tabs */}
            <div
              style={{
                borderBottom: '1px solid #e5e5e5',
                display: 'flex',
                gap: '8px',
                paddingLeft: '24px',
                overflowX: 'auto',
              }}
            >
              <button style={tabStyles(activeTab === 'showcase')} onClick={() => setActiveTab('showcase')}>
                Showcase (Top 3)
              </button>
              <button style={tabStyles(activeTab === 'attributes')} onClick={() => setActiveTab('attributes')}>
                Project Comparison Fields
              </button>
              <button style={tabStyles(activeTab === 'skills')} onClick={() => setActiveTab('skills')}>
                Highlighted Skills
              </button>
              <button style={tabStyles(activeTab === 'chronology')} onClick={() => setActiveTab('chronology')}>
                Chronology Correction
              </button>
            </div>

            {/* Tab Content */}
            <div style={{ padding: '32px' }}>
              {/* Showcase Tab */}
              {activeTab === 'showcase' && (
                <div>
                  <h3 style={{ fontSize: '20px', fontWeight: '600', margin: '0 0 16px 0' }}>
                    Select Top 3 Showcase Projects
                  </h3>
                  <p style={{ fontSize: '14px', color: '#737373', marginBottom: '24px' }}>
                    Choose up to 3 projects to highlight on Portfolio. Selected: {selectedShowcase.length}/3.
                    The number in each row is the showcase order (1st–3rd pick).
                  </p>

                  <div style={{ display: 'grid', gap: '12px', marginBottom: '24px' }}>
                    {projects.map((project) => {
                      const isSelected = selectedShowcase.includes(project.id);
                      const showcaseRank = isSelected ? selectedShowcase.indexOf(project.id) + 1 : null;
                      return (
                        <div
                          key={project.id}
                          onClick={() => toggleShowcase(project.id)}
                          style={{
                            padding: '16px',
                            border: isSelected ? '2px solid #1a1a1a' : '1px solid #e5e5e5',
                            borderRadius: '12px',
                            cursor: selectedShowcase.length < 3 || isSelected ? 'pointer' : 'not-allowed',
                            backgroundColor: isSelected ? '#fafafa' : 'white',
                            transition: 'all 0.2s',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                            <div
                              role="img"
                              aria-label={
                                showcaseRank != null
                                  ? `Showcase order ${showcaseRank} of 3`
                                  : 'Not selected for showcase'
                              }
                              style={{
                                boxSizing: 'border-box',
                                minWidth: '22px',
                                width: '22px',
                                height: '22px',
                                border: isSelected ? '2px solid #1a1a1a' : '2px solid #d4d4d4',
                                borderRadius: '4px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                backgroundColor: isSelected ? '#1a1a1a' : 'white',
                              }}
                            >
                              {showcaseRank != null && (
                                <span
                                  style={{
                                    color: 'white',
                                    fontSize: '12px',
                                    fontWeight: '700',
                                    lineHeight: 1,
                                  }}
                                >
                                  {showcaseRank}
                                </span>
                              )}
                            </div>
                            <div style={{ flex: 1 }}>
                              <strong style={{ fontSize: '16px' }}>{project.project_name}</strong>
                              <div style={{ fontSize: '13px', color: '#737373', marginTop: '4px' }}>
                                {project.primary_language} • {project.total_files} files
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <button disabled={saving} onClick={saveShowcase} style={buttonStyles}>
                    {saving ? 'Saving...' : 'Save Showcase Projects'}
                  </button>
                </div>
              )}

              {/* Attributes Tab */}
              {activeTab === 'attributes' && (
                <div>
                  <h3 style={{ fontSize: '20px', fontWeight: '600', margin: '0 0 16px 0' }}>
                    Select Project Comparison Fields
                  </h3>
                  <p style={{ fontSize: '14px', color: '#737373', marginBottom: '24px' }}>
                    Choose which fields appear in your Portfolio project comparison view. Selected:{' '}
                    {selectedAttributes.length}/6
                  </p>
                  <p style={{ fontSize: '13px', color: '#737373', marginTop: '-12px', marginBottom: '20px' }}>
                    Tip: after saving, open Portfolio to see the comparison block update.
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '12px', marginBottom: '24px' }}>
                    {availableAttributes.map((attr) => {
                      const isSelected = selectedAttributes.includes(attr.key);
                      return (
                        <div
                          key={attr.key}
                          onClick={() => toggleAttribute(attr.key)}
                          style={{
                            padding: '16px',
                            border: isSelected ? '2px solid #1a1a1a' : '1px solid #e5e5e5',
                            borderRadius: '12px',
                            cursor: 'pointer',
                            backgroundColor: isSelected ? '#fafafa' : 'white',
                            transition: 'all 0.2s',
                          }}
                        >
                          <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
                            <div
                              style={{
                                width: '20px',
                                height: '20px',
                                marginTop: '2px',
                                border: isSelected ? '2px solid #1a1a1a' : '2px solid #d4d4d4',
                                borderRadius: '4px',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                backgroundColor: isSelected ? '#1a1a1a' : 'white',
                                flexShrink: 0,
                              }}
                            >
                              {isSelected && <span style={{ color: 'white', fontSize: '14px' }}>✓</span>}
                            </div>
                            <div>
                              <strong style={{ fontSize: '14px' }}>{attr.description}</strong>
                              {attr.is_default && (
                                <span
                                  style={{
                                    marginLeft: '8px',
                                    fontSize: '11px',
                                    padding: '2px 6px',
                                    backgroundColor: '#e5e5e5',
                                    borderRadius: '4px',
                                  }}
                                >
                                  Default
                                </span>
                              )}
                              <div style={{ fontSize: '12px', color: '#a3a3a3', marginTop: '4px' }}>
                                {attr.key}
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  <button disabled={saving} onClick={saveAttributes} style={buttonStyles}>
                    {saving ? 'Saving...' : 'Save Attributes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => navigate('/portfolio')}
                    style={{
                      ...buttonStyles,
                      marginLeft: '10px',
                      backgroundColor: 'white',
                      color: '#1a1a1a',
                      border: '1px solid #e5e5e5',
                    }}
                  >
                    Go to Portfolio
                  </button>
                </div>
              )}

              {/* Skills Tab */}
              {activeTab === 'skills' && (
                <div>
                  <h3 style={{ fontSize: '20px', fontWeight: '600', margin: '0 0 16px 0' }}>
                    Highlight Skills (Max 10)
                  </h3>
                  <p style={{ fontSize: '14px', color: '#737373', marginBottom: '24px' }}>
                    Select up to 10 skills to emphasize in your Portfolio profile summary. Selected: {selectedSkills.length}/10
                  </p>

                  <div
                    style={{
                      display: 'flex',
                      flexWrap: 'wrap',
                      gap: '8px',
                      marginBottom: '24px',
                      maxHeight: '400px',
                      overflowY: 'auto',
                      padding: '16px',
                      border: '1px solid #e5e5e5',
                      borderRadius: '12px',
                    }}
                  >
                    {availableSkills.map((skill) => {
                      const isSelected = selectedSkills.includes(skill);
                      return (
                        <button
                          key={skill}
                          onClick={() => toggleSkill(skill)}
                          disabled={!isSelected && selectedSkills.length >= 10}
                          style={{
                            padding: '8px 16px',
                            fontSize: '14px',
                            border: isSelected ? '2px solid #1a1a1a' : '1px solid #e5e5e5',
                            borderRadius: '20px',
                            backgroundColor: isSelected ? '#1a1a1a' : 'white',
                            color: isSelected ? 'white' : '#1a1a1a',
                            cursor: !isSelected && selectedSkills.length >= 10 ? 'not-allowed' : 'pointer',
                            opacity: !isSelected && selectedSkills.length >= 10 ? 0.5 : 1,
                            transition: 'all 0.2s',
                          }}
                        >
                          {skill}
                        </button>
                      );
                    })}
                  </div>

                  <button disabled={saving} onClick={saveSkills} style={buttonStyles}>
                    {saving ? 'Saving...' : 'Save Highlighted Skills'}
                  </button>
                </div>
              )}

              {/* Chronology Tab */}
              {activeTab === 'chronology' && (
                <div>
                  <h3 style={{ fontSize: '20px', fontWeight: '600', margin: '0 0 16px 0' }}>
                    Correct Project Dates
                  </h3>
                  <p style={{ fontSize: '14px', color: '#737373', marginBottom: '24px' }}>
                    Override detected dates with custom values (YYYY-MM-DD). These updates affect portfolio timeline-based insights.
                  </p>

                  <div style={{ display: 'grid', gap: '24px' }}>
                    {projects.map((project) => {
                      const edits = chronologyEdits[project.id] || {};
                      return (
                        <div
                          key={project.id}
                          style={{
                            padding: '20px',
                            border: '1px solid #e5e5e5',
                            borderRadius: '12px',
                          }}
                        >
                          <strong style={{ fontSize: '16px', display: 'block', marginBottom: '16px' }}>
                            {project.project_name}
                          </strong>

                          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
                            <div>
                              <label htmlFor={`last-commit-${project.id}`} style={{ fontSize: '13px', color: '#737373', display: 'block', marginBottom: '4px' }}>
                                Last Commit Date
                              </label>
                              <input
                                id={`last-commit-${project.id}`}
                                type="date"
                                value={edits.last_commit_date || project.effective_last_commit_date?.split('T')[0] || ''}
                                onChange={(e) =>
                                  setChronologyEdits({
                                    ...chronologyEdits,
                                    [project.id]: { ...edits, last_commit_date: e.target.value },
                                  })
                                }
                                style={{
                                  width: '100%',
                                  padding: '8px',
                                  fontSize: '14px',
                                  border: '1px solid #e5e5e5',
                                  borderRadius: '6px',
                                }}
                              />
                            </div>

                            <div>
                              <label htmlFor={`last-modified-${project.id}`} style={{ fontSize: '13px', color: '#737373', display: 'block', marginBottom: '4px' }}>
                                Last Modified Date
                              </label>
                              <input
                                id={`last-modified-${project.id}`}
                                type="date"
                                value={edits.last_modified_date || project.effective_last_modified_date?.split('T')[0] || ''}
                                onChange={(e) =>
                                  setChronologyEdits({
                                    ...chronologyEdits,
                                    [project.id]: { ...edits, last_modified_date: e.target.value },
                                  })
                                }
                                style={{
                                  width: '100%',
                                  padding: '8px',
                                  fontSize: '14px',
                                  border: '1px solid #e5e5e5',
                                  borderRadius: '6px',
                                }}
                              />
                            </div>

                            <div>
                              <label htmlFor={`start-date-${project.id}`} style={{ fontSize: '13px', color: '#737373', display: 'block', marginBottom: '4px' }}>
                                Project Start Date
                              </label>
                              <input
                                id={`start-date-${project.id}`}
                                type="date"
                                value={edits.project_start_date || project.effective_project_start_date?.split('T')[0] || ''}
                                onChange={(e) =>
                                  setChronologyEdits({
                                    ...chronologyEdits,
                                    [project.id]: { ...edits, project_start_date: e.target.value },
                                  })
                                }
                                style={{
                                  width: '100%',
                                  padding: '8px',
                                  fontSize: '14px',
                                  border: '1px solid #e5e5e5',
                                  borderRadius: '6px',
                                }}
                              />
                            </div>

                            <div>
                              <label htmlFor={`end-date-${project.id}`} style={{ fontSize: '13px', color: '#737373', display: 'block', marginBottom: '4px' }}>
                                Project End Date
                              </label>
                              <input
                                id={`end-date-${project.id}`}
                                type="date"
                                value={edits.project_end_date || project.effective_project_end_date?.split('T')[0] || ''}
                                onChange={(e) =>
                                  setChronologyEdits({
                                    ...chronologyEdits,
                                    [project.id]: { ...edits, project_end_date: e.target.value },
                                  })
                                }
                                style={{
                                  width: '100%',
                                  padding: '8px',
                                  fontSize: '14px',
                                  border: '1px solid #e5e5e5',
                                  borderRadius: '6px',
                                }}
                              />
                            </div>
                          </div>

                          {chronologyEdits[project.id] && (
                            <button
                              disabled={saving}
                              onClick={() => saveChronology(project.id)}
                              style={{ ...buttonStyles, marginTop: '16px' }}
                            >
                              {saving ? 'Saving...' : 'Save Dates'}
                            </button>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

            </div>
          </div>
        )}
      </div>
    </div>
  );
}

