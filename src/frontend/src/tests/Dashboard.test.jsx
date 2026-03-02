import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock useNavigate
const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => {
  return {
    useAuth: vi.fn(),
  };
});

// Mock API module
vi.mock('../services/api', () => {
  return {
    default: {
      get: vi.fn(),
    },
    projectsAPI: {
      getProjects: vi.fn(),
    },
    portfoliosAPI: {
      listPortfolios: vi.fn(),
    },
    curationAPI: {
      getShowcase: vi.fn(),
    },
  };
});

// Mock Navigation component
vi.mock('../components/Navigation', () => ({
  default: () => <nav data-testid="mock-navigation">Navigation</nav>,
}));

// Import after mocks
import Dashboard from '../pages/Dashboard';
import { useAuth } from '../contexts/AuthContext';
import { projectsAPI, portfoliosAPI, curationAPI } from '../services/api';
import api from '../services/api';

const renderDashboard = (isAuthenticated = true, user = { username: 'testuser' }) => {
  useAuth.mockReturnValue({
    isAuthenticated,
    user,
    logout: vi.fn(),
  });

  return render(
    <MemoryRouter>
      <Dashboard />
    </MemoryRouter>
  );
};

describe('Dashboard — Showcase Projects', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    // Sensible defaults for all APIs
    projectsAPI.getProjects.mockResolvedValue([]);
    portfoliosAPI.listPortfolios.mockResolvedValue([]);
    api.get.mockResolvedValue({ data: { total_skills: 0 } });
    curationAPI.getShowcase.mockResolvedValue([]);
  });

  // ---------- Showcase Section Rendering ----------

  describe('Showcase section rendering', () => {
    it('renders the Showcase Projects heading', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText(/Showcase Projects/)).toBeInTheDocument();
      });
    });

    it('shows empty state when no showcase projects are set', async () => {
      curationAPI.getShowcase.mockResolvedValue([]);
      renderDashboard();

      await waitFor(() => {
        expect(
          screen.getByText(/No showcase projects selected yet/i)
        ).toBeInTheDocument();
      });
    });

    it('shows "Select your top projects" button in empty state', async () => {
      curationAPI.getShowcase.mockResolvedValue([]);
      renderDashboard();

      await waitFor(() => {
        expect(
          screen.getByText(/Select your top projects/i)
        ).toBeInTheDocument();
      });
    });

    it('renders showcase project cards when data exists', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: 'Alpha Project',
          primary_language: 'Python',
          total_files: 25,
          has_tests: true,
          frameworks: ['Django', 'Celery'],
        },
        {
          id: 2,
          project_name: 'Beta Project',
          primary_language: 'TypeScript',
          total_files: 40,
          has_tests: false,
          frameworks: ['React'],
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument();
        expect(screen.getByText('Beta Project')).toBeInTheDocument();
      });
    });

    it('displays Top 1, Top 2, Top 3 badges', async () => {
      const showcaseData = [
        { id: 1, project_name: 'First', primary_language: 'Go', total_files: 10 },
        { id: 2, project_name: 'Second', primary_language: 'Rust', total_files: 20 },
        { id: 3, project_name: 'Third', primary_language: 'Java', total_files: 30 },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText(/Top 1/)).toBeInTheDocument();
        expect(screen.getByText(/Top 2/)).toBeInTheDocument();
        expect(screen.getByText(/Top 3/)).toBeInTheDocument();
      });
    });

    it('displays project language and file count', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: 'My App',
          primary_language: 'Kotlin',
          total_files: 55,
          has_tests: true,
          frameworks: [],
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Kotlin')).toBeInTheDocument();
        expect(screen.getByText(/55 files/)).toBeInTheDocument();
      });
    });

    it('displays "Has tests" indicator when project has tests', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: 'Tested App',
          primary_language: 'Python',
          total_files: 20,
          has_tests: true,
          frameworks: [],
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText(/Has tests/)).toBeInTheDocument();
      });
    });

    it('does not show "Has tests" when project has no tests', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: 'Untested App',
          primary_language: 'Ruby',
          total_files: 15,
          has_tests: false,
          frameworks: [],
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Untested App')).toBeInTheDocument();
        expect(screen.queryByText(/Has tests/)).not.toBeInTheDocument();
      });
    });

    it('displays framework badges', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: 'FW App',
          primary_language: 'Python',
          total_files: 30,
          has_tests: false,
          frameworks: ['Flask', 'SQLAlchemy', 'Celery'],
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Flask')).toBeInTheDocument();
        expect(screen.getByText('SQLAlchemy')).toBeInTheDocument();
        expect(screen.getByText('Celery')).toBeInTheDocument();
      });
    });

    it('limits framework badges to 3', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: 'Many FW',
          primary_language: 'JS',
          total_files: 10,
          has_tests: false,
          frameworks: ['React', 'Redux', 'Express', 'Mongoose', 'Jest'],
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('React')).toBeInTheDocument();
        expect(screen.getByText('Redux')).toBeInTheDocument();
        expect(screen.getByText('Express')).toBeInTheDocument();
        // 4th and 5th should be hidden
        expect(screen.queryByText('Mongoose')).not.toBeInTheDocument();
        expect(screen.queryByText('Jest')).not.toBeInTheDocument();
      });
    });

    it('handles project with no frameworks gracefully', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: 'No FW',
          primary_language: 'C',
          total_files: 5,
          has_tests: false,
          frameworks: [],
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('No FW')).toBeInTheDocument();
      });
    });

    it('handles missing project_name gracefully', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: null,
          primary_language: 'Python',
          total_files: 10,
          has_tests: false,
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Unnamed Project')).toBeInTheDocument();
      });
    });

    it('handles missing primary_language gracefully', async () => {
      const showcaseData = [
        {
          id: 1,
          project_name: 'NoLang',
          primary_language: null,
          total_files: 10,
          has_tests: false,
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Unknown language')).toBeInTheDocument();
      });
    });
  });

  // ---------- Navigation ----------

  describe('Showcase card navigation', () => {
    it('navigates to /projects with showcaseProjectId state on click', async () => {
      const showcaseData = [
        {
          id: 42,
          project_name: 'Click Me',
          primary_language: 'Go',
          total_files: 12,
          has_tests: false,
        },
      ];

      curationAPI.getShowcase.mockResolvedValue(showcaseData);
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Click Me')).toBeInTheDocument();
      });

      // Click the card
      screen.getByText('Click Me').closest('div[style]').click();

      expect(mockNavigate).toHaveBeenCalledWith('/projects', {
        state: { showcaseProjectId: 42 },
      });
    });

    it('navigates to /curate when "Select your top projects" is clicked', async () => {
      curationAPI.getShowcase.mockResolvedValue([]);
      renderDashboard();

      await waitFor(() => {
        const btn = screen.getByText(/Select your top projects/i);
        btn.click();
      });

      expect(mockNavigate).toHaveBeenCalledWith('/curate');
    });
  });

  // ---------- Error Handling ----------

  describe('Showcase error handling', () => {
    it('handles API error gracefully and shows empty state', async () => {
      curationAPI.getShowcase.mockRejectedValue(new Error('Network error'));
      renderDashboard();

      await waitFor(() => {
        expect(
          screen.getByText(/No showcase projects selected yet/i)
        ).toBeInTheDocument();
      });
    });

    it('handles non-array API response gracefully', async () => {
      curationAPI.getShowcase.mockResolvedValue({ error: 'unexpected' });
      renderDashboard();

      await waitFor(() => {
        expect(
          screen.getByText(/No showcase projects selected yet/i)
        ).toBeInTheDocument();
      });
    });
  });

  // ---------- Quick Actions (existing) ----------

  describe('Quick Actions are still present', () => {
    it('renders all 4 quick action cards', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(screen.getByText('Upload Project')).toBeInTheDocument();
        expect(screen.getByText('View Projects')).toBeInTheDocument();
        expect(screen.getByText('Generate Portfolio')).toBeInTheDocument();
        expect(screen.getByText('Generate Resume')).toBeInTheDocument();
      });
    });
  });

  // ---------- curationAPI.getShowcase is called ----------

  describe('API calls', () => {
    it('calls curationAPI.getShowcase on mount', async () => {
      renderDashboard();

      await waitFor(() => {
        expect(curationAPI.getShowcase).toHaveBeenCalledTimes(1);
      });
    });
  });
});
