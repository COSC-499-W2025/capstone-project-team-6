import { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import { projectsAPI, resumeAPI } from '../services/api';
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
  const [personalInfo, setPersonalInfo] = useState({
    name: '',
    email: '',
    phone: '',
    location: '',
    linkedIn: '',
    github: '',
    website: '',
  });

  // Editable resume content
  const [editableContent, setEditableContent] = useState(null);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    loadProjects();
    loadStoredResumes();
    loadPersonalInfo();
  }, []);

  const loadProjects = async () => {
    try {
      setLoading(true);
      const data = await projectsAPI.getProjects();

      // data should already be a list of projects
      setProjects(Array.isArray(data) ? data : []);
      setError('');
    } catch (err) {
      console.error('Error loading projects:', err);
      setError(err.response?.data?.detail || 'Failed to load projects');
    } finally {
      setLoading(false);
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
        setPersonalInfo((prev) => ({
          ...prev,
          ...saved,
        }));
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
      return;
    }

    try {
      setGenerating(true);
      setError('');

      const resume = await resumeAPI.generateResume(selectedProjectIds, {
        format: resumeFormat,
        include_skills: includeSkills,
        include_projects: includeProjects,
        personal_info: personalInfo,
        stored_resume_id: resumeFormat === 'markdown' ? (storedResumeId || null) : null,
      });

      setGeneratedResume(resume);
      setEditableContent(resume.content);
      setIsEditing(false);
    } catch (err) {
      console.error('Error generating resume:', err);
      setError(err.response?.data?.detail || 'Failed to generate resume');
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
      }}
    >
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
              <h2
                style={{
                  fontSize: '20px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: 0,
                  marginBottom: '16px',
                }}
              >
                Personal Information
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <input
                  type="text"
                  placeholder="Full Name"
                  value={personalInfo.name}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, name: e.target.value })}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                />
                <input
                  type="email"
                  placeholder="Email Address"
                  value={personalInfo.email}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, email: e.target.value })}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                />
                <input
                  type="tel"
                  placeholder="Phone Number"
                  value={personalInfo.phone}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, phone: e.target.value })}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                />
                <input
                  type="text"
                  placeholder="Location (e.g., City, State)"
                  value={personalInfo.location}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, location: e.target.value })}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                />
                <input
                  type="url"
                  placeholder="LinkedIn URL (optional)"
                  value={personalInfo.linkedIn}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, linkedIn: e.target.value })}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                />
                <input
                  type="url"
                  placeholder="GitHub URL (optional)"
                  value={personalInfo.github}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, github: e.target.value })}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                />
                <input
                  type="url"
                  placeholder="Personal Website (optional)"
                  value={personalInfo.website}
                  onChange={(e) => setPersonalInfo({ ...personalInfo, website: e.target.value })}
                  style={{
                    padding: '10px 12px',
                    border: '1px solid #e5e7eb',
                    borderRadius: '6px',
                    fontSize: '14px',
                    width: '100%',
                    boxSizing: 'border-box',
                  }}
                />
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
                  {projects.map((project) => (
                    <label
                      key={project.id}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '12px',
                        backgroundColor: selectedProjectIds.includes(project.id) ? '#eff6ff' : '#f9fafb',
                        border: `2px solid ${
                          selectedProjectIds.includes(project.id) ? '#2563eb' : '#e5e7eb'
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
                          }}
                        >
                          {project.project_name || 'Unnamed Project'}
                        </div>

                        <div style={{ fontSize: '12px', color: '#737373' }}>
                          Project ID: <span style={{ fontFamily: 'monospace' }}>{project.id}</span>
                          {project.primary_language ? ` • ${project.primary_language}` : ''}
                          {typeof project.total_files === 'number' ? ` • ${project.total_files} files` : ''}
                        </div>
                      </div>
                    </label>
                  ))}
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
                    <option value="latex">PDF</option>
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
                {resumeFormat === 'pdf' || resumeFormat === 'latex' ? (
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
                      stroke={resumeFormat === 'latex' ? '#16a34a' : '#2563eb'}
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
                      {resumeFormat === 'latex'
                        ? generatedResume.content.startsWith('%')
                          ? 'LaTeX Source Generated'
                          : 'LaTeX Resume Compiled Successfully'
                        : 'PDF Resume Generated Successfully'}
                    </h3>

                    <p style={{ color: '#737373', marginBottom: '16px' }}>
                      {resumeFormat === 'latex' && generatedResume.content.startsWith('%')
                        ? 'LaTeX compilation requires pdflatex. Download the .tex file to compile locally or upload to Overleaf.'
                        : 'Your resume has been generated as a professional PDF file. Click the Download button above to save it.'}
                    </p>

                    <div
                      style={{
                        padding: '12px 16px',
                        backgroundColor:
                          resumeFormat === 'latex' && generatedResume.content.startsWith('%')
                            ? '#fef3c7'
                            : resumeFormat === 'latex'
                            ? '#f0fdf4'
                            : '#eff6ff',
                        borderRadius: '6px',
                        border: `1px solid ${
                          resumeFormat === 'latex' && generatedResume.content.startsWith('%')
                            ? '#fcd34d'
                            : resumeFormat === 'latex'
                            ? '#86efac'
                            : '#bfdbfe'
                        }`,
                        color:
                          resumeFormat === 'latex' && generatedResume.content.startsWith('%')
                            ? '#92400e'
                            : resumeFormat === 'latex'
                            ? '#166534'
                            : '#1e40af',
                        fontSize: '13px',
                      }}
                    >
                      {resumeFormat === 'latex' ? (
                        generatedResume.content.startsWith('%') ? (
                          <span>
                            LaTeX compilation failed. Install pdflatex:{' '}
                            <code>brew install --cask mactex-no-gui</code> or upload the .tex file to Overleaf.com
                          </span>
                        ) : (
                          <span>Resume compiled successfully. Download the PDF by clicking the button above.</span>
                        )
                      ) : (
                        <span />
                      )}
                    </div>
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