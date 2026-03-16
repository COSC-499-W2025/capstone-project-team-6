import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Mocks
// ---------------------------------------------------------------------------

vi.mock('../components/Navigation', () => ({
  default: () => <div data-testid="nav">Navigation</div>,
}));

vi.mock('../services/api', () => ({
  projectsAPI: {
    getProjects: vi.fn(),
  },
  resumeAPI: {
    generateResume: vi.fn(),
    listStoredResumes: vi.fn(),
    getPersonalInfo: vi.fn(),
    createStoredResume: vi.fn(),
    updateStoredResume: vi.fn(),
    getStoredResume: vi.fn(),
  },
  curationAPI: {
    getSettings: vi.fn(),
    getProjects: vi.fn(),
  },
}));

vi.mock('react-markdown', () => ({
  default: ({ children }) => <div data-testid="markdown">{children}</div>,
}));
vi.mock('remark-gfm', () => ({ default: () => {} }));

// Import after mocks
import Resume from '../pages/Resume';
import { projectsAPI, resumeAPI, curationAPI } from '../services/api';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const MOCK_PROJECTS = [
  { id: 1, project_name: 'CapstoneApp', primary_language: 'Python', total_files: 10 },
  { id: 2, project_name: 'FrontendUI', primary_language: 'TypeScript', total_files: 20 },
  { id: 3, project_name: 'DataPipeline', primary_language: 'Java', total_files: 8 },
];

const MOCK_CURATION_SETTINGS = {
  showcase_project_ids: [],
  custom_project_order: [],
  highlighted_skills: [],
};

const MOCK_SHOWCASE_CURATION_SETTINGS = {
  showcase_project_ids: [1, 3],
  custom_project_order: [],
  highlighted_skills: [],
};

const MOCK_VALID_PERSONAL_INFO = {
  name: 'Jane Doe',
  email: 'jane@example.com',
  phone: '5551234567',
  location: '',
  linkedIn: '',
  github: '',
  website: '',
};

function setupDefaultMocks() {
  projectsAPI.getProjects.mockResolvedValue(MOCK_PROJECTS);
  resumeAPI.listStoredResumes.mockResolvedValue([]);
  resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: MOCK_VALID_PERSONAL_INFO });
  curationAPI.getSettings.mockResolvedValue(MOCK_CURATION_SETTINGS);
  curationAPI.getProjects.mockResolvedValue([]);
}

function setupShowcaseMocks() {
  projectsAPI.getProjects.mockResolvedValue(MOCK_PROJECTS);
  resumeAPI.listStoredResumes.mockResolvedValue([]);
  resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: MOCK_VALID_PERSONAL_INFO });
  curationAPI.getSettings.mockResolvedValue(MOCK_SHOWCASE_CURATION_SETTINGS);
  curationAPI.getProjects.mockResolvedValue([]);
}

const renderResume = () =>
  render(
    <BrowserRouter>
      <Resume />
    </BrowserRouter>
  );

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Resume Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Initial render', () => {
    it('renders the page heading', async () => {
      setupDefaultMocks();
      renderResume();

      expect(await screen.findByText('Resume Generator')).toBeInTheDocument();
    });

    it('renders the Generate Resume button', async () => {
      setupDefaultMocks();
      renderResume();

      expect(await screen.findByRole('button', { name: /generate resume/i })).toBeInTheDocument();
    });

    it('loads and displays projects', async () => {
      setupDefaultMocks();
      renderResume();

      expect(await screen.findByText('CapstoneApp')).toBeInTheDocument();
      expect(await screen.findByText('FrontendUI')).toBeInTheDocument();
      expect(await screen.findByText('DataPipeline')).toBeInTheDocument();
    });

    it('shows "No projects found" when project list is empty', async () => {
      projectsAPI.getProjects.mockResolvedValue([]);
      resumeAPI.listStoredResumes.mockResolvedValue([]);
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });
      curationAPI.getSettings.mockResolvedValue(MOCK_CURATION_SETTINGS);
      curationAPI.getProjects.mockResolvedValue([]);

      renderResume();

      expect(await screen.findByText(/no projects found/i)).toBeInTheDocument();
    });
  });

  describe('Generate button state', () => {
    it('is disabled when no projects are selected', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');
      const btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).toBeDisabled();
    });

    it('becomes enabled after selecting a project', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      const checkbox = screen.getByLabelText(/frontendui/i);
      fireEvent.click(checkbox);

      const btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).not.toBeDisabled();
    });
  });

  describe('Resume generation — success path', () => {
    it('calls generateResume with project ids', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockResolvedValue({
        resume_id: 'abc-123',
        format: 'markdown',
        content: '# Jane Doe\n\n## Projects\n\n**CapstoneApp** | *Python*\n',
        metadata: { project_count: 1, total_projects: 1, generated_at: new Date().toISOString() },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/capstoneapp/i));
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(resumeAPI.generateResume).toHaveBeenCalledOnce();
      });

      const [calledIds] = resumeAPI.generateResume.mock.calls[0];
      expect(Array.isArray(calledIds)).toBe(true);
      expect(calledIds).toContain(1);
      expect(typeof calledIds[0]).toBe('number');
    });

    it('renders the generated resume content', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockResolvedValue({
        resume_id: 'abc-123',
        format: 'markdown',
        content: '# Jane Doe\n\n## Projects\n\n**CapstoneApp** | *Python*\n',
        metadata: { project_count: 1, total_projects: 1, generated_at: new Date().toISOString() },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/capstoneapp/i));
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByTestId('markdown')).toBeInTheDocument();
      });
    });

    it('shows "Generating..." while the request is in flight', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockImplementation(() => new Promise(() => {}));

      renderResume();
      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/capstoneapp/i));
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /generating\.\.\./i })).toBeInTheDocument();
      });
    });
  });

  describe('Resume generation — error path', () => {
    it('shows API detail error message when generation fails', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockRejectedValue({
        response: { data: { detail: 'No valid projects found for the provided IDs' } },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/capstoneapp/i));
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByText(/no valid projects found for the provided ids/i)).toBeInTheDocument();
      });
    });

    it('shows fallback error message when API returns no detail', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockRejectedValue(new Error('Network Error'));

      renderResume();
      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/capstoneapp/i));
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByText(/failed to generate resume/i)).toBeInTheDocument();
      });
    });

    it('re-enables the Generate button after an API error', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockRejectedValue(new Error('fail'));

      renderResume();
      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/capstoneapp/i));
      const btn = screen.getByRole('button', { name: /generate resume/i });
      fireEvent.click(btn);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /generate resume/i })).not.toBeDisabled();
      });
    });
  });

  describe('Project selection actions', () => {
    it('selects all projects when "Select All" is clicked', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');
      fireEvent.click(screen.getByRole('button', { name: /^select all$/i }));

      const btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).not.toBeDisabled();
    });

    it('clears all selections when "Clear Selection" is clicked', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');
      fireEvent.click(screen.getByRole('button', { name: /^select all$/i }));

      let btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).not.toBeDisabled();

      fireEvent.click(screen.getByRole('button', { name: /clear selection/i }));

      btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).toBeDisabled();
    });
  });

  describe('Showcase project quick selection', () => {
    it('preselects showcase projects on load when showcase ids exist', async () => {
      setupShowcaseMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      const btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).not.toBeDisabled();
    });

    it('selects only showcase projects when "Select Showcase Projects" is clicked', async () => {
      setupShowcaseMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByRole('button', { name: /clear selection/i }));
      expect(screen.getByRole('button', { name: /generate resume/i })).toBeDisabled();

      fireEvent.click(screen.getByRole('button', { name: /select showcase projects/i }));

      expect(screen.getByRole('button', { name: /generate resume/i })).not.toBeDisabled();
    });

    it('disables showcase button when no showcase projects exist', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      expect(screen.getByRole('button', { name: /select showcase projects/i })).toBeDisabled();
    });

    it('shows only showcase projects when "Show showcase projects only" is checked', async () => {
      setupShowcaseMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/show showcase projects only/i));

      expect(screen.getByText('CapstoneApp')).toBeInTheDocument();
      expect(screen.getByText('DataPipeline')).toBeInTheDocument();
      expect(screen.queryByText('FrontendUI')).not.toBeInTheDocument();
    });

    it('shows empty showcase message when showcase filter is on and no showcase projects exist', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/show showcase projects only/i));

      expect(screen.getByText(/no showcase projects selected in curation yet/i)).toBeInTheDocument();
    });
  });
});