import { render, screen, waitFor, fireEvent } from '@testing-library/react';
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
    useLocation: () => ({ state: null }),
  };
});

// Mock the AuthContext module
vi.mock('../contexts/AuthContext', () => {
  return {
    useAuth: vi.fn(),
  };
});

// Mock the API module
vi.mock('../services/api', () => {
  return {
    curationAPI: {
      getSettings: vi.fn(),
      getProjects: vi.fn(),
      getShowcase: vi.fn(),
      getSkills: vi.fn(),
      getAttributes: vi.fn(),
      saveShowcase: vi.fn(),
      saveAttributes: vi.fn(),
      saveSkills: vi.fn(),
      saveChronology: vi.fn(),
    },
  };
});

// Import after all mocks are set up
import CuratePage from '../pages/CuratePage';
import { useAuth } from '../contexts/AuthContext';
import { curationAPI } from '../services/api';

// Helper to render with auth context and router
const renderWithAuth = (isAuthenticated = true, user = { id: 1, email: 'test@example.com' }) => {
  useAuth.mockReturnValue({ isAuthenticated, user });
  
  return render(
    <BrowserRouter>
      <CuratePage />
    </BrowserRouter>
  );
};

describe('CuratePage', () => {
  const mockProjects = [
    {
      id: 1,
      project_name: 'Project A',
      primary_language: 'Python',
      total_files: 25,
      has_tests: true,
    },
    {
      id: 2,
      project_name: 'Project B',
      primary_language: 'JavaScript',
      total_files: 35,
      has_tests: false,
    },
    {
      id: 3,
      project_name: 'Project C',
      primary_language: 'Python',
      total_files: 15,
      has_tests: true,
    },
  ];

  const mockSettings = {
    comparison_attributes: ['total_files', 'has_tests', 'primary_language'],
    showcase_project_ids: [1],
    custom_project_order: [],
    highlighted_skills: ['Python', 'JavaScript'],
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    // Default mock implementations
    curationAPI.getProjects.mockResolvedValue(mockProjects);
    curationAPI.getSettings.mockResolvedValue(mockSettings);
    curationAPI.getShowcase.mockResolvedValue([1]);
    curationAPI.getSkills.mockResolvedValue(['Python', 'JavaScript']);
    curationAPI.getAttributes.mockResolvedValue([
      { key: 'total_files', description: 'Total Files', is_default: true },
      { key: 'has_tests', description: 'Has Tests', is_default: true },
      { key: 'primary_language', description: 'Primary Language', is_default: true },
    ]);
    curationAPI.saveShowcase.mockResolvedValue({ success: true });
    curationAPI.saveAttributes.mockResolvedValue({ success: true });
    curationAPI.saveSkills.mockResolvedValue({ success: true });
    curationAPI.saveChronology.mockResolvedValue({ success: true });
  });

  describe('Page Rendering', () => {
    it('renders the page title', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('Curate Your Portfolio')).toBeInTheDocument();
      });
    });

    it('renders navigation with dashboard link', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('Dashboard')).toBeInTheDocument();
      });
    });

    it('loads user projects on mount', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(curationAPI.getProjects).toHaveBeenCalled();
      });
    });

    it('loads curation settings on mount', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(curationAPI.getSettings).toHaveBeenCalled();
      });
    });
  });

  describe('Tab Navigation', () => {
    it('renders all available curation tabs', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('Showcase (Top 3)')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Project Comparison Fields' })).toBeInTheDocument();
        expect(screen.getByText('Highlighted Skills')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: 'Chronology Correction' })).toBeInTheDocument();
      });
    });

    it('defaults to showcase tab', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText(/Select Top 3 Showcase Projects/i)).toBeInTheDocument();
      });
    });

    it('switches to attributes tab when clicked', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const attributesTab = screen.getByRole('button', { name: 'Project Comparison Fields' });
        fireEvent.click(attributesTab);
      });

      await waitFor(() => {
        expect(screen.getByText('Select Project Comparison Fields')).toBeInTheDocument();
      });
    });

    it('switches to skills tab when clicked', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const skillsTab = screen.getByText('Highlighted Skills');
        fireEvent.click(skillsTab);
      });

      await waitFor(() => {
        expect(screen.getByText('Highlight Skills (Max 10)')).toBeInTheDocument();
      });
    });

    it('switches to chronology tab when clicked', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const chronologyTab = screen.getByRole('button', { name: 'Chronology Correction' });
        fireEvent.click(chronologyTab);
      });

      await waitFor(() => {
        expect(screen.getByText('Correct Project Dates')).toBeInTheDocument();
      });
    });

  });

  describe('Showcase Tab', () => {
    it('displays projects for selection', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('Project A')).toBeInTheDocument();
        expect(screen.getByText('Project B')).toBeInTheDocument();
        expect(screen.getByText('Project C')).toBeInTheDocument();
      });
    });

    it('shows selected count', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText(/Selected: \d\/3/)).toBeInTheDocument();
      });
    });

    it('displays save button', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText('Save Showcase Projects')).toBeInTheDocument();
      });
    });

    it('calls save API when save button is clicked', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const saveButton = screen.getByText('Save Showcase Projects');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(curationAPI.saveShowcase).toHaveBeenCalled();
      });
    });

    it('shows success message after successful save', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const saveButton = screen.getByText('Save Showcase Projects');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/saved successfully/i)).toBeInTheDocument();
      });
    });

    it('shows error message when save fails', async () => {
      curationAPI.saveShowcase.mockRejectedValue(new Error('Save failed'));
      renderWithAuth();
      
      await waitFor(() => {
        const saveButton = screen.getByText('Save Showcase Projects');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(screen.getByText(/Save failed/i)).toBeInTheDocument();
      });
    });
  });

  describe('Attributes Tab', () => {
    it('displays attribute options', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const attributesTab = screen.getByRole('button', { name: 'Project Comparison Fields' });
        fireEvent.click(attributesTab);
      });

      await waitFor(() => {
        // Just check the tab content is shown
        expect(screen.getByText('Select Project Comparison Fields')).toBeInTheDocument();
      });
    });

    it('displays save button', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const attributesTab = screen.getByRole('button', { name: 'Project Comparison Fields' });
        fireEvent.click(attributesTab);
      });

      await waitFor(() => {
        expect(screen.getByText('Save Attributes')).toBeInTheDocument();
      });
    });

    it('calls save API when save button is clicked', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const attributesTab = screen.getByRole('button', { name: 'Project Comparison Fields' });
        fireEvent.click(attributesTab);
      });

      await waitFor(() => {
        const saveButton = screen.getByText('Save Attributes');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(curationAPI.saveAttributes).toHaveBeenCalled();
      });
    });
  });

  describe('Skills Tab', () => {
    it('displays skill toggle buttons', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const skillsTab = screen.getByText('Highlighted Skills');
        fireEvent.click(skillsTab);
      });

      await waitFor(() => {
        // Skills are displayed as toggle buttons, not an input field
        expect(screen.getByText('Python')).toBeInTheDocument();
        expect(screen.getByText('JavaScript')).toBeInTheDocument();
      });
    });

    it('displays current skills count', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const skillsTab = screen.getByText('Highlighted Skills');
        fireEvent.click(skillsTab);
      });

      await waitFor(() => {
        expect(screen.getByText(/Selected: \d+\/10/)).toBeInTheDocument();
      });
    });

    it('displays save button', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const skillsTab = screen.getByText('Highlighted Skills');
        fireEvent.click(skillsTab);
      });

      await waitFor(() => {
        expect(screen.getByText('Save Highlighted Skills')).toBeInTheDocument();
      });
    });

    it('calls save API when save button is clicked', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const skillsTab = screen.getByText('Highlighted Skills');
        fireEvent.click(skillsTab);
      });

      await waitFor(() => {
        const saveButton = screen.getByText('Save Highlighted Skills');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(curationAPI.saveSkills).toHaveBeenCalled();
      });
    });
  });

  describe('Chronology Tab', () => {
    it('displays projects for chronology correction', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const chronologyTab = screen.getByRole('button', { name: 'Chronology Correction' });
        fireEvent.click(chronologyTab);
      });

      await waitFor(() => {
        expect(screen.getAllByText(/Project [ABC]/).length).toBeGreaterThan(0);
      });
    });

    it('displays save button after editing dates', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const chronologyTab = screen.getByRole('button', { name: 'Chronology Correction' });
        fireEvent.click(chronologyTab);
      });

      await waitFor(() => {
        const dateInputs = screen.getAllByLabelText(/Last Commit Date/i);
        expect(dateInputs.length).toBeGreaterThan(0);
        // Trigger a change to make save button appear
        fireEvent.change(dateInputs[0], { target: { value: '2024-01-01' } });
      });

      await waitFor(() => {
        expect(screen.getByText('Save Dates')).toBeInTheDocument();
      });
    });

    it('calls save API when save button is clicked', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const chronologyTab = screen.getByRole('button', { name: 'Chronology Correction' });
        fireEvent.click(chronologyTab);
      });

      await waitFor(() => {
        const dateInputs = screen.getAllByLabelText(/Last Commit Date/i);
        fireEvent.change(dateInputs[0], { target: { value: '2024-01-01' } });
      });

      await waitFor(() => {
        const saveButton = screen.getByText('Save Dates');
        fireEvent.click(saveButton);
      });

      await waitFor(() => {
        expect(curationAPI.saveChronology).toHaveBeenCalled();
      });
    });
  });

  describe('Error Handling', () => {
    it('shows error message when projects fail to load', async () => {
      curationAPI.getProjects.mockRejectedValue(new Error('Failed to load'));
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });

    it('shows error message when settings fail to load', async () => {
      curationAPI.getSettings.mockRejectedValue(new Error('Failed to load'));
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.getByText(/failed to load/i)).toBeInTheDocument();
      });
    });
  });

  describe('Loading States', () => {
    it('shows loading state while fetching data', async () => {
      curationAPI.getProjects.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
      renderWithAuth();
      
      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });

    it('hides loading state after data is loaded', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('Navigation', () => {
    it('navigates to dashboard when dashboard button is clicked', async () => {
      renderWithAuth();
      
      await waitFor(() => {
        const dashboardButton = screen.getByText('Dashboard');
        fireEvent.click(dashboardButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });
});
