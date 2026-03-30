import { useState, useRef, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import Navigation from '../components/Navigation';
import api from '../services/api';
import { consentAPI, portfoliosAPI } from '../services/api';

// Max file size: 500MB
const MAX_FILE_SIZE_MB = 500;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

/** Incremental upload: show project name(s) first, then date, analysis type, and count (matches Portfolio page intent). */
const formatIncrementalPortfolioOptionLabel = (portfolio) => {
  const projectNames = Array.isArray(portfolio.project_names)
    ? portfolio.project_names.filter(Boolean)
    : [];

  let primaryLabel;
  if (projectNames.length === 0) {
    const base = (portfolio.zip_file || '').replace(/\\/g, '/').split('/').pop() || '';
    primaryLabel = base.replace(/\.zip$/i, '') || 'Unnamed project';
  } else if (projectNames.length === 1) {
    primaryLabel = projectNames[0];
  } else if (projectNames.length <= 3) {
    primaryLabel = projectNames.join(', ');
  } else {
    primaryLabel = `${projectNames.slice(0, 2).join(', ')} + ${projectNames.length - 2} more`;
  }

  const date = new Date(portfolio.analysis_timestamp);
  const dateTimeStr = Number.isNaN(date.getTime())
    ? (portfolio.analysis_timestamp || '—')
    : date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      });

  const typeStr = (portfolio.analysis_type || '').toUpperCase() || '—';
  const n = portfolio.total_projects ?? 0;
  const projectsStr = `${n} project${n !== 1 ? 's' : ''}`;

  return `${primaryLabel} — ${dateTimeStr} · ${typeStr} · ${projectsStr}`;
};

const Upload = () => {
  const navigate = useNavigate();
  const location = useLocation();
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
  const [duplicateFiles, setDuplicateFiles] = useState([]);

  // Form state for incremental upload
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState('');
  const [incrementalFile, setIncrementalFile] = useState(null);
  const [loadingPortfolios, setLoadingPortfolios] = useState(false);

  // UI state
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [duplicateMessage, setDuplicateMessage] = useState(location.state?.duplicateMessage || '');
  const [uploadProgress, setUploadProgress] = useState({ current: 0, total: 0 });
  const [incrementalResults, setIncrementalResults] = useState(null);

  // Consent and analysis type: fetch consent on mount; default LLM on when consented
  const [hasConsented, setHasConsented] = useState(false);
  const [useLLMAnalysis, setUseLLMAnalysis] = useState(true);

  useEffect(() => {
    consentAPI.getConsent()
      .then((res) => {
        const consented = !!res?.has_consented;
        setHasConsented(consented);
        setUseLLMAnalysis(consented);
      })
      .catch(() => {
        setHasConsented(false);
        setUseLLMAnalysis(false);
      });
  }, []);

  // Sync duplicateMessage from navigation state (e.g. when AnalyzePage navigates back)
  useEffect(() => {
    const msg = location.state?.duplicateMessage;
    if (msg) setDuplicateMessage(msg);
  }, [location.state?.duplicateMessage]);

  const effectiveAnalysisType = (hasConsented && useLLMAnalysis) ? 'llm' : 'non_llm';

  const canAnalyzeSingle = selectedFile && projectName.trim().length > 0;
  const hasDuplicates = duplicateFiles.length > 0;
  const isSubmitDisabled = isUploading || (activeTab === 'single' && !canAnalyzeSingle)
    || (activeTab === 'incremental' && (!selectedPortfolio || !incrementalFile))
    || (activeTab === 'multiple' && (multipleFiles.length === 0 || hasDuplicates));

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
      console.error('Error loading projects for incremental upload:', err);
      setError('Failed to load projects');
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
    setDuplicateFiles([]);
    setError('');
    setDuplicateMessage('');
    setProjectName('');
    setDescription('');
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

  const createFileId = (file) => {
    return `${file.name}::${file.size}::${file.lastModified || 0}`;
  };

  const checkForDuplicates = (existingFiles, newFiles) => {
    const existingIds = new Set(existingFiles.map(createFileId));
    const newIds = new Map();
    const duplicates = [];
    const uniqueNewFiles = [];

    for (const file of newFiles) {
      const fileId = createFileId(file);
      if (existingIds.has(fileId)) {
        duplicates.push({
          file,
          reason: 'Already in upload list'
        });
        continue;
      }
      
      if (newIds.has(fileId)) {
        duplicates.push({
          file,
          reason: 'Duplicate in current selection'
        });
        continue;
      }
      
      newIds.set(fileId, file);
      uniqueNewFiles.push(file);
    }

    return { duplicates, uniqueNewFiles };
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
      const { duplicates, uniqueNewFiles } = checkForDuplicates(multipleFiles, validFiles);
      
      if (duplicates.length > 0) {
        setDuplicateFiles(duplicates);
        if (uniqueNewFiles.length > 0) {
          setMultipleFiles(prev => [...prev, ...uniqueNewFiles]);
        }
      } else {
        setMultipleFiles(prev => [...prev, ...validFiles]);
        setDuplicateFiles([]);
      }
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
  };

  const handleSubmit = async () => {
    if (activeTab === 'single' && !selectedFile) {
      setError('Please select a ZIP file to upload');
      return;
    }
    if (activeTab === 'single' && !projectName.trim()) {
      setError('Please enter a project name');
      return;
    }

    if (activeTab === 'multiple' && multipleFiles.length === 0) {
      setError('Please select at least one ZIP file to upload');
      return;
    }

    if (activeTab === 'multiple' && hasDuplicates) {
      setError('Please remove duplicate files before proceeding with the analysis');
      return;
    }

    if (activeTab === 'incremental') {
      if (!selectedPortfolio) {
        setError('Please select a project to add to');
        return;
      }
      if (!incrementalFile) {
        setError('Please select a ZIP file to upload');
        return;
      }
    }

    setIsUploading(true);
    setError('');
    setDuplicateMessage('');
    setDuplicateFiles([]);

    let taskIdForAnalyze = null;
    let taskIdsForAnalyze = [];
    let multipleSkippedDuplicates = [];
    let multipleTotalFiles = 0;
    try {
      if (activeTab === 'single') {
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('analysis_type', effectiveAnalysisType);
        formData.append('project_name', projectName.trim());

        const res = await api.post('/portfolios/upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });

        // Duplicate: this ZIP was already analysed — skip re-analysis
        if (res?.data?.details?.duplicate === true) {
          setDuplicateMessage('This project has already been analyzed. You can view it in your projects.');
          return;
        }

        // Backend returns task_id inside details
        const taskId = res?.data?.task_id || res?.data?.details?.task_id;

        if (!taskId) {
          throw new Error("Upload succeeded but no task_id was returned by the server.");
        }

        // Go straight to Analyze page; persist taskId for refresh/back navigation
        taskIdForAnalyze = taskId;
        sessionStorage.setItem("analyze_task_id", taskId);
        sessionStorage.setItem("analyze_project_type", "single");
        sessionStorage.setItem("analyze_analysis_type", effectiveAnalysisType);
        sessionStorage.setItem("analyze_project_name", projectName.trim());
        navigate("/analyze", { state: { taskId, projectType: 'single', analysisType: effectiveAnalysisType, projectName: projectName.trim() } });
        return;


      } else if (activeTab === 'multiple') {
        // Upload multiple files with progress tracking and error aggregation
        const uploadErrors = [];
        const duplicates = [];
        const total = multipleFiles.length;
        multipleTotalFiles = total;
        setUploadProgress({ current: 0, total });

        for (let i = 0; i < multipleFiles.length; i++) {
          const file = multipleFiles[i];
          setUploadProgress({ current: i + 1, total });

          try {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('analysis_type', effectiveAnalysisType);

            const res = await api.post('/portfolios/upload', formData, { headers: { 'Content-Type': 'multipart/form-data' } });
            if (res?.data?.details?.duplicate) {
              duplicates.push(file.name);
            } else {
              const taskId = res?.data?.task_id || res?.data?.details?.task_id;
              if (taskId) {
                taskIdsForAnalyze.push(taskId);
              }
            }
          } catch (err) {
            const errorMsg = err.response?.data?.detail || 'Upload failed';
            uploadErrors.push(`${file.name}: ${errorMsg}`);
          }
        }

        // If there were actual upload errors (not duplicates), show them
        if (uploadErrors.length > 0) {
          const successCount = taskIdsForAnalyze.length;
          const errorLines = uploadErrors.join('\n');
          const dupNote = duplicates.length > 0 ? `\nAlready analyzed (skipped): ${duplicates.join(', ')}` : '';
          if (successCount > 0) {
            setError(`${successCount} file(s) uploaded. Failed:\n${errorLines}${dupNote}`);
          } else {
            setError(`All uploads failed:\n${errorLines}${dupNote}`);
          }
          if (taskIdsForAnalyze.length === 0) {
            setIsUploading(false);
            setUploadProgress({ current: 0, total: 0 });
            return;
          }
        } else if (duplicates.length > 0 && taskIdsForAnalyze.length === 0) {
          // All files were duplicates — nothing new to analyze
          setError(`All ${duplicates.length} ${duplicates.length === 1 ? 'project has' : 'projects have'} already been analyzed. You can view them in your projects.`);
          setIsUploading(false);
          setUploadProgress({ current: 0, total: 0 });
          return;
        }
        multipleSkippedDuplicates = duplicates;
      } else if (activeTab === 'incremental') {
        // Upload to existing analysis (selected project)
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

      // Navigate to analyze page after successful upload
      if (activeTab === 'multiple' && taskIdsForAnalyze.length > 0) {
        sessionStorage.setItem("analyze_task_ids", JSON.stringify(taskIdsForAnalyze));
        sessionStorage.setItem("analyze_analysis_type", effectiveAnalysisType);
        navigate("/analyze", {
          state: {
            taskIds: taskIdsForAnalyze,
            analysisType: effectiveAnalysisType,
            skippedDuplicates: multipleSkippedDuplicates,
            totalFiles: multipleTotalFiles,
          },
        });
      } else if (taskIdForAnalyze) {
        navigate("/analyze", { state: { taskId: taskIdForAnalyze } });
      } else {
        navigate('/analyze');
      }
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to upload project. Please try again.');
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

        {/* Duplicate Message — shown above the card so it is always visible */}
        {duplicateMessage && (
          <div style={{
            padding: '16px 20px',
            backgroundColor: '#eff6ff',
            border: '1px solid #93c5fd',
            borderRadius: '10px',
            marginBottom: '24px',
          }}>
            <p style={{ fontSize: '15px', fontWeight: '500', color: '#1d4ed8', margin: 0 }}>
              {duplicateMessage}
            </p>
          </div>
        )}

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

             

              {/* AI-enhanced analysis (requires consent) */}
              <div style={{ marginBottom: '24px' }}>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  fontSize: '14px',
                  color: '#1a1a1a',
                  cursor: hasConsented ? 'pointer' : 'not-allowed',
                  opacity: hasConsented ? 1 : 0.6,
                }}>
                  <input
                    type="checkbox"
                    checked={useLLMAnalysis}
                    onChange={(e) => setUseLLMAnalysis(e.target.checked)}
                    disabled={!hasConsented}
                    style={{ width: '18px', height: '18px', cursor: hasConsented ? 'pointer' : 'not-allowed' }}
                  />
                  <span>Use AI-enhanced analysis (requires consent in Settings)</span>
                </label>
                {!hasConsented && (
                  <p style={{ fontSize: '12px', color: '#737373', margin: '4px 0 0 28px' }}>
                    Enable in Settings to use AI-powered analysis
                  </p>
                )}
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

              {/* AI-enhanced analysis for multiple */}
              <div style={{ marginBottom: '24px' }}>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '10px',
                  fontSize: '14px',
                  color: '#1a1a1a',
                  cursor: hasConsented ? 'pointer' : 'not-allowed',
                  opacity: hasConsented ? 1 : 0.6,
                }}>
                  <input
                    type="checkbox"
                    checked={useLLMAnalysis}
                    onChange={(e) => setUseLLMAnalysis(e.target.checked)}
                    disabled={!hasConsented}
                    style={{ width: '18px', height: '18px', cursor: hasConsented ? 'pointer' : 'not-allowed' }}
                  />
                  <span>Use AI-enhanced analysis (requires consent in Settings)</span>
                </label>
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
                  Add to Existing Project
                </h2>
                <p style={{
                  fontSize: '14px',
                  color: '#737373',
                  margin: 0,
                }}>
                  Upload additional projects to an existing project
                </p>
              </div>

              {/* Project selector (existing analysis to extend) */}
              <div style={{ marginBottom: '24px' }}>
                <label style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: '500',
                  color: '#1a1a1a',
                  marginBottom: '8px',
                }}>
                  Select Project
                </label>
                {loadingPortfolios ? (
                  <div style={{
                    padding: '12px 16px',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px',
                    fontSize: '14px',
                    color: '#737373',
                  }}>
                    Loading projects...
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
                    No projects found. Please create a project first by uploading one.
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
                    <option value="">-- Select a project --</option>
                    {portfolios.map((portfolio) => (
                      <option key={portfolio.analysis_uuid} value={portfolio.analysis_uuid}>
                        {formatIncrementalPortfolioOptionLabel(portfolio)}
                      </option>
                    ))}
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

          {/* Duplicate Files Warning */}
          {activeTab === 'multiple' && duplicateFiles.length > 0 && (
            <div style={{ 
              marginBottom: '16px',
              padding: '12px 16px',
              backgroundColor: '#fef2f2',
              borderRadius: '6px',
              border: '1px solid #fecaca'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="2">
                  <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                  <path d="M12 9v4"/>
                  <path d="m12 17 .01 0"/>
                </svg>
                <p style={{ 
                  fontSize: '13px', 
                  color: '#dc2626', 
                  margin: 0,
                  fontWeight: '500'
                }}>
                  Duplicate file detected: {duplicateFiles.map(d => d.file.name).join(', ')}. Only the first instance will be uploaded. 
                </p>
              </div>
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
            disabled={isSubmitDisabled}
            style={{
              width: '100%',
              padding: '14px 24px',
              backgroundColor: isSubmitDisabled ? '#9ca3af' : '#1a1a1a',
              color: '#ffffff',
              border: 'none',
              borderRadius: '8px',
              fontSize: '14px',
              fontWeight: '500',
              cursor: isSubmitDisabled ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s ease',
            }}
            onMouseEnter={(e) => {
              if (!isSubmitDisabled) e.target.style.backgroundColor = '#333333';
            }}
            onMouseLeave={(e) => {
              if (!isSubmitDisabled) e.target.style.backgroundColor = '#1a1a1a';
            }}
          >
            {isUploading
              ? (uploadProgress.total > 1 ? `Uploading ${uploadProgress.current}/${uploadProgress.total}...` : 'Uploading...')
              : hasDuplicates 
                ? 'Remove Duplicates to Continue'
                : (activeTab === 'incremental' ? 'Add to Project' : activeTab === 'single' ? 'Analyze Project' : 'Analyze Projects')}
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
              {incrementalResults.completed ? 'Project Updated' : 'Upload Processing'}
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
                    Successfully updated project!
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
                    Your project is being updated in the background. The system will:
                  </p>
                  <ul style={{ fontSize: '14px', color: '#1a1a1a', margin: 0, paddingLeft: '20px' }}>
                    <li style={{ marginBottom: '4px' }}>Add new projects found in the ZIP file</li>
                    <li style={{ marginBottom: '4px' }}>Update existing projects if changes exceed about 5%</li>
                    <li style={{ marginBottom: '4px' }}>Skip projects with smaller detected changes (about 5% or less)</li>
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
