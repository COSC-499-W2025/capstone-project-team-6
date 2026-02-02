import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import api from '../services/api';

// Max file size: 100MB
const MAX_FILE_SIZE_MB = 100;
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

  // UI state
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });

  // Clear form state when switching tabs
  const handleTabChange = (tab) => {
    setActiveTab(tab);
    setSelectedFile(null);
    setMultipleFiles([]);
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
    } else {
      setMultipleFiles(prev => [...prev, ...validFiles]);
    }
  };

  const handleRemoveFile = (index) => {
    if (activeTab === 'single') {
      setSelectedFile(null);
    } else {
      setMultipleFiles(prev => prev.filter((_, i) => i !== index));
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
      } else {
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
      }

      // Reset form state after successful upload
      setSelectedFile(null);
      setMultipleFiles([]);
      setProjectName('');
      setDescription('');
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }

      // Navigate to projects page after successful upload
      navigate('/projects');
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload project. Please try again.');
    } finally {
      setIsUploading(false);
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
          ) : (
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
              : (activeTab === 'single' ? 'Analyze Project' : 'Analyze Projects')}
          </button>
        </div>
      </div>
    </div>
  );
};

export default Upload;
