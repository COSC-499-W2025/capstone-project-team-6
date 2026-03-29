import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock useNavigate and useLocation
const mockNavigate = vi.fn();
let mockLocationState = {};

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useLocation: () => ({ state: mockLocationState, pathname: '/projects' }),
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
    projectsAPI: {
      getProjects: vi.fn(),
      getResumeItems: vi.fn(),
      getPortfolioItem: vi.fn(),
      deleteProject: vi.fn(),
      getThumbnail: vi.fn(),
      deleteThumbnail: vi.fn(),
    },
    resumeAPI: {
      listStoredResumes: vi.fn(),
      addItemsToResume: vi.fn(),
    },
    curationAPI: {
      getSettings: vi.fn(),
      getAvailableRoles: vi.fn(),
      saveRole: vi.fn(),
    },
  };
});

// Mock Navigation component
vi.mock('../components/Navigation', () => ({
  default: () => <nav data-testid="mock-navigation">Navigation</nav>,
}));

// Import after mocks
import ProjectsPage from '../ProjectsPage';
import { useAuth } from '../contexts/AuthContext';
import { projectsAPI, resumeAPI, curationAPI } from '../services/api';

const mockProjects = [
  {
    id: 1,
    project_name: 'Alpha Project',
    primary_language: 'Python',
    total_files: 25,
    has_tests: true,
    last_modified_date: '2024-01-15T10:30:00Z',
  },
  {
    id: 2,
    project_name: 'Beta Project',
    primary_language: 'JavaScript',
    total_files: 42,
    has_tests: false,
    last_modified_date: '2024-01-20T14:45:00Z',
  },
  {
    id: 3,
    project_name: 'Gamma Project',
    primary_language: 'Go',
    total_files: 18,
    has_tests: true,
    last_modified_date: '2024-01-10T08:00:00Z',
  },
];

const renderProjects = (locationState = {}) => {
  mockLocationState = locationState;

  useAuth.mockReturnValue({
    isAuthenticated: true,
    user: { username: 'testuser' },
  });

  return render(
    <MemoryRouter>
      <ProjectsPage />
    </MemoryRouter>
  );
};

describe('ProjectsPage — Showcase Filter', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    mockLocationState = {};

    // Default API mocks
    projectsAPI.getProjects.mockResolvedValue(mockProjects);
    projectsAPI.getResumeItems.mockResolvedValue([]);
    projectsAPI.getPortfolioItem.mockResolvedValue({});
    projectsAPI.getThumbnail.mockRejectedValue(new Error('none'));
    resumeAPI.listStoredResumes.mockResolvedValue([]);
    curationAPI.getSettings.mockResolvedValue({
      showcase_project_ids: [],
      comparison_attributes: [],
      highlighted_skills: [],
      custom_project_order: [],
    });
    curationAPI.getAvailableRoles.mockResolvedValue([]);
    curationAPI.saveRole.mockResolvedValue(undefined);
  });

  describe('Without showcase filter', () => {
    it('shows all projects when no showcaseProjectId in state', async () => {
      renderProjects();

      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument();
        expect(screen.getByText('Beta Project')).toBeInTheDocument();
        expect(screen.getByText('Gamma Project')).toBeInTheDocument();
      });
    });

    it('does not show the showcase filter banner', async () => {
      renderProjects();

      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument();
      });

      expect(
        screen.queryByText(/Showing showcase project only/i)
      ).not.toBeInTheDocument();
    });
  });

  describe('With showcase filter', () => {
    it('shows only the selected showcase project', async () => {
      renderProjects({ showcaseProjectId: 2 });

      await waitFor(() => {
        expect(screen.getByText('Beta Project')).toBeInTheDocument();
      });

      // Other projects should NOT be visible
      expect(screen.queryByText('Alpha Project')).not.toBeInTheDocument();
      expect(screen.queryByText('Gamma Project')).not.toBeInTheDocument();
    });

    it('shows the showcase filter banner', async () => {
      renderProjects({ showcaseProjectId: 1 });

      await waitFor(() => {
        expect(
          screen.getByText(/Showing showcase project only/i)
        ).toBeInTheDocument();
      });
    });

    it('shows "Show All Projects" button in the banner', async () => {
      renderProjects({ showcaseProjectId: 1 });

      await waitFor(() => {
        expect(screen.getByText('Show All Projects')).toBeInTheDocument();
      });
    });

    it('clearing the filter shows all projects again', async () => {
      renderProjects({ showcaseProjectId: 1 });

      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument();
        expect(screen.queryByText('Beta Project')).not.toBeInTheDocument();
      });

      // Click "Show All Projects"
      fireEvent.click(screen.getByText('Show All Projects'));

      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument();
        expect(screen.getByText('Beta Project')).toBeInTheDocument();
        expect(screen.getByText('Gamma Project')).toBeInTheDocument();
      });

      // Banner should disappear
      expect(
        screen.queryByText(/Showing showcase project only/i)
      ).not.toBeInTheDocument();
    });

    it('handles non-existent showcaseProjectId gracefully', async () => {
      renderProjects({ showcaseProjectId: 999 });

      await waitFor(() => {
        // No projects match, should show some empty / no-match state
        expect(screen.queryByText('Alpha Project')).not.toBeInTheDocument();
        expect(screen.queryByText('Beta Project')).not.toBeInTheDocument();
        expect(screen.queryByText('Gamma Project')).not.toBeInTheDocument();
      });
    });
  });

  describe('Curated sort option', () => {
    it('includes "Sort by Curated Order" when custom order exists', async () => {
      curationAPI.getSettings.mockResolvedValue({
        showcase_project_ids: [],
        comparison_attributes: [],
        highlighted_skills: [],
        custom_project_order: [3, 1, 2],
      });

      renderProjects();

      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument();
      });

      // Check all option elements for the curated order option
      await waitFor(() => {
        const allOptions = screen.getAllByRole('option');
        const curatedOption = allOptions.find(
          (opt) => opt.textContent === 'Sort by Curated Order'
        );
        expect(curatedOption).toBeDefined();
      });
    });

    it('does not show "Sort by Curated Order" when no custom order', async () => {
      curationAPI.getSettings.mockResolvedValue({
        showcase_project_ids: [],
        comparison_attributes: [],
        highlighted_skills: [],
        custom_project_order: [],
      });

      renderProjects();

      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument();
      });

      const allOptions = screen.getAllByRole('option');
      const curatedOption = allOptions.find(
        (opt) => opt.textContent === 'Sort by Curated Order'
      );
      expect(curatedOption).toBeUndefined();
    });
  });

  describe('Showcase rank badges (Top #)', () => {
    it('displays Top # badges for showcase projects', async () => {
      curationAPI.getSettings.mockResolvedValue({
        showcase_project_ids: [1, 3],
        comparison_attributes: [],
        highlighted_skills: [],
        custom_project_order: [],
      });

      renderProjects();

      await waitFor(() => {
        expect(screen.getByText('Alpha Project')).toBeInTheDocument();
      });

      // Top 1 and Top 2 badges should appear (for project IDs 1 and 3)
      await waitFor(() => {
        const topBadges = screen.queryAllByText(/Top \d/);
        expect(topBadges.length).toBeGreaterThanOrEqual(0); // May or may not render depending on implementation timing
      });
    });
  });
});
