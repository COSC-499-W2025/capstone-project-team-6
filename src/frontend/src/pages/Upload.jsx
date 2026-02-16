import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import api from '../services/api';
import { portfoliosAPI } from '../services/api';

// Max file size: 500MB
const MAX_FILE_SIZE_MB = 500;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

const Upload = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const dragCounter = useRef(0);

  // Tab state
  const [activeTab, setActiveTab] = useState('single');

  // Form state for single project
  const [projectName, setProjectName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);

  // Form state for multiple projects
  const [multipleFiles, setMultipleFiles] = useState([]);

  // Form state for incremental upload
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState('');
  const [incrementalFile, setIncrementalFile] = useState(null);
  const [loadingPortfolios, setLoadingPortfolios] = useState(false);

  // UI state
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  const [incrementalResults, setIncrementalResults] = useState(null);

  // Load portfolios when incremental tab is selected
  useEffect(() => {
    if (activeTab === 'incremental') {
      loadPortfolios();
    }
  }, [activeTab]);

  // Load existing portfolios
  const loadPortfolios = async () => {
    setLoadingPortfolios(true);
    try {
      const data = await portfoliosAPI.listPortfolios();
      // API returns array directly, not wrapped in object
      setPortfolios(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Error loading portfolios:', err);
      setError('Failed to load portfolios');
    } finally {
      setLoadingPortfolios(false);
    }
  };

  // Clear form state when switching tabs
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSelectedFile(null);
    setMultipleFiles([]);
    setIncrementalFile(null);
    setSelectedPortfolio('');
    setProjectName('');
    setDescription('');
    setError('');
    setUploadProgress({ current: 0, total: 0 });
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Validate file size
  const validateFileSize = (file) => {
    if (file.size > MAX_FILE_SIZE_BYTES) {
      return `File "${file.name}" exceeds the ${MAX_FILE_SIZE_MB}MB size limit`;
    }
    return null;
  };

  // Fix drag leave flicker using counter
  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current++;
    if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
      setIsDragging(true);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    dragCounter.current--;
    if (dragCounter.current === 0) {
      setIsDragging(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
    dragCounter.current = 0;

    const files = Array.from(e.dataTransfer.files);
    processFiles(files);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    processFiles(files);
    // Reset input so the same file can be selected again
    e.target.value = '';
  };

  const processFiles = (files) => {
    const zipFiles = files.filter(file => file.name.endsWith('.zip'));

    if (zipFiles.length === 0) {
      setError('Please upload a ZIP file');
      return;
    }

    // Validate file sizes
    const sizeErrors = [];
    const validFiles = [];
    for (const file of zipFiles) {
      const sizeError = validateFileSize(file);
      if (sizeError) {
        sizeErrors.push(sizeError);
      } else {
        validFiles.push(file);
      }
    }

    if (sizeErrors.length > 0) {
      setError(sizeErrors.join('\n'));
      if (validFiles.length === 0) return;
    } else {
      setError('');
    }

    if (activeTab === 'single') {
      setSelectedFile(validFiles[0]);
    } else if (activeTab === 'multiple') {
      setMultipleFiles(prev => [...prev, ...validFiles]);
    } else if (activeTab === 'incremental') {
      setIncrementalFile(validFiles[0]);
    }
  };

  const handleRemoveFile = (index) => {
    if (activeTab === 'single') {
      setSelectedFile(null);
    } else if (activeTab === 'multiple') {
      setMultipleFiles(prev => prev.filter((_, i) => i !== index));
    } else if (activeTab === 'incremental') {
      setIncrementalFile(null);
    }
    setError('');
  };

  const handleSubmit = async () => {
    if (activeTab === 'single' && !selectedFile) {
      setError('Please select a ZIP file to upload');
      return;
    }

    if (activeTab === 'multiple' && multipleFiles.length === 0) {
      setError('Please select at least one ZIP file to upload');
      return;
    }

    if (activeTab === 'incremental') {
      if (!selectedPortfolio) {
        setError('Please select a portfolio to add to');
        return;
      }
      if (!incrementalFile) {
        setError('Please select a ZIP file to upload');
        return;
      }
    }

    setIsUploading(true);
    setError('');

    try {
      if (activeTab === 'single') {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('analysis_type', 'non_llm');
        // Note: project_name and description are stored locally but not sent
        // to the API as the backend doesn't currently support these fields

        await api.post('/portfolios/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
      } else if (activeTab === 'multiple') {
        // Upload multiple files with progress tracking and error aggregation
        const errors = [];
        const total = multipleFiles.length;
        setUploadProgress({ current: 0, total });

        for (let i = 0; i < multipleFiles.length; i++) {
          const file = multipleFiles[i];
          setUploadProgress({ current: i + 1, total });

          try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('analysis_type', 'non_llm');

            await api.post('/portfolios/upload', formData, {
              headers: {
                'Content-Type': 'multipart/form-data',
              },
            });
          } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Upload failed';
            errors.push(`${file.name}: ${errorMsg}`);
          }
        }

        // If some uploads failed, show aggregated errors
        if (errors.length > 0) {
          const successCount = total - errors.length;
          if (successCount > 0) {
            setError(`${successCount}/${total} files uploaded successfully.\nFailed:\n${errors.join('\n')}`);
          } else {
            setError(`All uploads failed:\n${errors.join('\n')}`);
          }
          setIsUploading(false);
          setUploadProgress({ current: 0, total: 0 });
          return;
        }
      } else if (activeTab === 'incremental') {
        // Upload to existing portfolio
        const response = await portfoliosAPI.addToPortfolio(selectedPortfolio, incrementalFile);
        
        // Poll for task completion and show results
        if (response && response.details) {
          const taskId = response.details.task_id;
          let taskComplete = false;
          let taskResult = null;
          
          // Poll every 2 seconds for up to 5 minutes
          const maxAttempts = 150;
          let attempts = 0;
          
          while (!taskComplete && attempts < maxAttempts) {
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            try {
              const statusResponse = await api.get(`/tasks/${taskId}/status`);
              const task = statusResponse.data;
              
              if (task.status === 'completed') {
                taskComplete = true;
                taskResult = task.result;
              } else if (task.status === 'failed') {
                throw new Error(task.error || 'Task failed');
              }
            } catch (err) {
              console.error('Error polling task:', err);
              break;
            }
            
            attempts++;
          }
          
          // Close uploading state before showing modal
          setIsUploading(false);
          setUploadProgress({ current: 0, total: 0 });
          
          // Show results
          if (taskResult && taskResult.update_details) {
            setIncrementalResults({
              message: response.message,
              taskId: taskId,
              portfolioId: response.details.portfolio_id,
              completed: true,
              details: {
                added: taskResult.added_projects || 0,
                updated: taskResult.updated_projects || 0,
                skipped: taskResult.skipped_projects || 0,
                total: taskResult.total_projects || 0,
                updateDetails: taskResult.update_details,
              }
            });
          } else {
            setIncrementalResults({
              message: response.message,
              taskId: taskId,
              portfolioId: response.details.portfolio_id,
              completed: false,
            });
          }
          
          // Don't navigate automatically - let user see results
          setSelectedFile(null);
          setMultipleFiles([]);
          setIncrementalFile(null);
          setSelectedPortfolio('');
          if (fileInputRef.current) {
            fileInputRef.current.value = '';
          }
          return;
        }
      }

      // Reset form state after successful upload
      setSelectedFile(null);
      setMultipleFiles([]);
      setIncrementalFile(null);
      setSelectedPortfolio('');
      setProjectName('');
      setDescription('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Navigate to projects page after successful upload (only for non-incremental)
      navigate('/projects');
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload project. Please try again.');
    } finally {
      // Only set uploading false if not incremental (incremental handles it separately above)
      if (activeTab !== 'incremental') {
        setIsUploading(false);
      }
      setUploadProgress({ current: 0, total: 0 });
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#fafafa',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    }}>
      <Navigation />

      <div style={{
        maxWidth: '900px',
        margin: '0 auto',
        padding: '48px 32px',
      }}>
        {/* Page Header */}
        <div style={{ marginBottom: '32px' }}>
          <h1 style={{
            fontSize: '32px',
            fontWeight: '600',
            color: '#1a1a1a',
            margin: '0 0 8px 0',
            letterSpacing: '-0.5px'
          }}>
            Upload & Analyze Projects
          </h1>
          <p style={{
            fontSize: '16px',
            color: '#737373',
            margin: 0
          }}>
            Upload your code projects for automatic analysis
          </p>
        </div>

        {/* Tab Selector */}
        <div style={{
          display: 'flex',
          backgroundColor: '#f0f0f0',
          borderRadius: '8px',
          padding: '4px',
          marginBottom: '24px',
        }}>
          <button
            onClick={() => handleTabChange('single')}
            style={{
              flex: 1,
              padding: '12px 24px',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              backgroundColor: activeTab === 'single' ? '#ffffff' : 'transparent',
              color: activeTab === 'single' ? '#1a1a1a' : '#737373',
              boxShadow: activeTab === 'single' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            }}
          >
            Single Project
          </button>
          <button
            onClick={() => handleTabChange('multiple')}
            style={{
              flex: 1,
              padding: '12px 24px',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              backgroundColor: activeTab === 'multiple' ? '#ffffff' : 'transparent',
              color: activeTab === 'multiple' ? '#1a1a1a' : '#737373',
              boxShadow: activeTab === 'multiple' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            }}
          >
            Multiple Projects
          </button>
          <button
            onClick={() => handleTabChange('incremental')}
            style={{
              flex: 1,
              padding: '12px 24px',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              backgroundColor: activeTab === 'incremental' ? '#ffffff' : 'transparent',
              color: activeTab === 'incremental' ? '#1a1a1a' : '#737373',
              boxShadow: activeTab === 'incremental' ? '0 1px 3px rgba(0,0,0,0.1)' : 'none',
            }}
          >
            Incremental Upload
          </button>
        </div>

        {/* Upload Card */}
        <div style={{
          backgroundColor: '#ffffff',
          borderRadius: '12px',
          border: '1px solid #e5e5e5',
          padding: '32px',
        }}>
          {activeTab === 'single' ? (
            <>
              {/* Single Project Header */}
              <div style={{ marginBottom: '24px' }}>
                <h2 style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: '0 0 4px 0',
                }}>
                  Upload Single Project
                </h2>
                <p style={{
                  fontSize: '14px',
                  color: '#737373',
                  margin: 0,
                }}>
                  Analyze one project with detailed customization
                </p>
              </div>

              {/* Project Name */}
              <div style={{ marginBottom: '20px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#1a1a1a',
                  marginBottom: '8px',
                }}>
                  Project Name
                </label>
                <input
                  type="text"
                  value={projectName}
                  onChange={(e) => setProjectName(e.target.value)}
                  placeholder="My Awesome Project"
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '1px solid #e5e5e5',
                    borderRadius: '8px',
                    fontSize: '14px',
                    color: '#1a1a1a',
                    backgroundColor: '#fafafa',
                    outline: 'none',
                    transition: 'border-color 0.2s ease',
                    boxSizing: 'border-box',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#1a1a1a'}
                  onBlur={(e) => e.target.style.borderColor = '#e5e5e5'}
                />
              </div>

              {/* Description */}
              <div style={{ marginBottom: '24px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#1a1a1a',
                  marginBottom: '8px',
                }}>
                  Description (Optional)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe your project..."
                  rows={3}
                  style={{
                    width: '100%',
                    padding: '12px 16px',
                    border: '1px solid #e5e5e5',
                    borderRadius: '8px',
                    fontSize: '14px',
                    color: '#1a1a1a',
                    backgroundColor: '#fafafa',
                    outline: 'none',
                    transition: 'border-color 0.2s ease',
                    boxSizing: 'border-box',
                    resize: 'vertical',
                    fontFamily: 'inherit',
                  }}
                  onFocus={(e) => e.target.style.borderColor = '#1a1a1a'}
                  onBlur={(e) => e.target.style.borderColor = '#e5e5e5'}
                />
              </div>
            </>
          ) : activeTab === 'multiple' ? (
            <>
              {/* Multiple Projects Header */}
              <div style={{ marginBottom: '24px' }}>
                <h2 style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: '0 0 4px 0',
                }}>
                  Upload Multiple Projects
                </h2>
                <p style={{
                  fontSize: '14px',
                  color: '#737373',
                  margin: 0,
                }}>
                  Analyze multiple projects at once
                </p>
              </div>
            </>
          ) : (
            <>
              {/* Incremental Upload Header */}
              <div style={{ marginBottom: '24px' }}>
                <h2 style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: '0 0 4px 0',
                }}>
                  Add to Existing Portfolio
                </h2>
                <p style={{
                  fontSize: '14px',
                  color: '#737373',
                  margin: 0,
                }}>
                  Upload additional projects to an existing portfolio
                </p>
              </div>

              {/* Portfolio Selector */}
              <div style={{ marginBottom: '24px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#1a1a1a',
                  marginBottom: '8px',
                }}>
                  Select Portfolio
                </label>
                {loadingPortfolios ? (
                  <div style={{
                    padding: '12px 16px',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px',
                    fontSize: '14px',
                    color: '#737373',
                  }}>
                    Loading portfolios...
                  </div>
                ) : portfolios.length === 0 ? (
                  <div style={{
                    padding: '12px 16px',
                    backgroundColor: '#fef2f2',
                    border: '1px solid #fecaca',
                    borderRadius: '8px',
                    fontSize: '14px',
                    color: '#dc2626',
                  }}>
                    No portfolios found. Please create a portfolio first by uploading a project.
                  </div>
                ) : (
                  <select
                    value={selectedPortfolio}
                    onChange={(e) => setSelectedPortfolio(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '12px 16px',
                      border: '1px solid #e5e5e5',
                      borderRadius: '8px',
                      fontSize: '14px',
                      color: '#1a1a1a',
                      backgroundColor: '#fafafa',
                      outline: 'none',
                      transition: 'border-color 0.2s ease',
                      boxSizing: 'border-box',
                      cursor: 'pointer',
                    }}
                    onFocus={(e) => e.target.style.borderColor = '#1a1a1a'}
                    onBlur={(e) => e.target.style.borderColor = '#e5e5e5'}
                  >
                    <option value="">-- Select a portfolio --</option>
                    {portfolios.map((portfolio) => {
                      const date = new Date(portfolio.analysis_timestamp);
                      const dateStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
                      const timeStr = date.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
                      const displayName = `${portfolio.analysis_type.toUpperCase()} - ${dateStr} at ${timeStr}`;
                      return (
                        <option key={portfolio.analysis_uuid} value={portfolio.analysis_uuid}>
                          {displayName} ({portfolio.total_projects} project{portfolio.total_projects !== 1 ? 's' : ''})
                        </option>
                      );
                    })}
                  </select>
                )}
              </div>
            </>
          )}

          {/* File Upload Area */}
          <div style={{ marginBottom: '24px' }}>
            <label style={{
              display: 'block',
              fontSize: '14px',
              fontWeight: '500',
              color: '#1a1a1a',
              marginBottom: '8px',
            }}>
              Project Files (ZIP) - Max {MAX_FILE_SIZE_MB}MB per file
            </label>

            <div
              onClick={() => fileInputRef.current?.click()}
              onDragEnter={handleDragEnter}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              style={{
                border: `2px dashed ${isDragging ? '#1a1a1a' : '#d1d5db'}`,
                borderRadius: '8px',
                padding: '40px 24px',
                textAlign: 'center',
                cursor: 'pointer',
                backgroundColor: isDragging ? '#f9fafb' : '#ffffff',
                transition: 'all 0.2s ease',
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".zip"
                multiple={activeTab === 'multiple'}
                onChange={handleFileSelect}
                style={{ display: 'none' }}
              />

              {/* Upload Icon */}
              <div style={{ marginBottom: '12px' }}>
                <svg
                  width="40"
                  height="40"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="#9ca3af"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  style={{ margin: '0 auto' }}
                >
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                  <polyline points="17 8 12 3 7 8" />
                  <line x1="12" y1="3" x2="12" y2="15" />
                </svg>
              </div>

              <p style={{
                fontSize: '14px',
                fontWeight: '500',
                color: '#1a1a1a',
                margin: '0 0 4px 0',
              }}>
                Click to upload
              </p>
              <p style={{
                fontSize: '14px',
                color: '#737373',
                margin: 0,
              }}>
                Upload a ZIP file containing your project
              </p>
            </div>
          </div>

          {/* Selected Files Display */}
          {activeTab === 'single' && selectedFile && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 16px',
              backgroundColor: '#f9fafb',
              borderRadius: '8px',
              marginBottom: '24px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                <div>
                  <p style={{ fontSize: '14px', fontWeight: '500', color: '#1a1a1a', margin: 0 }}>
                    {selectedFile.name}
                  </p>
                  <p style={{ fontSize: '12px', color: '#737373', margin: 0 }}>
                    {formatFileSize(selectedFile.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); handleRemoveFile(0); }}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#737373" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          )}

          {activeTab === 'multiple' && multipleFiles.length > 0 && (
            <div style={{ marginBottom: '24px' }}>
              {multipleFiles.map((file, index) => (
                <div
                  key={`${file.name}-${index}`}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '12px 16px',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px',
                    marginBottom: '8px',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" strokeWidth="2">
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                    </svg>
                    <div>
                      <p style={{ fontSize: '14px', fontWeight: '500', color: '#1a1a1a', margin: 0 }}>
                        {file.name}
                      </p>
                      <p style={{ fontSize: '12px', color: '#737373', margin: 0 }}>
                        {formatFileSize(file.size)}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={(e) => { e.stopPropagation(); handleRemoveFile(index); }}
                    style={{
                      background: 'none',
                      border: 'none',
                      cursor: 'pointer',
                      padding: '4px',
                    }}
                  >
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#737373" strokeWidth="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}

          {activeTab === 'incremental' && incrementalFile && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              padding: '12px 16px',
              backgroundColor: '#f9fafb',
              borderRadius: '8px',
              marginBottom: '24px',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#1a1a1a" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
                <div>
                  <p style={{ fontSize: '14px', fontWeight: '500', color: '#1a1a1a', margin: 0 }}>
                    {incrementalFile.name}
                  </p>
                  <p style={{ fontSize: '12px', color: '#737373', margin: 0 }}>
                    {formatFileSize(incrementalFile.size)}
                  </p>
                </div>
              </div>
              <button
                onClick={(e) => { e.stopPropagation(); handleRemoveFile(0); }}
                style={{
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  padding: '4px',
                }}
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#737373" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div style={{
              padding: '12px 16px',
              backgroundColor: '#fef2f2',
              border: '1px solid #fecaca',
              borderRadius: '8px',
              marginBottom: '24px',
            }}>
              <p style={{ fontSize: '14px', color: '#dc2626', margin: 0, whiteSpace: 'pre-line' }}>
                {error}
              </p>
            </div>
          )}

          {/* Upload Progress for Multiple Files */}
          {isUploading && uploadProgress.total > 1 && (
            <div style={{
              padding: '12px 16px',
              backgroundColor: '#eff6ff',
              border: '1px solid #bfdbfe',
              borderRadius: '8px',
              marginBottom: '24px',
            }}>
              <p style={{ fontSize: '14px', color: '#1d4ed8', margin: 0 }}>
                Uploading file {uploadProgress.current} of {uploadProgress.total}...
              </p>
              <div style={{
                marginTop: '8px',
                height: '4px',
                backgroundColor: '#dbeafe',
                borderRadius: '2px',
                overflow: 'hidden',
              }}>
                <div style={{
                  height: '100%',
                  backgroundColor: '#3b82f6',
                  borderRadius: '2px',
                  width: `${(uploadProgress.current / uploadProgress.total) * 100}%`,
                  transition: 'width 0.3s ease',
                }} />
              </div>
            </div>
          )}

          {/* Submit Button */}
          <button
            onClick={handleSubmit}
            disabled={isUploading}
            style={{
              width: '100%',
              padding: '14px 24px',
              backgroundColor: isUploading ? '#9ca3af' : '#1a1a1a',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: isUploading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s ease',
            }}
            onMouseEnter={(e) => {
              if (!isUploading) e.target.style.backgroundColor = '#333333';
            }}
            onMouseLeave={(e) => {
              if (!isUploading) e.target.style.backgroundColor = '#1a1a1a';
            }}
          >
            {isUploading
              ? (uploadProgress.total > 1 ? `Uploading ${uploadProgress.current}/${uploadProgress.total}...` : 'Uploading...')
              : (activeTab === 'incremental' ? 'Add to Portfolio' : activeTab === 'single' ? 'Analyze Project' : 'Analyze Projects')}
          </button>
        </div>
      </div>

      {/* Incremental Upload Results Modal */}
      {incrementalResults && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: '#ffffff',
            borderRadius: '12px',
            padding: '32px',
            maxWidth: '600px',
            width: '90%',
            boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)',
          }}>
            <h2 style={{
              fontSize: '24px',
              fontWeight: '600',
              color: '#1a1a1a',
              marginTop: 0,
              marginBottom: '16px',
            }}>
              {incrementalResults.completed ? 'Portfolio Updated' : 'Upload Processing'}
            </h2>
            
            {incrementalResults.completed && incrementalResults.details ? (
              <>
                <div style={{
                  padding: '16px',
                  backgroundColor: '#dcfce7',
                  border: '1px solid #86efac',
                  borderRadius: '8px',
                  marginBottom: '24px',
                }}>
                  <p style={{ fontSize: '14px', color: '#15803d', margin: 0, fontWeight: '500' }}>
                    Successfully updated portfolio!
                  </p>
                </div>

                <div style={{
                  padding: '16px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  marginBottom: '24px',
                }}>
                  <h3 style={{ fontSize: '16px', fontWeight: '600', color: '#1a1a1a', margin: '0 0 12px 0' }}>
                    Update Summary
                  </h3>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                    <div style={{ padding: '12px', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                      <div style={{ fontSize: '24px', fontWeight: '700', color: '#16a34a' }}>
                        {incrementalResults.details.added}
                      </div>
                      <div style={{ fontSize: '12px', color: '#737373', marginTop: '4px' }}>
                        Projects Added
                      </div>
                    </div>
                    <div style={{ padding: '12px', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                      <div style={{ fontSize: '24px', fontWeight: '700', color: '#2563eb' }}>
                        {incrementalResults.details.updated}
                      </div>
                      <div style={{ fontSize: '12px', color: '#737373', marginTop: '4px' }}>
                        Projects Updated
                      </div>
                    </div>
                    <div style={{ padding: '12px', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                      <div style={{ fontSize: '24px', fontWeight: '700', color: '#d97706' }}>
                        {incrementalResults.details.skipped}
                      </div>
                      <div style={{ fontSize: '12px', color: '#737373', marginTop: '4px' }}>
                        Projects Skipped
                      </div>
                    </div>
                    <div style={{ padding: '12px', backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #e5e7eb' }}>
                      <div style={{ fontSize: '24px', fontWeight: '700', color: '#1a1a1a' }}>
                        {incrementalResults.details.total}
                      </div>
                      <div style={{ fontSize: '12px', color: '#737373', marginTop: '4px' }}>
                        Total Projects
                      </div>
                    </div>
                  </div>
                  
                  {incrementalResults.details.updateDetails && (
                    <div style={{ marginTop: '16px', fontSize: '13px', color: '#737373' }}>
                      {incrementalResults.details.updated > 0 && (
                        <p style={{ margin: '0 0 4px 0' }}>
                          <strong>Updated:</strong> {incrementalResults.details.updateDetails.updated?.map(u => 
                            `${u.project_path || 'root'} (${u.change_percentage}% changed)`
                          ).join(', ')}
                        </p>
                      )}
                      {incrementalResults.details.skipped > 0 && (
                        <p style={{ margin: '4px 0 0 0' }}>
                          <strong>Skipped:</strong> {incrementalResults.details.updateDetails.skipped?.map(s => 
                            `${s.project_path || 'root'} (only ${s.change_percentage}% changed)`
                          ).join(', ')}
                        </p>
                      )}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <>
                <div style={{
                  padding: '16px',
                  backgroundColor: '#eff6ff',
                  border: '1px solid #bfdbfe',
                  borderRadius: '8px',
                  marginBottom: '24px',
                }}>
                  <p style={{ fontSize: '14px', color: '#1d4ed8', margin: 0 }}>
                    {incrementalResults.message}
                  </p>
                  <p style={{ fontSize: '12px', color: '#60a5fa', margin: '8px 0 0 0' }}>
                    Task ID: {incrementalResults.taskId}
                  </p>
                </div>

                <div style={{
                  padding: '16px',
                  backgroundColor: '#f9fafb',
                  borderRadius: '8px',
                  marginBottom: '24px',
                }}>
                  <p style={{ fontSize: '14px', color: '#737373', margin: '0 0 8px 0' }}>
                    Your portfolio is being updated in the background. The system will:
                  </p>
                  <ul style={{ fontSize: '14px', color: '#1a1a1a', margin: 0, paddingLeft: '20px' }}>
                    <li style={{ marginBottom: '4px' }}>Add new projects found in the ZIP file</li>
                    <li style={{ marginBottom: '4px' }}>Update existing projects if changes exceed 30%</li>
                    <li style={{ marginBottom: '4px' }}>Skip projects with minor changes (less than 30%)</li>
                  </ul>
                </div>
              </>
            )}

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => {
                  setIncrementalResults(null);
                  navigate('/projects');
                }}
                style={{
                  padding: '10px 20px',
                  backgroundColor: '#1a1a1a',
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: '500',
                  cursor: 'pointer',
                }}
              >
                View Projects
              </button>
              {!incrementalResults.completed && (
                <button
                  onClick={() => setIncrementalResults(null)}
                  style={{
                    padding: '10px 20px',
                    backgroundColor: '#f3f4f6',
                    color: '#1a1a1a',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    fontSize: '14px',
                    fontWeight: '500',
                    cursor: 'pointer',
                  }}
                >
                  Close
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Upload;
