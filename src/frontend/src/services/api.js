import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    console.error('Error response:', error.response);

    if (error.response?.status === 401) {
      console.log('401 Unauthorized - clearing tokens and redirecting to login');
      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      localStorage.removeItem('token_expiry');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Authentication API calls
export const authAPI = {
  login: async (username, password) => {
    const response = await api.post('/auth/login', { username, password });
    return response.data;
  },

  signup: async (username, password) => {
    const response = await api.post('/auth/signup', { username, password });
    return response.data;
  },

  logout: async () => {
    const response = await api.post('/auth/logout');
    return response.data;
  },
};

// Consent API calls
export const consentAPI = {
  saveConsent: async (hasConsented) => {
    const response = await api.post('/user/consent', { has_consented: hasConsented });
    return response.data;
  },

  getConsent: async () => {
    const response = await api.get('/user/consent');
    return response.data;
  },
};

// Projects API calls
export const projectsAPI = {
  getProjects: async () => {
    const response = await api.get('/projects');
    // API returns { username, total_projects, projects } - extract the projects array
    const data = response.data;
    if (Array.isArray(data)) {
      return data;
    }
    return data?.projects || [];
  },

  getProjectById: async (projectId) => {
    // If you don't have a backend endpoint for this yet, you can remove this later.
    // Keeping as-is in case it's referenced elsewhere.
    const response = await api.get(`/projects/${projectId}`);
    return response.data;
  },

  deleteProject: async (portfolioId) => {
    const response = await api.delete(`/portfolios/${portfolioId}`);
    return response.data;
  },

  getResumeItems: async (projectId) => {
    const response = await api.get(`/projects/${projectId}/resume-items`);
    return response.data;
  },

  getPortfolioItem: async (projectId) => {
    const response = await api.get(`/projects/${projectId}/portfolio`);
    return response.data;
  },

  // Thumbnail methods
  // Note: projectId must be URL-encoded as it may contain special characters (format: uuid:path)
  uploadThumbnail: async (projectId, file) => {
    const formData = new FormData();
    formData.append('file', file);
    const encodedId = encodeURIComponent(projectId);
    // Must explicitly unset Content-Type to override the default 'application/json' header
    // This allows axios to automatically set 'multipart/form-data' with the correct boundary
    const response = await api.post(`/projects/${encodedId}/thumbnail`, formData, {
      headers: {
        'Content-Type': undefined,
      },
    });
    return response.data;
  },

  getThumbnail: async (projectId) => {
    const encodedId = encodeURIComponent(projectId);
    const response = await api.get(`/projects/${encodedId}/thumbnail`, {
      responseType: 'blob',
    });
    return URL.createObjectURL(response.data);
  },

  deleteThumbnail: async (projectId) => {
    const encodedId = encodeURIComponent(projectId);
    const response = await api.delete(`/projects/${encodedId}/thumbnail`);
    return response.data;
  },
};

export const portfoliosAPI = {
  listPortfolios: async () => {
    const response = await api.get('/portfolios');
    return response.data;
  },

  getPortfolioDetail: async (portfolioId) => {
    const response = await api.get(`/portfolios/${portfolioId}`);
    return response.data;
  },

  generatePortfolioDocument: async (portfolioId) => {
    const response = await api.post('/portfolio/generate', { portfolio_id: portfolioId });
    return response.data;
  },
};

// Resume API calls
export const resumeAPI = {
  generateResume: async (projectIds, options = {}) => {
    const response = await api.post('/resume/generate', {
      project_ids: projectIds,
      format: options.format || 'markdown',
      include_skills: options.include_skills !== false,
      include_projects: options.include_projects !== false,
      max_projects: options.max_projects || null,
      personal_info: options.personal_info || null,
      stored_resume_id: options.stored_resume_id || null,
    });
    return response.data;
  },

  createStoredResume: async (payload) => {
    const response = await api.post('/resumes', payload);
    return response.data;
  },

  listStoredResumes: async () => {
    const response = await api.get('/resumes');
    return response.data;
  },

  getStoredResume: async (resumeId) => {
    const response = await api.get(`/resumes/${resumeId}`);
    return response.data;
  },

  updateStoredResume: async (resumeId, content) => {
    const response = await api.patch(`/resumes/${resumeId}`, { content });
    return response.data;
  },

  addItemsToResume: async (resumeId, resumeItemIds) => {
    const response = await api.post(`/resumes/${resumeId}/items`, {
      resume_item_ids: resumeItemIds,
    });
    return response.data;
  },
};

export default api;