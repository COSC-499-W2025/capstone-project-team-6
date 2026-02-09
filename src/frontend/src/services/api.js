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
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    console.error('Error response:', error.response);
    
    if (error.response?.status === 401) {
      console.log('401 Unauthorized - clearing tokens and redirecting to login');
      // Clear token and redirect to login
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
    return response.data || [];
  },

  getProjectById: async (portfolioId) => {
    const response = await api.get(`/portfolios/${portfolioId}`);
    return response.data;
  },

  deleteProject: async (projectId) => {
    const response = await api.delete(`/projects/${projectId}`);
    return response.data;
  },

  deleteAllProjects: async () => {
    const response = await api.delete('/projects');
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
};

export const portfolioAPI = {
  getPortfolios: async () => {
    const response = await api.get('/portfolios');
    return response.data;
  },

  getPortfolioById: async (portfolioId) => {
    const response = await api.get(`/portfolios/${portfolioId}`);
    return response.data;
  }
};

// Resume API calls
export const resumeAPI = {
  generateResume: async (portfolioIds, options = {}) => {
    const response = await api.post('/resume/generate', {
      portfolio_ids: portfolioIds,
      format: options.format || 'markdown',
      include_skills: options.include_skills !== false,
      include_projects: options.include_projects !== false,
      max_projects: options.max_projects || null,
      personal_info: options.personal_info || null,
    });
    return response.data;
  },
};

// Curation API calls
export const curationAPI = {
  // Get user's curation settings
  getSettings: async () => {
    const response = await api.get('/curation/settings');
    return response.data;
  },

  // Get all projects for curation
  getProjects: async () => {
    const response = await api.get('/curation/projects');
    return response.data;
  },

  // Get showcase projects
  getShowcase: async () => {
    const response = await api.get('/curation/showcase');
    return response.data;
  },

  // Get available skills
  getSkills: async () => {
    const response = await api.get('/curation/skills');
    return response.data;
  },

  // Get available comparison attributes
  getAttributes: async () => {
    const response = await api.get('/curation/attributes');
    return response.data;
  },

  // Save chronology correction
  saveChronology: async (projectId, dates) => {
    const response = await api.post('/curation/chronology', {
      project_id: projectId,
      last_commit_date: dates.last_commit_date || null,
      last_modified_date: dates.last_modified_date || null,
      project_start_date: dates.project_start_date || null,
      project_end_date: dates.project_end_date || null,
    });
    return response.data;
  },

  // Save showcase projects (max 3)
  saveShowcase: async (projectIds) => {
    const response = await api.post('/curation/showcase', {
      project_ids: projectIds,
    });
    return response.data;
  },

  // Save comparison attributes
  saveAttributes: async (attributes) => {
    const response = await api.post('/curation/attributes', {
      attributes: attributes,
    });
    return response.data;
  },

  // Save project order
  saveOrder: async (projectIds) => {
    const response = await api.post('/curation/order', {
      project_ids: projectIds,
    });
    return response.data;
  },

  // Save highlighted skills (max 10)
  saveSkills: async (skills) => {
    const response = await api.post('/curation/skills', {
      skills: skills,
    });
    return response.data;
  },
};

export default api;