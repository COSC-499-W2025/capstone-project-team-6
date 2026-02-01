import { useState, useEffect } from 'react';
import Navigation from '../components/Navigation';
import { portfolioAPI, resumeAPI } from '../services/api';

const Resume = () => {
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolios, setSelectedPortfolios] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState('');
  const [generatedResume, setGeneratedResume] = useState(null);
  const [resumeFormat, setResumeFormat] = useState('markdown');
  const [includeSkills, setIncludeSkills] = useState(true);
  const [includeProjects, setIncludeProjects] = useState(true);

  useEffect(() => {
    loadPortfolios();
  }, []);

  const loadPortfolios = async () => {
    try {
      setLoading(true);
      const data = await portfolioAPI.getPortfolios();
      setPortfolios(data);
      setError('');
    } catch (err) {
      console.error('Error loading portfolios:', err);
      setError(err.response?.data?.detail || 'Failed to load portfolios');
    } finally {
      setLoading(false);
    }
  };

  const togglePortfolio = (portfolioId) => {
    setSelectedPortfolios(prev => {
      if (prev.includes(portfolioId)) {
        return prev.filter(id => id !== portfolioId);
      } else {
        return [...prev, portfolioId];
      }
    });
  };

  const selectAll = () => {
    if (selectedPortfolios.length === portfolios.length) {
      setSelectedPortfolios([]);
    } else {
      setSelectedPortfolios(portfolios.map(p => p.analysis_uuid));
    }
  };

  const handleGenerateResume = async () => {
    if (selectedPortfolios.length === 0) {
      setError('Please select at least one portfolio');
      return;
    }

    try {
      setGenerating(true);
      setError('');
      const resume = await resumeAPI.generateResume(selectedPortfolios, {
        portfolio_ids: selectedPortfolios,
        format: resumeFormat,
        include_skills: includeSkills,
        include_projects: includeProjects,
      });
      setGeneratedResume(resume);
    } catch (err) {
      console.error('Error generating resume:', err);
      setError(err.response?.data?.detail || 'Failed to generate resume');
    } finally {
      setGenerating(false);
    }
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
    } else {
      // Markdown download
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
    navigator.clipboard.writeText(generatedResume.content);
    alert('Resume copied to clipboard!');
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#fafafa',
    }}>
      <Navigation />

      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        padding: '48px 32px',
      }}>
        {/* Header */}
        <div style={{
          marginBottom: '32px',
        }}>
          <h1 style={{
            fontSize: '36px',
            fontWeight: '600',
            color: '#1a1a1a',
            margin: '0 0 8px 0',
          }}>
            Resume Generator
          </h1>
          <p style={{
            fontSize: '16px',
            color: '#737373',
            margin: 0,
          }}>
            Select portfolios to generate a professional resume from your analyzed projects
          </p>
        </div>

        {error && (
          <div style={{
            backgroundColor: '#fee',
            border: '1px solid #fcc',
            padding: '12px 16px',
            borderRadius: '8px',
            color: '#c33',
            marginBottom: '24px',
          }}>
            {error}
          </div>
        )}

        <div style={{
          display: 'grid',
          gridTemplateColumns: generatedResume ? '400px 1fr' : '1fr',
          gap: '24px',
        }}>
          {/* Left Panel - Portfolio Selection */}
          <div>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '24px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '16px',
              }}>
                <h2 style={{
                  fontSize: '20px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: 0,
                }}>
                  Select Portfolios
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
                  {selectedPortfolios.length === portfolios.length ? 'Deselect All' : 'Select All'}
                </button>
              </div>

              {loading ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#737373' }}>
                  Loading portfolios...
                </div>
              ) : portfolios.length === 0 ? (
                <div style={{ textAlign: 'center', padding: '20px', color: '#737373' }}>
                  No portfolios found. Upload a project first.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {portfolios.map((portfolio) => (
                    <label
                      key={portfolio.analysis_uuid}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        padding: '12px',
                        backgroundColor: selectedPortfolios.includes(portfolio.analysis_uuid) ? '#eff6ff' : '#f9fafb',
                        border: `2px solid ${selectedPortfolios.includes(portfolio.analysis_uuid) ? '#2563eb' : '#e5e7eb'}`,
                        borderRadius: '8px',
                        cursor: 'pointer',
                        transition: 'all 0.2s',
                      }}
                    >
                      <input
                        type="checkbox"
                        checked={selectedPortfolios.includes(portfolio.analysis_uuid)}
                        onChange={() => togglePortfolio(portfolio.analysis_uuid)}
                        style={{
                          width: '18px',
                          height: '18px',
                          marginRight: '12px',
                          cursor: 'pointer',
                        }}
                      />
                      <div style={{ flex: 1 }}>
                        <div style={{
                          fontSize: '14px',
                          fontWeight: '500',
                          color: '#1a1a1a',
                          marginBottom: '4px',
                        }}>
                          {portfolio.zip_file}
                        </div>
                        <div style={{
                          fontSize: '12px',
                          color: '#737373',
                        }}>
                          {portfolio.total_projects} project{portfolio.total_projects !== 1 ? 's' : ''} • {new Date(portfolio.analysis_timestamp).toLocaleDateString()}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              )}

              {/* Options */}
              <div style={{
                marginTop: '24px',
                paddingTop: '24px',
                borderTop: '1px solid #e5e7eb',
              }}>
                <h3 style={{
                  fontSize: '16px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  marginBottom: '12px',
                }}>
                  Options
                </h3>
                
                <div style={{ marginBottom: '12px' }}>
                  <label style={{
                    fontSize: '14px',
                    color: '#525252',
                    marginBottom: '4px',
                    display: 'block',
                  }}>
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

                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#525252',
                  marginBottom: '8px',
                  cursor: 'pointer',
                }}>
                  <input
                    type="checkbox"
                    checked={includeSkills}
                    onChange={(e) => setIncludeSkills(e.target.checked)}
                    style={{ marginRight: '8px' }}
                  />
                  Include Skills Section
                </label>

                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  fontSize: '14px',
                  color: '#525252',
                  cursor: 'pointer',
                }}>
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
                disabled={generating || selectedPortfolios.length === 0}
                style={{
                  width: '100%',
                  marginTop: '24px',
                  padding: '12px',
                  fontSize: '16px',
                  fontWeight: '500',
                  color: 'white',
                  backgroundColor: generating || selectedPortfolios.length === 0 ? '#9ca3af' : '#2563eb',
                  border: 'none',
                  borderRadius: '8px',
                  cursor: generating || selectedPortfolios.length === 0 ? 'not-allowed' : 'pointer',
                  transition: 'background-color 0.2s',
                }}
              >
                {generating ? 'Generating...' : 'Generate Resume'}
              </button>
            </div>
          </div>

          {/* Right Panel - Generated Resume Preview */}
          {generatedResume && (
            <div style={{
              backgroundColor: 'white',
              borderRadius: '12px',
              padding: '24px',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            }}>
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginBottom: '16px',
              }}>
                <h2 style={{
                  fontSize: '20px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: 0,
                }}>
                  Generated Resume
                </h2>
                <div style={{ display: 'flex', gap: '8px' }}>
                  {resumeFormat !== 'pdf' && (
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
              <div style={{
                padding: '12px',
                backgroundColor: '#f9fafb',
                borderRadius: '8px',
                marginBottom: '16px',
                fontSize: '14px',
                color: '#525252',
              }}>
                <div>Format: <strong>{generatedResume.format}</strong></div>
                <div>Portfolios: <strong>{generatedResume.metadata.portfolio_count}</strong></div>
                <div>Total Projects: <strong>{generatedResume.metadata.total_projects}</strong></div>
                <div>Generated: <strong>{new Date(generatedResume.metadata.generated_at).toLocaleString()}</strong></div>
              </div>

              {/* Resume Content */}
              <div style={{
                padding: '24px',
                backgroundColor: '#fafafa',
                borderRadius: '8px',
                maxHeight: '600px',
                overflowY: 'auto',
                fontFamily: resumeFormat === 'pdf' ? 'inherit' : 'monospace',
                fontSize: '14px',
                lineHeight: '1.6',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}>
                {resumeFormat === 'pdf' ? (
                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '48px',
                    textAlign: 'center',
                  }}>
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
                    <h3 style={{ fontSize: '18px', fontWeight: '600', color: '#1a1a1a', marginBottom: '8px' }}>
                      PDF Resume Generated Successfully
                    </h3>
                    <p style={{ color: '#737373', marginBottom: '16px' }}>
                      Your resume has been generated as a PDF file. Click the Download button above to save it.
                    </p>
                    <div style={{ 
                      padding: '12px 16px', 
                      backgroundColor: '#eff6ff', 
                      borderRadius: '6px',
                      border: '1px solid #bfdbfe',
                      color: '#1e40af',
                      fontSize: '13px'
                    }}>
                      💡 PDF files cannot be previewed in the browser. Use the Download button to view the full resume.
                    </div>
                  </div>
                ) : (
                  generatedResume.content
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
