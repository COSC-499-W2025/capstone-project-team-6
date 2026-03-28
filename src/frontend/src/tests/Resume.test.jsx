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
    listEducation: vi.fn().mockResolvedValue([]),
    listWorkExperience: vi.fn().mockResolvedValue([]),
  },
  curationAPI: {
    getSettings: vi.fn(),
    getProjects: vi.fn(),
  },
}));

// react-markdown and remark-gfm are heavy; replace with a plain renderer
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
  education: '',
  education_university: '',
  education_location: '',
  education_degree: '',
  education_start_date: '',
  education_end_date: '',
  education_awards: '',
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

      const btn = await screen.findByRole('button', { name: /generate resume/i });
      await screen.findByText('CapstoneApp');
      expect(btn).toBeDisabled();
    });

    it('becomes enabled after selecting a project', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');
      const checkboxes = screen.getAllByRole('checkbox');
      // Index 0: educationEndCurrent, Index 1: workEndCurrent, Index 2: showShowcaseOnly
      // Index 3: first project (CapstoneApp)
      fireEvent.click(checkboxes[3]);

      const btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).not.toBeDisabled();
    });
  });

  describe('Resume generation — success path', () => {
    it('calls generateResume with project_ids (not portfolio_ids)', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockResolvedValue({
        resume_id: 'abc-123',
        format: 'markdown',
        content: '# Jane Doe\n\n## Projects\n\n**CapstoneApp** | *Python*\n',
        metadata: { project_count: 1, total_projects: 1, generated_at: new Date().toISOString() },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
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

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
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

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /generating\.\.\./i })).toBeInTheDocument();
      });
    });
  });

  describe('Resume generation — error path (Bug: white screen on failure)', () => {
    it('shows an error message instead of crashing when the API fails', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockRejectedValue({
        response: { data: { detail: 'No valid projects found for the provided IDs' } },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/no valid projects found/i);
      });
    });

    it('shows a fallback error message when the API returns no detail', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockRejectedValue(new Error('Network Error'));

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/failed to generate resume/i);
      });
    });

    it('re-enables the Generate button after an API error', async () => {
      setupDefaultMocks();
      resumeAPI.generateResume.mockRejectedValue(new Error('fail'));

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);

      const btn = screen.getByRole('button', { name: /generate resume/i });
      fireEvent.click(btn);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /generate resume/i })).not.toBeDisabled();
      });
    });
  });

  describe('Select All / Deselect All', () => {
    it('selects all projects when "Select All" is clicked', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');
      fireEvent.click(screen.getByRole('button', { name: /select all/i }));

      const btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).not.toBeDisabled();
    });
  });

  describe('Personal info validation', () => {
    it('blocks generate when personal info has invalid email', async () => {
      setupDefaultMocks();
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { ...MOCK_VALID_PERSONAL_INFO, email: 'not-an-email' },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByText(/enter a valid email address/i)).toBeInTheDocument();
      });

      expect(resumeAPI.generateResume).not.toHaveBeenCalled();
    });

    it('blocks generate when phone contains letters', async () => {
      setupDefaultMocks();
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { ...MOCK_VALID_PERSONAL_INFO, phone: '555-abc-1234' },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByText(/phone may only contain digits/i)).toBeInTheDocument();
      });

      expect(resumeAPI.generateResume).not.toHaveBeenCalled();
    });

    it('blocks generate when phone has fewer than 7 digits', async () => {
      setupDefaultMocks();
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { ...MOCK_VALID_PERSONAL_INFO, phone: '123456' },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByText(/minimum of 7 digits required/i)).toBeInTheDocument();
      });

      expect(resumeAPI.generateResume).not.toHaveBeenCalled();
    });

    it('shows error in toast at top when generate fails validation', async () => {
      setupDefaultMocks();
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { ...MOCK_VALID_PERSONAL_INFO, name: '' },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByRole('alert')).toHaveTextContent(/please fix the personal information errors/i);
      });
    });

    it('blocks generate when name is empty', async () => {
      setupDefaultMocks();
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { ...MOCK_VALID_PERSONAL_INFO, name: '' },
      });

      renderResume();
      await screen.findByText('CapstoneApp');

      const checkboxes = screen.getAllByRole('checkbox');
      fireEvent.click(checkboxes[3]);
      fireEvent.click(screen.getByRole('button', { name: /generate resume/i }));

      await waitFor(() => {
        expect(screen.getByText(/full name is required/i)).toBeInTheDocument();
      });

      expect(resumeAPI.generateResume).not.toHaveBeenCalled();
    });
  });

  describe('Personal info Cancel Changes', () => {
    it('Cancel Changes button reverts to loaded values when user has changes', async () => {
      setupDefaultMocks();

      renderResume();
      await screen.findByText('CapstoneApp');

      expect(screen.getByDisplayValue('Jane Doe')).toBeInTheDocument();

      fireEvent.change(screen.getByPlaceholderText('Full Name'), {
        target: { value: 'Jane Smith' },
      });

      expect(screen.getByDisplayValue('Jane Smith')).toBeInTheDocument();

      const cancelBtn = screen.getByRole('button', { name: /cancel changes/i });
      fireEvent.click(cancelBtn);

      await waitFor(() => {
        expect(screen.getByDisplayValue('Jane Doe')).toBeInTheDocument();
      });
    });

    it('Cancel Changes button does not show when no loaded data', async () => {
      projectsAPI.getProjects.mockResolvedValue(MOCK_PROJECTS);
      resumeAPI.listStoredResumes.mockResolvedValue([]);
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });
      curationAPI.getSettings.mockResolvedValue(MOCK_CURATION_SETTINGS);
      curationAPI.getProjects.mockResolvedValue([]);

      renderResume();
      await screen.findByText('CapstoneApp');

      expect(screen.queryByRole('button', { name: /cancel changes/i })).not.toBeInTheDocument();
    });

    it('Cancel Changes button does not show when no changes', async () => {
      setupDefaultMocks();

      renderResume();
      await screen.findByText('CapstoneApp');

      expect(screen.getByDisplayValue('Jane Doe')).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: /cancel changes/i })).not.toBeInTheDocument();
    });
  });

  describe('Showcase project selection', () => {
    it('preselects showcase projects on load when showcase projects exist', async () => {
      setupShowcaseMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      const btn = screen.getByRole('button', { name: /generate resume/i });
      expect(btn).not.toBeDisabled();
    });

    it('selects showcase projects when "Select Showcase Projects" is clicked', async () => {
      setupShowcaseMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByRole('button', { name: /clear selection/i }));
      expect(screen.getByRole('button', { name: /generate resume/i })).toBeDisabled();

      fireEvent.click(screen.getByRole('button', { name: /select showcase projects/i }));

      expect(screen.getByRole('button', { name: /generate resume/i })).not.toBeDisabled();
    });

    it('clears all selected projects when "Clear Selection" is clicked', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByRole('button', { name: /select all/i }));
      expect(screen.getByRole('button', { name: /generate resume/i })).not.toBeDisabled();

      fireEvent.click(screen.getByRole('button', { name: /clear selection/i }));
      expect(screen.getByRole('button', { name: /generate resume/i })).toBeDisabled();
    });

    it('disables "Select Showcase Projects" when there are no showcase projects', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      expect(
        screen.getByRole('button', { name: /select showcase projects/i })
      ).toBeDisabled();
    });

    it('shows only showcase projects when "Show showcase projects only" is enabled', async () => {
      setupShowcaseMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/show showcase projects only/i));

      expect(screen.getByText('CapstoneApp')).toBeInTheDocument();
      expect(screen.getByText('DataPipeline')).toBeInTheDocument();
      expect(screen.queryByText('FrontendUI')).not.toBeInTheDocument();
    });

    it('shows empty message when showcase-only filter is enabled and no showcase projects exist', async () => {
      setupDefaultMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByLabelText(/show showcase projects only/i));

      expect(
        screen.getByText(/no showcase projects selected in curation yet/i)
      ).toBeInTheDocument();
    });

    it('keeps Select Showcase Projects enabled even after selections change when showcase ids exist', async () => {
      setupShowcaseMocks();
      renderResume();

      await screen.findByText('CapstoneApp');

      fireEvent.click(screen.getByRole('button', { name: /clear selection/i }));
      expect(screen.getByRole('button', { name: /select showcase projects/i })).not.toBeDisabled();
    });
  });
});