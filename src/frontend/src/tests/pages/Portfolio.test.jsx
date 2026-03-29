import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, expect, it, vi, beforeEach } from 'vitest';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../../contexts/AuthContext', () => {
  return {
    useAuth: vi.fn(),
  };
});

vi.mock('../../services/api', () => {
  return {
    portfoliosAPI: {
      listPortfolios: vi.fn(),
      getPortfolioDetail: vi.fn(),
      getPortfolioSettings: vi.fn(),
      savePortfolioSettings: vi.fn(),
      deletePortfolio: vi.fn(),
    },
    curationAPI: {
      getSettings: vi.fn().mockResolvedValue({}),
    },
  };
});

import Portfolio from '../../pages/Portfolio';
import { useAuth } from '../../contexts/AuthContext';
import { portfoliosAPI, curationAPI } from '../../services/api';

const renderWithAuth = (isAuthenticated = true) => {
  useAuth.mockReturnValue({
    isAuthenticated,
    user: { username: 'test-user' },
  });

  return render(
    <BrowserRouter>
      <Portfolio />
    </BrowserRouter>
  );
};

const mockPortfolioList = [
  {
    analysis_uuid: 'run-1',
    zip_file: 'analysis-one.zip',
    analysis_timestamp: '2026-01-01T08:00:00Z',
    total_projects: 2,
    analysis_type: 'llm',
    project_names: ['Alpha'],
  },
  {
    analysis_uuid: 'run-2',
    zip_file: 'analysis-two.zip',
    analysis_timestamp: '2026-02-02T11:30:00Z',
    total_projects: 1,
    analysis_type: 'non_llm',
    project_names: ['Beta'],
  },
];

const mockDetailFirst = {
  analysis_uuid: 'run-1',
  analysis_type: 'llm',
  zip_file: 'analysis-one.zip',
  analysis_timestamp: '2026-01-01T08:00:00Z',
  total_projects: 2,
  summary: {
    text_summary: 'Summary of run 1',
  },
  skills: [
    { skill: 'Python', count: 3 },
    { skill: 'Testing', count: 1 },
  ],
  projects: [
    {
      project_name: 'Alpha',
      primary_language: 'Python',
      total_files: 10,
      summary: 'Alpha summary',
    },
  ],
  portfolio_items: [
    {
      title: 'Alpha highlight',
      project_name: 'Alpha',
      text_summary: 'A Python backend project with strong code quality signals.',
      tech_stack: ['Python', 'FastAPI'],
      skills_exercised: ['API design', 'Testing'],
      quality_score: 45,
      sophistication_level: 'intermediate',
    },
  ],
};

const mockDetailSecond = {
  analysis_uuid: 'run-2',
  analysis_type: 'non_llm',
  zip_file: 'analysis-two.zip',
  analysis_timestamp: '2026-02-02T11:30:00Z',
  total_projects: 1,
  summary: {
    analysis_summary: 'Summary of run 2',
  },
  skills: [{ skill: 'JavaScript', count: 2 }],
  projects: [
    {
      project_name: 'Beta',
      primary_language: 'JavaScript',
      total_files: 5,
      summary: 'Beta summary',
    },
  ],
  items: [
    {
      project_name: 'Beta',
      text_summary: 'A JavaScript project with nested stats output shape.',
      tech_stack: ['JavaScript'],
      skills_exercised: ['Frontend development'],
      project_statistics: {
        quality_score: 38,
        sophistication_level: 'intermediate',
      },
    },
  ],
};

describe('Portfolio page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
    portfoliosAPI.listPortfolios.mockResolvedValue([]);
    portfoliosAPI.getPortfolioDetail.mockResolvedValue({});
    portfoliosAPI.getPortfolioSettings.mockResolvedValue({});
    portfoliosAPI.savePortfolioSettings.mockResolvedValue({});
    portfoliosAPI.deletePortfolio.mockResolvedValue({});
    curationAPI.getSettings.mockResolvedValue({});
  });

  it('redirects to login when not authenticated', async () => {
    renderWithAuth(false);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('shows loading state while fetching portfolios', async () => {
    portfoliosAPI.listPortfolios.mockImplementation(() => new Promise(() => {}));
    curationAPI.getSettings.mockImplementation(() => new Promise(() => {}));

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText('Loading portfolios...')).toBeInTheDocument();
    });
  });

  it('shows error message when portfolio list fails', async () => {
    const errorMessage = 'Unable to reach API';
    portfoliosAPI.listPortfolios.mockRejectedValue({ response: { data: { detail: errorMessage } } });

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('displays skills and projects once data is available', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail.mockResolvedValue(mockDetailFirst);

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText('Alpha highlight')).toBeInTheDocument();
      expect(screen.getAllByText(/Python/).length).toBeGreaterThan(0);
      expect(screen.getAllByText('Alpha').length).toBeGreaterThan(0);
      expect(screen.getByText(/Quality score: 45/)).toBeInTheDocument();
      expect(screen.getByText(/Sophistication: intermediate/)).toBeInTheDocument();
    });
  });

  it('does not render the summary section', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail.mockResolvedValue(mockDetailFirst);

    renderWithAuth();

    await waitFor(() => {
      expect(screen.queryByText('Summary')).not.toBeInTheDocument();
      expect(screen.queryByText('Summary of run 1')).not.toBeInTheDocument();
    });
  });

  it('derives highlighted skills from portfolio items when skills list is empty', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail.mockResolvedValue({
      ...mockDetailFirst,
      skills: [],
      portfolio_items: [
        {
          project_name: 'Alpha',
          text_summary: 'Skill fallback test',
          skills_exercised: ['Backend APIs', 'Testing', 'Backend APIs'],
        },
      ],
    });

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText('Skill fallback test')).toBeInTheDocument();
      expect(screen.getAllByText(/Backend APIs/).length).toBeGreaterThan(0);
      expect(screen.getAllByText(/Testing/).length).toBeGreaterThan(0);
    });
  });

  it('shows project names in available analyses cards', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail.mockResolvedValue(mockDetailFirst);

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText('Alpha')).toBeInTheDocument();
      expect(screen.getByText('Beta')).toBeInTheDocument();
    });
  });

  it('loads detail for another portfolio when selected', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail.mockImplementation((uuid) => {
      if (uuid === 'run-1') return Promise.resolve(mockDetailFirst);
      if (uuid === 'run-2') return Promise.resolve(mockDetailSecond);
      return Promise.reject(new Error(`Unknown uuid: ${uuid}`));
    });

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText('Alpha highlight')).toBeInTheDocument();
    });

    const secondCard = screen.getByTestId('portfolio-card-run-2');
    fireEvent.click(secondCard);

    await waitFor(() => {
      expect(screen.getByText('A JavaScript project with nested stats output shape.')).toBeInTheDocument();
      expect(screen.getByText(/Quality score: 38/)).toBeInTheDocument();
      expect(screen.getByText(/Sophistication: intermediate/)).toBeInTheDocument();
    });

    expect(portfoliosAPI.getPortfolioDetail).toHaveBeenCalledWith('run-2');
  });

  it('renders portfolio item metadata fields (summary, tech stack, and skills)', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail.mockResolvedValue(mockDetailFirst);

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText('Alpha highlight')).toBeInTheDocument();
      expect(
        screen.getByText('A Python backend project with strong code quality signals.')
      ).toBeInTheDocument();
      expect(screen.getByText('Tech stack: Python, FastAPI')).toBeInTheDocument();
      expect(screen.getByText('Skills: API design, Testing')).toBeInTheDocument();
    });
  });

  it('shows empty state when no portfolio items are returned', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail.mockResolvedValue({
      ...mockDetailFirst,
      portfolio_items: [],
      items: [],
    });

    renderWithAuth();

    await waitFor(() => {
      expect(
        screen.getByText('No portfolio items were returned by the backend yet.')
      ).toBeInTheDocument();
    });
  });
});
