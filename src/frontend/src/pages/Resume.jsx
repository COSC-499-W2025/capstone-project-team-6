import { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import { projectsAPI, resumeAPI, curationAPI } from '../services/api';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const Resume = () => {
  const [projects, setProjects] = useState([]);
  const [selectedProjectIds, setSelectedProjectIds] = useState([]);

  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');

  const [generatedResume, setGeneratedResume] = useState(null);
  const [resumeFormat, setResumeFormat] = useState('markdown');
  const [includeSkills, setIncludeSkills] = useState(true);
  const [includeProjects, setIncludeProjects] = useState(true);
  const [storedResumes, setStoredResumes] = useState([]);
  const [storedResumeId, setStoredResumeId] = useState('');
  const [storedResumeTitle, setStoredResumeTitle] = useState('');
  const [storedResumeContent, setStoredResumeContent] = useState('');
  const [storedResumeFormat, setStoredResumeFormat] = useState('markdown');
  const [storedResumeLoading, setStoredResumeLoading] = useState(false);
  const [storedResumeSaving, setStoredResumeSaving] = useState(false);

  // Personal information
  const emptyPersonal = {
    name: '',
    email: '',
    phone: '',
    location: '',
    linkedIn: '',
    github: '',
    website: '',
    education: '',
    education_university: '',
    education_location: '',
    education_degree: '',
    education_start_date: '',
    education_end_date: '',
    education_awards: '',
  });
  };
  const [personalInfo, setPersonalInfo] = useState(emptyPersonal);
  const [originalPersonalInfo, setOriginalPersonalInfo] = useState(emptyPersonal);
  const [personalErrors, setPersonalErrors] = useState({});

  const validatePersonalInfo = (info) => {
    const errs = {};

    if (!info.name.trim()) {
      errs.name = 'Full name is required.';
    } else if (!/^[A-Za-z\s\-'.]+$/.test(info.name.trim())) {
      errs.name = 'Name may only contain letters, spaces, hyphens, and apostrophes.';
    } else if (info.name.trim().length > 100) {
      errs.name = 'Name must be 100 characters or fewer.';
    }

    if (!info.email.trim()) {
      errs.email = 'Email is required.';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(info.email.trim())) {
      errs.email = 'Enter a valid email address.';
    }

    const phoneTrim = info.phone.trim();
    if (phoneTrim) {
      if (!/^[+\d][\d\s\-().]{7,20}$/.test(phoneTrim)) {
        errs.phone = 'Phone may only contain digits, spaces, dashes, parentheses, or a leading +. Minimum of 7 digits required.';
      } else if ((phoneTrim.replace(/\D/g, '').length || 0) < 7) {
        errs.phone = 'Phone may only contain digits, spaces, dashes, parentheses, or a leading +. Minimum of 7 digits required.';
      }
    }

    if (info.location.trim().length > 100) {
      errs.location = 'Location must be 100 characters or fewer.';
    }

    const linkedInPattern = /^https?:\/\/(www\.)?linkedin\.com\//i;
    if (info.linkedIn.trim() && !linkedInPattern.test(info.linkedIn.trim())) {
      errs.linkedIn = 'Must start with https://linkedin.com/ or https://www.linkedin.com/';
    }

    if (info.github.trim() && !/^https?:\/\/(www\.)?github\.com\//i.test(info.github.trim())) {
      errs.github = 'Must start with https://github.com/';
    }

    if (info.website.trim() && !/^https?:\/\/.+\..+/.test(info.website.trim())) {
      errs.website = 'Must be a valid URL starting with http:// or https://';
    }

    return errs;
  };

  const onChangePersonalField = (key, value) => {
    const updated = { ...personalInfo, [key]: value };
    setPersonalInfo(updated);
    if (Object.keys(personalErrors).length > 0) {
      setPersonalErrors(validatePersonalInfo(updated));
    }
  };

  const hasOriginalPersonalInfo = Object.values(originalPersonalInfo).some((v) => (v || '').trim().length > 0);

  const hasPersonalInfoChanges = () => {
    const keys = Object.keys(emptyPersonal);
    for (const k of keys) {
      if ((personalInfo[k] || '').trim() !== (originalPersonalInfo[k] || '').trim()) return true;
    }
    return false;
  };

  const onCancelPersonalInfo = () => {
    setPersonalInfo({ ...originalPersonalInfo });
    setPersonalErrors({});
  };

  // Editable resume content
  const [editableContent, setEditableContent] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  // Curation settings
  const [curationSettings, setCurationSettings] = useState(null);
  const [chronologyCorrections, setChronologyCorrections] = useState({});

  useEffect(() => {
    loadProjects();
    loadStoredResumes();
    loadPersonalInfo();
    loadCurationSettings();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await projectsAPI.getProjects();

      // data should already be a list of projects
      const projectList = Array.isArray(data) ? data : [];
      setProjects(projectList);
      setError('');
    } catch (err) {
      console.error('Error loading projects:', err);
      setError(err.response?.data?.detail || 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  const loadCurationSettings = async () => {
    try {
      const [settings, curationProjects] = await Promise.all([
        curationAPI.getSettings(),
        curationAPI.getProjects(),
      ]);
      setCurationSettings(settings);

      // Build chronology corrections map from curation projects
      const corrections = {};
      if (Array.isArray(curationProjects)) {
        curationProjects.forEach((p) => {
          if (p.correction_timestamp) {
            corrections[p.id] = {
              last_commit_date: p.effective_last_commit_date,
              last_modified_date: p.effective_last_modified_date,
              project_start_date: p.effective_project_start_date,
              project_end_date: p.effective_project_end_date,
            };
          }
        });
      }
      setChronologyCorrections(corrections);

      // Pre-select showcase projects if no projects are selected yet
      if (settings?.showcase_project_ids?.length > 0) {
        setSelectedProjectIds((prev) => {
          if (prev.length === 0) {
            return settings.showcase_project_ids;
          }
          return prev;
        });
      }
    } catch (err) {
      console.error('Error loading curation settings:', err);
    }
  };

  const loadStoredResumes = async () => {
    try {
      setStoredResumeLoading(true);
      const data = await resumeAPI.listStoredResumes();
      setStoredResumes(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading stored resumes:', err);
    } finally {
      setStoredResumeLoading(false);
    }
  };

  const loadPersonalInfo = async () => {
    try {
      const data = await resumeAPI.getPersonalInfo();
      const saved = data?.personal_info || {};

      if (saved && typeof saved === 'object') {
        const loaded = { ...emptyPersonal, ...saved };
        setPersonalInfo(loaded);
        setOriginalPersonalInfo(loaded);
      }
    } catch (err) {
      console.error('Error loading personal info:', err);
    }
  };

  const handleCreateStoredResume = async () => {
    if (!storedResumeTitle.trim() || !storedResumeContent.trim()) {
      setError('Please add a resume title and content to save.');
      return;
    }

    try {
      setStoredResumeSaving(true);
      setError('');
      const created = await resumeAPI.createStoredResume({
        title: storedResumeTitle.trim(),
        format: storedResumeFormat,
        content: storedResumeContent,
      });
      setStoredResumes((prev) => [created, ...prev]);
      setStoredResumeId(created.id);
    } catch (err) {
      console.error('Error creating stored resume:', err);
      setError(err.response?.data?.detail || 'Failed to store resume');
    } finally {
      setStoredResumeSaving(false);
    }
  };

  const handleUpdateStoredResume = async () => {
    if (!storedResumeId) {
      setError('Select a stored resume to update.');
      return;
    }

    try {
      setStoredResumeSaving(true);
      setError('');
      const updated = await resumeAPI.updateStoredResume(storedResumeId, storedResumeContent);
      setStoredResumes((prev) => prev.map((r) => (r.id === updated.id ? updated : r)));
    } catch (err) {
      console.error('Error updating stored resume:', err);
      setError(err.response?.data?.detail || 'Failed to update resume');
    } finally {
      setStoredResumeSaving(false);
    }
  };

  const handleSelectStoredResume = async (resumeId) => {
    setStoredResumeId(resumeId);

    if (!resumeId) {
      setStoredResumeTitle('');
      setStoredResumeContent('');
      setStoredResumeFormat('markdown');
      return;
    }

    try {
      const resume = await resumeAPI.getStoredResume(resumeId);
      setStoredResumeTitle(resume.title);
      setStoredResumeContent(resume.content);
      setStoredResumeFormat(resume.format);
    } catch (err) {
      console.error('Error loading stored resume:', err);
      setError(err.response?.data?.detail || 'Failed to load stored resume');
    }
  };

  const toggleProject = (projectId) => {
    setSelectedProjectIds((prev) => {
      if (prev.includes(projectId)) {
        return prev.filter((id) => id !== projectId);
      }
      return [...prev, projectId];
    });
  };

  const selectAll = () => {
    if (selectedProjectIds.length === projects.length) {
      setSelectedProjectIds([]);
    } else {
      setSelectedProjectIds(projects.map((p) => p.id));
    }
  };

  const handleGenerateResume = async () => {
    if (selectedProjectIds.length === 0) {
      setError('Please select at least one project');
      try { window.scrollTo(0, 0); } catch (_) {}
      return;
    }

    const errs = validatePersonalInfo(personalInfo);
    if (Object.keys(errs).length > 0) {
      setPersonalErrors(errs);
      setError('Please fix the personal information errors before generating.');
      try { window.scrollTo(0, 0); } catch (_) {}
      return;
    }
    setPersonalErrors({});

    try {
      setGenerating(true);
      setError('');

      const resume = await resumeAPI.generateResume(selectedProjectIds, {
        format: resumeFormat,
        include_skills: includeSkills,
        include_projects: includeProjects,
        personal_info: personalInfo,
        stored_resume_id: resumeFormat === 'markdown' ? (storedResumeId || null) : null,
        highlighted_skills: curationSettings?.highlighted_skills?.length > 0
          ? curationSettings.highlighted_skills
          : undefined,
      });

      setGeneratedResume(resume);
      setEditableContent(resume.content);
      setIsEditing(false);
    } catch (err) {
      console.error('Error generating resume:', err);
      setError(err.response?.data?.detail || 'Failed to generate resume');
      try { window.scrollTo(0, 0); } catch (_) {}
    } finally {
      setGenerating(false);
    }
  };

  const handleEditContent = () => setIsEditing(true);

  const handleSaveEdit = () => {
    if (editableContent && generatedResume) {
      setGeneratedResume({
        ...generatedResume,
        content: editableContent,
      });
      setIsEditing(false);
    }
  };

  const handleCancelEdit = () => {
    setEditableContent(generatedResume?.content || '');
    setIsEditing(false);
  };

  const downloadResume = () => {
    if (!generatedResume) return;

    if (resumeFormat === 'pdf') {
      // Decode base64 PDF
      const binaryString = atob(generatedResume.content);
      const bytes = new Uint8Array(binaryString.length);
      for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
      }
      const blob = new Blob([bytes], { type: 'application/pdf' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `resume_${new Date().toISOString().split('T')[0]}.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } else if (resumeFormat === 'latex') {
      try {
        const binaryString = atob(generatedResume.content);
        const bytes = new Uint8Array(binaryString.length);
        for (let i = 0; i < binaryString.length; i++) {
          bytes[i] = binaryString.charCodeAt(i);
        }
        const pdfSignature = String.fromCharCode(bytes[0], bytes[1], bytes[2], bytes[3]);
        if (pdfSignature === '%PDF') {
          const blob = new Blob([bytes], { type: 'application/pdf' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = `resume_latex_${new Date().toISOString().split('T')[0]}.pdf`;
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        } else {
          throw new Error('Not a PDF');
        }
      } catch (e) {
        const blob = new Blob([generatedResume.content], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `resume_${new Date().toISOString().split('T')[0]}.tex`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } else {
      const blob = new Blob([generatedResume.content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `resume_${new Date().toISOString().split('T')[0]}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const copyToClipboard = () => {
    if (!generatedResume) return;
    const contentToCopy = isEditing ? editableContent : generatedResume.content;
    navigator.clipboard.writeText(contentToCopy);
    alert('Resume copied to clipboard!');
  };

  // backend may return different metadata keys now (project-based)
  const meta = generatedResume?.metadata || {};
  const selectedCount =
    meta.project_count ??
    meta.selected_projects ??
    meta.portfolio_count ??
    selectedProjectIds.length;

  const totalProjects =
    meta.total_projects ??
    meta.projects_total ??
    selectedProjectIds.length;

  return (
    <div
      style={{
        minHeight: '100vh',
        backgroundColor: '#fafafa',
        paddingTop: error ? '52px' : 0,
      }}
    >
      {/* Fixed error toast at top so Generate Resume errors are visible without scrolling */}
      {error && (
        <div
          role="alert"
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            zIndex: 9999,
            backgroundColor: '#dc2626',
            color: 'white',
            padding: '12px 16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
          }}
        >
          <span style={{ flex: 1 }}>{error}</span>
          <button
            type="button"
            onClick={() => setError('')}
            aria-label="Dismiss"
            style={{
              background: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              padding: '6px 12px',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '500',
            }}
          >
            Dismiss
          </button>
        </div>
      )}

      <Navigation />

      <div
        style={{
          maxWidth: '1400px',
          margin: '0 auto',
          padding: '48px 32px',
        }}
      >
        {/* Header */}
        <div
          style={{
            marginBottom: '32px',
          }}
        >
          <h1
            style={{
              fontSize: '36px',
              fontWeight: '600',
              color: '#1a1a1a',
              margin: '0 0 8px 0',
            }}
          >
            Resume Generator
          </h1>
          <p
            style={{
              fontSize: '16px',
              color: '#737373',
              margin: 0,
            }}
          >
            Customize your resume by selecting projects and personalizing information.
          </p>
        </div>

        {error && (
          <div
            style={{
              backgroundColor: '#fee',
              border: '1px solid #fcc',
              padding: '12px 16px',
              borderRadius: '8px',
              color: '#c33',
              marginBottom: '24px',
            }}
          >
            {error}
          </div>
        )}

        <div
          style={{
            display: 'grid',
            gridTemplateColumns: generatedResume ? '400px 1fr' : '1fr',
            gap: '24px',
          }}
        >
          {/* Left Panel */}
          <div>
            {/* Personal Information */}
            <div
              style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                marginBottom: '24px',
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2
                  style={{
                    fontSize: '20px',
                    fontWeight: '600',
                    color: '#1a1a1a',
                    margin: 0,
                  }}
                />
                <div style={{ marginTop: '8px', paddingTop: '12px', borderTop: '1px solid #e5e7eb' }}>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#525252', marginBottom: '8px' }}>Education Section</div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <input
                      type="text"
                      placeholder="University Name"
                      value={personalInfo.education_university}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, education_university: e.target.value })}
                      style={{ padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '14px', width: '100%', boxSizing: 'border-box' }}
                    />
                    <input
                      type="text"
                      placeholder="Location (e.g., City, State)"
                      value={personalInfo.education_location}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, education_location: e.target.value })}
                      style={{ padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '14px', width: '100%', boxSizing: 'border-box' }}
                    />
                    <input
                      type="text"
                      placeholder="Degree (e.g., B.S. Computer Science)"
                      value={personalInfo.education_degree}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, education_degree: e.target.value })}
                      style={{ padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '14px', width: '100%', boxSizing: 'border-box' }}
                    />
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <input
                        type="text"
                        placeholder="Start date (e.g., Aug 2020)"
                        value={personalInfo.education_start_date}
                        onChange={(e) => setPersonalInfo({ ...personalInfo, education_start_date: e.target.value })}
                        style={{ flex: 1, padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
                      />
                      <input
                        type="text"
                        placeholder="End date (e.g., May 2024)"
                        value={personalInfo.education_end_date}
                        onChange={(e) => setPersonalInfo({ ...personalInfo, education_end_date: e.target.value })}
                        style={{ flex: 1, padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '14px', boxSizing: 'border-box' }}
                      />
                    </div>
                    <input
                      type="text"
                      placeholder="Awards (e.g., Dean's List, Scholarship Name)"
                      value={personalInfo.education_awards}
                      onChange={(e) => setPersonalInfo({ ...personalInfo, education_awards: e.target.value })}
                      style={{ padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: '6px', fontSize: '14px', width: '100%', boxSizing: 'border-box' }}
                    />
                  </div>
                >
                  Personal Information
                </h2>
                {hasOriginalPersonalInfo && hasPersonalInfoChanges() && (
                  <button
                    type="button"
                    onClick={onCancelPersonalInfo}
                    style={{
                      padding: '6px 14px',
                      fontSize: '13px',
                      fontWeight: '500',
                      color: '#991b1b',
                      backgroundColor: 'white',
                      border: '1px solid #e5e7eb',
                      borderRadius: '6px',
                      cursor: 'pointer',
                    }}
                  >
                    Cancel Changes
                  </button>
                )}
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
                    Full Name
                  </div>
                  <input
                    type="text"
                    placeholder="Full Name"
                    value={personalInfo.name}
                    onChange={(e) => onChangePersonalField('name', e.target.value)}
                    style={{
                      padding: '10px 12px',
                      border: `1px solid ${personalErrors.name ? '#dc2626' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      fontSize: '14px',
                      width: '100%',
                      boxSizing: 'border-box',
                    }}
                  />
                  {personalErrors.name && (
                    <div style={{ color: '#dc2626', fontSize: '12px', marginTop: '4px' }}>
                      {personalErrors.name}
                    </div>
                  )}
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
                    Email
                  </div>
                  <input
                    type="email"
                    placeholder="Email Address"
                    value={personalInfo.email}
                    onChange={(e) => onChangePersonalField('email', e.target.value)}
                    style={{
                      padding: '10px 12px',
                      border: `1px solid ${personalErrors.email ? '#dc2626' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      fontSize: '14px',
                      width: '100%',
                      boxSizing: 'border-box',
                    }}
                  />
                  {personalErrors.email && (
                    <div style={{ color: '#dc2626', fontSize: '12px', marginTop: '4px' }}>
                      {personalErrors.email}
                    </div>
                  )}
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
                    Phone
                  </div>
                  <input
                    type="tel"
                    placeholder="Phone Number"
                    value={personalInfo.phone}
                    onChange={(e) => onChangePersonalField('phone', e.target.value)}
                    style={{
                      padding: '10px 12px',
                      border: `1px solid ${personalErrors.phone ? '#dc2626' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      fontSize: '14px',
                      width: '100%',
                      boxSizing: 'border-box',
                    }}
                  />
                  {personalErrors.phone && (
                    <div style={{ color: '#dc2626', fontSize: '12px', marginTop: '4px' }}>
                      {personalErrors.phone}
                    </div>
                  )}
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
                    Location
                  </div>
                  <input
                    type="text"
                    placeholder="Location (e.g., City, State)"
                    value={personalInfo.location}
                    onChange={(e) => onChangePersonalField('location', e.target.value)}
                    style={{
                      padding: '10px 12px',
                      border: `1px solid ${personalErrors.location ? '#dc2626' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      fontSize: '14px',
                      width: '100%',
                      boxSizing: 'border-box',
                    }}
                  />
                  {personalErrors.location && (
                    <div style={{ color: '#dc2626', fontSize: '12px', marginTop: '4px' }}>
                      {personalErrors.location}
                    </div>
                  )}
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
                    LinkedIn <span style={{ color: '#9ca3af', fontWeight: '400' }}>(optional)</span>
                  </div>
                  <input
                    type="url"
                    placeholder="LinkedIn URL"
                    value={personalInfo.linkedIn}
                    onChange={(e) => onChangePersonalField('linkedIn', e.target.value)}
                    style={{
                      padding: '10px 12px',
                      border: `1px solid ${personalErrors.linkedIn ? '#dc2626' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      fontSize: '14px',
                      width: '100%',
                      boxSizing: 'border-box',
                    }}
                  />
                  {personalErrors.linkedIn && (
                    <div style={{ color: '#dc2626', fontSize: '12px', marginTop: '4px' }}>
                      {personalErrors.linkedIn}
                    </div>
                  )}
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
                    GitHub <span style={{ color: '#9ca3af', fontWeight: '400' }}>(optional)</span>
                  </div>
                  <input
                    type="url"
                    placeholder="GitHub URL"
                    value={personalInfo.github}
                    onChange={(e) => onChangePersonalField('github', e.target.value)}
                    style={{
                      padding: '10px 12px',
                      border: `1px solid ${personalErrors.github ? '#dc2626' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      fontSize: '14px',
                      width: '100%',
                      boxSizing: 'border-box',
                    }}
                  />
                  {personalErrors.github && (
                    <div style={{ color: '#dc2626', fontSize: '12px', marginTop: '4px' }}>
                      {personalErrors.github}
                    </div>
                  )}
                </div>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: '600', color: '#374151', marginBottom: '4px' }}>
                    Website <span style={{ color: '#9ca3af', fontWeight: '400' }}>(optional)</span>
                  </div>
                  <input
                    type="url"
                    placeholder="Personal Website"
                    value={personalInfo.website}
                    onChange={(e) => onChangePersonalField('website', e.target.value)}
                    style={{
                      padding: '10px 12px',
                      border: `1px solid ${personalErrors.website ? '#dc2626' : '#e5e7eb'}`,
                      borderRadius: '6px',
                      fontSize: '14px',
                      width: '100%',
                      boxSizing: 'border-box',
                    }}
                  />
                  {personalErrors.website && (
                    <div style={{ color: '#dc2626', fontSize: '12px', marginTop: '4px' }}>
                      {personalErrors.website}
                    </div>
                  )}
                </div>
              </div>
            </div>
            {/* Stored Resume */}
            <div
              style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                marginBottom: '24px',
              }}
            >
              <h2
                style={{
                  fontSize: '20px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: 0,
                  marginBottom: '16px',
                }}
              >
                Stored Resume
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <input
                  type="text"
                  placeholder="Resume Title"
                  value={storedResumeTitle}
                  onChange={(e) => setStoredResumeTitle(e.target.value)}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                />

                <select
                  value={storedResumeFormat}
                  onChange={(e) => setStoredResumeFormat(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '8px 12px',
                    fontSize: '14px',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    backgroundColor: 'white',
                  }}
                >
                  <option value="markdown">Markdown</option>
                  <option value="text">Plain text</option>
                </select>

                <textarea
                  value={storedResumeContent}
                  onChange={(e) => setStoredResumeContent(e.target.value)}
                  placeholder="Paste your existing resume here..."
                  style={{
                    width: '100%',
                    minHeight: '180px',
                    padding: '12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '13px',
                    fontFamily: 'monospace',
                    lineHeight: '1.5',
                    resize: 'vertical',
                    boxSizing: 'border-box',
                  }}
                />

                <div style={{ display: 'flex', gap: '8px' }}>
                  <button
                    onClick={handleCreateStoredResume}
                    disabled={storedResumeSaving || storedResumeLoading}
                    style={{
                      flex: 1,
                      padding: '10px 12px',
                      fontSize: '14px',
                      color: 'white',
                      backgroundColor: '#2563eb',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                    }}
                  >
                    {storedResumeSaving ? 'Saving...' : 'Save New Resume'}
                  </button>
                  <button
                    onClick={handleUpdateStoredResume}
                    disabled={storedResumeSaving || !storedResumeId}
                    style={{
                      flex: 1,
                      padding: '10px 12px',
                      fontSize: '14px',
                      color: '#2563eb',
                      backgroundColor: 'white',
                      border: '1px solid #2563eb',
                      borderRadius: '6px',
                      cursor: storedResumeId ? 'pointer' : 'not-allowed',
                    }}
                  >
                    Update Resume
                  </button>
                </div>

                {storedResumeLoading && (
                  <div style={{ fontSize: '12px', color: '#737373' }}>
                    Loading stored resumes...
                  </div>
                )}
              </div>
            </div>

            {/* Project Selection */}
            <div
              style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '16px',
                }}
              >
                <h2
                  style={{
                    fontSize: '20px',
                    fontWeight: '600',
                    color: '#1a1a1a',
                    margin: 0,
                  }}
                >
                  Select Projects
                </h2>

                <button
                  onClick={selectAll}
                  style={{
                    padding: '6px 12px',
                    fontSize: '14px',
                    color: '#2563eb',
                    backgroundColor: 'transparent',
                    border: '1px solid #2563eb',
                    borderRadius: '6px',
                    cursor: 'pointer',
                  }}
                >
                  {selectedProjectIds.length === projects.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>

              {loading ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#737373' }}>
                  Loading projects...
                </div>
              ) : projects.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#737373' }}>
                  No projects found. Upload a project first.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(() => {
                    // Sort projects by curation order if available
                    const orderIds = curationSettings?.custom_project_order;
                    const showcaseIdsList = curationSettings?.showcase_project_ids ?? [];
                    const showcaseRanks = new Map();
                    showcaseIdsList.forEach((id, i) => showcaseRanks.set(id, i + 1));
                    let sortedProjects = [...projects];
                    if (Array.isArray(orderIds) && orderIds.length > 0) {
                      sortedProjects.sort((a, b) => {
                        const aIdx = orderIds.indexOf(a.id);
                        const bIdx = orderIds.indexOf(b.id);
                        if (aIdx === -1 && bIdx === -1) return 0;
                        if (aIdx === -1) return 1;
                        if (bIdx === -1) return -1;
                        return aIdx - bIdx;
                      });
                    }
                    return sortedProjects.map((project) => {
                      const showcaseRank = showcaseRanks.get(project.id);
                      const isShowcase = !!showcaseRank;
                      const correction = chronologyCorrections[project.id];
                      return (
                        <label
                          key={project.id}
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            padding: '12px',
                            backgroundColor: selectedProjectIds.includes(project.id)
                              ? isShowcase ? '#fefce8' : '#eff6ff'
                              : isShowcase ? '#fffbeb' : '#f9fafb',
                            border: `2px solid ${
                              selectedProjectIds.includes(project.id)
                                ? isShowcase ? '#f59e0b' : '#2563eb'
                                : isShowcase ? '#fcd34d' : '#e5e7eb'
                            }`,
                            borderRadius: '8px',
                            cursor: 'pointer',
                            transition: 'all 0.2s',
                          }}
                        >
                          <input
                            type="checkbox"
                            checked={selectedProjectIds.includes(project.id)}
                            onChange={() => toggleProject(project.id)}
                            style={{
                              width: '18px',
                              height: '18px',
                              marginRight: '12px',
                              cursor: 'pointer',
                            }}
                          />
                          <div style={{ flex: 1 }}>
                            <div
                              style={{
                                fontSize: '14px',
                                fontWeight: '600',
                                color: '#1a1a1a',
                                marginBottom: '4px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                              }}
                            >
                              {project.project_name || 'Unnamed Project'}
                              {isShowcase && (
                                <span style={{
                                  padding: '1px 6px',
                                  borderRadius: '999px',
                                  backgroundColor: '#fef3c7',
                                  color: '#b45309',
                                  fontSize: '10px',
                                  fontWeight: '700',
                                }}>⭐ Top {showcaseRank}</span>
                              )}
                            </div>

                        <div style={{ fontSize: '12px', color: '#737373' }}>
                          Project ID: <span style={{ fontFamily: 'monospace' }}>{project.id}</span>
                          {project.primary_language ? ` • ${project.primary_language}` : ''}
                          {typeof project.total_files === 'number' ? ` • ${project.total_files} files` : ''}
                          {correction && correction.project_start_date ? (
                            <span style={{ color: '#16a34a' }}>
                              {' '}• {correction.project_start_date}
                              {correction.project_end_date ? ` – ${correction.project_end_date}` : ''}
                              {' '}(corrected)
                            </span>
                          ) : null}
                        </div>
                      </div>
                    </label>
                  );
                    });
                  })()}
                </div>
              )}

              {/* Options */}
              <div
                style={{
                  marginTop: '24px',
                  paddingTop: '24px',
                  borderTop: '1px solid #e5e7eb',
                }}
              >
                <h3
                  style={{
                    fontSize: '16px',
                    fontWeight: '600',
                    color: '#1a1a1a',
                    marginBottom: '12px',
                  }}
                >
                  Options
                </h3>

                <div style={{ marginBottom: '12px' }}>
                  <label
                    style={{
                      fontSize: '14px',
                      color: '#525252',
                      marginBottom: '4px',
                      display: 'block',
                    }}
                  >
                    Format
                  </label>

                  <select
                    value={resumeFormat}
                    onChange={(e) => setResumeFormat(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '8px 12px',
                      fontSize: '14px',
                      border: '1px solid #d1d5db',
                      borderRadius: '6px',
                      backgroundColor: 'white',
                    }}
                  >
                    <option value="markdown">Markdown</option>
                    <option value="pdf">PDF</option>
                  </select>
                </div>

                <div>
                  {/* Stored Resume Selector */}
                  <div style={{ marginBottom: '12px' }}>
                    <label
                      style={{
                        fontSize: '14px',
                        color: '#525252',
                        marginBottom: '4px',
                        display: 'block',
                      }}
                    >
                      Use Stored Resume (Markdown only)
                    </label>
                    <select
                      value={storedResumeId || ''}
                      onChange={(e) => handleSelectStoredResume(Number(e.target.value) || '')}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        fontSize: '14px',
                        border: '1px solid #d1d5db',
                        borderRadius: '6px',
                        backgroundColor: 'white',
                      }}
                    >
                      <option value="">None</option>
                      {storedResumes.map((resume) => (
                        <option key={resume.id} value={resume.id}>
                          {resume.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  {/* Include Projects Section */}
                  <label
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      fontSize: '14px',
                      color: '#525252',
                      cursor: 'pointer',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={includeProjects}
                      onChange={(e) => setIncludeProjects(e.target.checked)}
                      style={{ marginRight: '8px' }}
                    />
                    Include Projects Section
                  </label>
                </div>

                {/* Generate Button */}
                <button
                  onClick={handleGenerateResume}
                  disabled={generating || selectedProjectIds.length === 0}
                  style={{
                    width: '100%',
                    marginTop: '24px',
                    padding: '12px',
                    fontSize: '16px',
                    fontWeight: '500',
                    color: 'white',
                    backgroundColor:
                      generating || selectedProjectIds.length === 0 ? '#9ca3af' : '#2563eb',
                    border: 'none',
                    borderRadius: '8px',
                    cursor: generating || selectedProjectIds.length === 0 ? 'not-allowed' : 'pointer',
                    transition: 'background-color 0.2s',
                  }}
                >
                  {generating ? 'Generating...' : 'Generate Resume'}
                </button>
              </div>
            </div>
          </div>

          {/* Right Panel - Generated Resume Preview */}
          {generatedResume && (
            <div
              style={{
                backgroundColor: 'white',
                borderRadius: '12px',
                padding: '24px',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              }}
            >
              <div
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  marginBottom: '16px',
                }}
              >
                <h2
                  style={{
                    fontSize: '20px',
                    fontWeight: '600',
                    color: '#1a1a1a',
                    margin: 0,
                  }}
                >
                  Generated Resume
                </h2>

                <div style={{ display: 'flex', gap: '8px' }}>
                  {resumeFormat !== 'pdf' && !isEditing && (
                    <>
                      <button
                        onClick={handleEditContent}
                        style={{
                          padding: '8px 16px',
                          fontSize: '14px',
                          color: '#2563eb',
                          backgroundColor: 'white',
                          border: '1px solid #2563eb',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                      >
                        Edit
                      </button>

                      <button
                        onClick={copyToClipboard}
                        style={{
                          padding: '8px 16px',
                          fontSize: '14px',
                          color: '#2563eb',
                          backgroundColor: 'white',
                          border: '1px solid #2563eb',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                      >
                        Copy
                      </button>
                    </>
                  )}

                  {isEditing && (
                    <>
                      <button
                        onClick={handleSaveEdit}
                        style={{
                          padding: '8px 16px',
                          fontSize: '14px',
                          color: 'white',
                          backgroundColor: '#16a34a',
                          border: 'none',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                      >
                        Save
                      </button>

                      <button
                        onClick={handleCancelEdit}
                        style={{
                          padding: '8px 16px',
                          fontSize: '14px',
                          color: '#737373',
                          backgroundColor: 'white',
                          border: '1px solid #d1d5db',
                          borderRadius: '6px',
                          cursor: 'pointer',
                        }}
                      >
                        Cancel
                      </button>
                    </>
                  )}

                  <button
                    onClick={downloadResume}
                    style={{
                      padding: '8px 16px',
                      fontSize: '14px',
                      color: 'white',
                      backgroundColor: '#2563eb',
                      border: 'none',
                      borderRadius: '6px',
                      cursor: 'pointer',
                    }}
                  >
                    Download
                  </button>
                </div>
              </div>

              {/* Metadata */}
              <div
                style={{
                  padding: '12px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  marginBottom: '16px',
                  fontSize: '14px',
                  color: '#525252',
                }}
              >
                <div>
                  Format: <strong>{generatedResume.format}</strong>
                </div>
                <div>
                  Selected Projects: <strong>{selectedCount}</strong>
                </div>
                <div>
                  Total Projects: <strong>{totalProjects}</strong>
                </div>
                <div>
                  Generated:{' '}
                  <strong>
                    {meta.generated_at ? new Date(meta.generated_at).toLocaleString() : 'N/A'}
                  </strong>
                </div>
              </div>

              {/* Resume Content */}
              <div
                style={{
                  padding: '24px',
                  backgroundColor: '#fafafa',
                  borderRadius: '8px',
                  maxHeight: '600px',
                  overflowY: 'auto',
                }}
              >
                {resumeFormat === 'pdf' ? (
                  <div
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      justifyContent: 'center',
                      padding: '48px',
                      textAlign: 'center',
                    }}
                  >
                    <svg
                      style={{ marginBottom: '16px' }}
                      width="64"
                      height="64"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="#2563eb"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                      <polyline points="14 2 14 8 20 8"></polyline>
                      <line x1="16" y1="13" x2="8" y2="13"></line>
                      <line x1="16" y1="17" x2="8" y2="17"></line>
                      <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>

                    <h3
                      style={{
                        fontSize: '18px',
                        fontWeight: '600',
                        color: '#1a1a1a',
                        marginBottom: '8px',
                      }}
                    >
                      PDF Resume Generated Successfully
                    </h3>

                    <p style={{ color: '#737373', marginBottom: '16px' }}>
                      Your resume has been generated as a professional PDF file. Click the Download button above to save it.
                    </p>
                  </div>
                ) : isEditing ? (
                  <textarea
                    value={editableContent}
                    onChange={(e) => setEditableContent(e.target.value)}
                    style={{
                      width: '100%',
                      minHeight: '500px',
                      padding: '16px',
                      border: '2px solid #2563eb',
                      borderRadius: '8px',
                      fontFamily: 'monospace',
                      fontSize: '14px',
                      lineHeight: '1.6',
                      resize: 'vertical',
                      boxSizing: 'border-box',
                    }}
                  />
                ) : (
                  <div
                    style={{
                      fontFamily:
                        '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
                      fontSize: '15px',
                      lineHeight: '1.7',
                      color: '#1a1a1a',
                    }}
                  >
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ node, ...props }) => (
                          <h1
                            style={{
                              fontSize: '32px',
                              fontWeight: '700',
                              marginTop: '24px',
                              marginBottom: '16px',
                              borderBottom: '2px solid #e5e7eb',
                              paddingBottom: '8px',
                            }}
                            {...props}
                          />
                        ),
                        h2: ({ node, ...props }) => (
                          <h2
                            style={{
                              fontSize: '24px',
                              fontWeight: '600',
                              marginTop: '20px',
                              marginBottom: '12px',
                              color: '#2563eb',
                            }}
                            {...props}
                          />
                        ),
                        h3: ({ node, ...props }) => (
                          <h3
                            style={{
                              fontSize: '20px',
                              fontWeight: '600',
                              marginTop: '16px',
                              marginBottom: '8px',
                            }}
                            {...props}
                          />
                        ),
                        h4: ({ node, ...props }) => (
                          <h4
                            style={{
                              fontSize: '18px',
                              fontWeight: '600',
                              marginTop: '12px',
                              marginBottom: '8px',
                            }}
                            {...props}
                          />
                        ),
                        p: ({ node, ...props }) => <p style={{ marginBottom: '12px' }} {...props} />,
                        ul: ({ node, ...props }) => (
                          <ul style={{ marginLeft: '20px', marginBottom: '12px', listStyleType: 'disc' }} {...props} />
                        ),
                        ol: ({ node, ...props }) => (
                          <ol style={{ marginLeft: '20px', marginBottom: '12px', listStyleType: 'decimal' }} {...props} />
                        ),
                        li: ({ node, ...props }) => <li style={{ marginBottom: '6px' }} {...props} />,
                        strong: ({ node, ...props }) => (
                          <strong style={{ fontWeight: '600', color: '#1a1a1a' }} {...props} />
                        ),
                        em: ({ node, ...props }) => <em style={{ fontStyle: 'italic' }} {...props} />,
                        code: ({ node, inline, ...props }) =>
                          inline ? (
                            <code
                              style={{
                                backgroundColor: '#f3f4f6',
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontFamily: 'monospace',
                                fontSize: '14px',
                                color: '#dc2626',
                              }}
                              {...props}
                            />
                          ) : (
                            <code
                              style={{
                                display: 'block',
                                backgroundColor: '#f3f4f6',
                                padding: '12px',
                                borderRadius: '6px',
                                fontFamily: 'monospace',
                                fontSize: '14px',
                                overflowX: 'auto',
                                marginBottom: '12px',
                              }}
                              {...props}
                            />
                          ),
                        blockquote: ({ node, ...props }) => (
                          <blockquote
                            style={{
                              borderLeft: '4px solid #2563eb',
                              paddingLeft: '16px',
                              color: '#525252',
                              fontStyle: 'italic',
                              marginLeft: '0',
                              marginBottom: '12px',
                            }}
                            {...props}
                          />
                        ),
                        a: ({ node, ...props }) => <a style={{ color: '#2563eb', textDecoration: 'underline' }} {...props} />,
                        hr: ({ node, ...props }) => (
                          <hr style={{ border: 'none', borderTop: '1px solid #e5e7eb', margin: '24px 0' }} {...props} />
                        ),
                      }}
                    >
                      {generatedResume.content}
                    </ReactMarkdown>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Resume;