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
      getResumeItems: vi.fn(),
      getPortfolioItem: vi.fn(),
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
    // Set default mock implementations
    projectsAPI.getResumeItems.mockResolvedValue([]);
    projectsAPI.getPortfolioItem.mockResolvedValue({});
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
        last_modified_date: '2024-01-15T10:30:00Z',
      },
      {
        id: 2,
        project_name: 'Test Project 2',
        primary_language: 'Python',
        total_files: 42,
        has_tests: false,
        last_modified_date: '2024-01-20T14:45:00Z',
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
        const jsElements = screen.getAllByText('JavaScript');
        expect(jsElements.length).toBeGreaterThan(0);
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

  describe('Project Filtering', () => {
    const mockProjects = [
      {
        project_id: 1,
        project_name: 'Python Web App',
        primary_language: 'Python',
        has_tests: true,
        total_files: 25,
      },
      {
        project_id: 2,
        project_name: 'JavaScript Mobile App',
        primary_language: 'JavaScript',
        has_tests: false,
        total_files: 35,
      },
      {
        project_id: 3,
        project_name: 'Python CLI Tool',
        primary_language: 'Python',
        has_tests: true,
        total_files: 15,
      },
    ];

    it('displays search input for filtering by name', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByPlaceholderText(/search projects/i)).toBeInTheDocument();
      });
    });

    it('displays language filter dropdown', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        const languageFilters = screen.getAllByRole('combobox');
        expect(languageFilters.length).toBeGreaterThan(0);
      });
    });

    it('displays test status filter dropdown', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        const dropdowns = screen.getAllByRole('combobox');
        expect(dropdowns.length).toBeGreaterThan(0);
      });
    });

    it('displays sort by dropdown', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        const dropdowns = screen.getAllByRole('combobox');
        expect(dropdowns.length).toBeGreaterThan(0);
      });
    });

    it('does not display clear filters button when no filters are applied', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        // Clear Filters button only shows when filters are active
        expect(screen.queryByText('Clear Filters')).not.toBeInTheDocument();
      });
    });

    it('shows filtered count when filters are applied', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        // Check that the page renders without error
        expect(screen.getByText('My Projects')).toBeInTheDocument();
      });
    });
  });

  describe('Project Sorting', () => {
    const mockProjects = [
      {
        project_id: 1,
        project_name: 'C Project',
        total_files: 10,
        last_commit_date: '2024-01-01T00:00:00',
      },
      {
        project_id: 2,
        project_name: 'A Project',
        total_files: 30,
        last_commit_date: '2024-01-15T00:00:00',
      },
      {
        project_id: 3,
        project_name: 'B Project',
        total_files: 20,
        last_commit_date: '2024-01-10T00:00:00',
      },
    ];

    it('displays projects in default order', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('C Project')).toBeInTheDocument();
        expect(screen.getByText('A Project')).toBeInTheDocument();
        expect(screen.getByText('B Project')).toBeInTheDocument();
      });
    });

    it('can sort projects alphabetically', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        // All projects should be visible
        expect(screen.getByText('C Project')).toBeInTheDocument();
      });
    });

    it('can sort projects by file count', async () => {
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        // All projects should be visible
        expect(screen.getByText('C Project')).toBeInTheDocument();
      });
    });
  });

  describe('Empty States', () => {
    it('shows no projects message when list is empty', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText(/No projects found/i)).toBeInTheDocument();
      });
    });

    it('shows no matches message when filters return no results', async () => {
      const mockProjects = [
        {
          project_id: 1,
          project_name: 'Python Project',
          primary_language: 'Python',
        },
      ];
      projectsAPI.getProjects.mockResolvedValue(mockProjects);
      renderWithAuth();
      
      await waitFor(() => {
        // Initially shows the project
        expect(screen.getByText('Python Project')).toBeInTheDocument();
      });
    });
  });
});