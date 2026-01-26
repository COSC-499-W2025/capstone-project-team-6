import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock useNavigate
const mockNavigate = vi.fn();

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock the AuthContext module - use factory function
vi.mock('../contexts/AuthContext', () => {
  return {
    useAuth: vi.fn(),
  };
});

// Mock the API module - use factory function
vi.mock('../services/api', () => {
  return {
    projectsAPI: {
      getProjects: vi.fn(),
    },
  };
});

// Import after all mocks are set up
import ProjectsPage from '../ProjectsPage';
import { useAuth } from '../contexts/AuthContext';
import { projectsAPI } from '../services/api';

// Helper to render with auth context and router
const renderWithAuth = (isAuthenticated = true, user = { id: 1, email: 'test@example.com' }) => {
  useAuth.mockReturnValue({ isAuthenticated, user });
  
  return render(
    <BrowserRouter>
      <ProjectsPage />
    </BrowserRouter>
  );
};

describe('ProjectsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  describe('Authentication', () => {
    it('redirects to login when not authenticated', () => {
      renderWithAuth(false, null);
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });

    it('does not redirect when authenticated', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth(true);
      
      await waitFor(() => {
        expect(mockNavigate).not.toHaveBeenCalledWith('/login');
      });
    });
  });

  describe('Loading State', () => {
    it('displays loading message initially', () => {
      projectsAPI.getProjects.mockImplementation(() => new Promise(() => {}));
      renderWithAuth();
      
      expect(screen.getByText('Loading projects...')).toBeInTheDocument();
    });

    it('hides loading message after data loads', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.queryByText('Loading projects...')).not.toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('displays error message when API call fails', async () => {
      const errorMessage = 'Failed to fetch projects';
      projectsAPI.getProjects.mockRejectedValue({
        response: { data: { detail: errorMessage } },
      });
      
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText(/Failed to fetch projects/i)).toBeInTheDocument();
      });
    });

    it('displays generic error message when no detail provided', async () => {
      projectsAPI.getProjects.mockRejectedValue(new Error('Network error'));
      
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText(/Network error/i)).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('displays no projects message when array is empty', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('No projects found.')).toBeInTheDocument();
      });
    });

    it('shows total projects as 0 when no projects', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('0')).toBeInTheDocument();
      });
    });
  });

  describe('Projects Display', () => {
    const mockProjects = [
      {
        id: 1,
        project_name: 'Test Project 1',
        primary_language: 'JavaScript',
        total_files: 25,
        has_tests: true,
        effective_last_modified_date: '2024-01-15T10:30:00Z',
      },
      {
        id: 2,
        project_name: 'Test Project 2',
        primary_language: 'Python',
        total_files: 42,
        has_tests: false,
        effective_last_modified_date: '2024-01-20T14:45:00Z',
      },
    ];

    it('displays all projects', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('Test Project 1')).toBeInTheDocument();
        expect(screen.getByText('Test Project 2')).toBeInTheDocument();
      });
    });

    it('displays correct project count', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('2')).toBeInTheDocument();
      });
    });

    it('displays project details correctly', async () => {
      projectsAPI.getProjects.mockResolvedValue([mockProjects[0]]);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
        expect(screen.getByText('25')).toBeInTheDocument();
        expect(screen.getByText('Yes')).toBeInTheDocument();
      });
    });

    it('handles projects without optional fields', async () => {
      const projectWithMissingFields = {
        id: 3,
        project_name: null,
        primary_language: null,
        total_files: 0,
        has_tests: false,
        effective_last_modified_date: null,
      };
      
      projectsAPI.getProjects.mockResolvedValue([projectWithMissingFields]);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('Unnamed Project')).toBeInTheDocument();
        expect(screen.getByText('Unknown')).toBeInTheDocument();
        expect(screen.getByText('N/A')).toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('has a back to dashboard button in header', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      await waitFor(() => {
        const buttons = screen.getAllByText('Back to Dashboard');
        expect(buttons.length).toBeGreaterThan(0);
      });
    });

    it('navigates to dashboard when back button is clicked', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      await waitFor(() => {
        const backButton = screen.getAllByText('Back to Dashboard')[0];
        backButton.click();
        expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
      });
    });

    it('shows go to dashboard button in empty state', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('Go to Dashboard')).toBeInTheDocument();
      });
    });
  });

  describe('Page Header', () => {
    it('displays page title', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      expect(screen.getByText('My Projects')).toBeInTheDocument();
    });

    it('displays total projects label', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      expect(screen.getByText('Total Projects')).toBeInTheDocument();
    });
  });
});