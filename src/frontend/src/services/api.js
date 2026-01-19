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
    const response = await api.get('/projects');  // Changed from /portfolios to /projects
    return response.data;
  },

  getProjectById: async (portfolioId) => {
    const response = await api.get(`/portfolios/${portfolioId}`);
    return response.data;
  },

  deleteProject: async (portfolioId) => {
    const response = await api.delete(`/portfolios/${portfolioId}`);
    return response.data;
  },
};

export default api;