import { render, screen, waitFor } from '@testing-library/react';
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
    },
  };
});

import Portfolio from '../../pages/Portfolio';
import { useAuth } from '../../contexts/AuthContext';
import { portfoliosAPI } from '../../services/api';

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
  },
  {
    analysis_uuid: 'run-2',
    zip_file: 'analysis-two.zip',
    analysis_timestamp: '2026-02-02T11:30:00Z',
    total_projects: 1,
    analysis_type: 'non_llm',
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
};

describe('Portfolio page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();
  });

  it('redirects to login when not authenticated', async () => {
    renderWithAuth(false);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    });
  });

  it('shows loading state while fetching portfolios', () => {
    portfoliosAPI.listPortfolios.mockImplementation(() => new Promise(() => {}));

    renderWithAuth();

    expect(screen.getByText('Loading portfolios...')).toBeInTheDocument();
  });

  it('shows error message when portfolio list fails', async () => {
    const errorMessage = 'Unable to reach API';
    portfoliosAPI.listPortfolios.mockRejectedValue({ response: { data: { detail: errorMessage } } });

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText(errorMessage)).toBeInTheDocument();
    });
  });

  it('displays summary, skills, and projects once data is available', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail.mockResolvedValue(mockDetailFirst);

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText('Summary of run 1')).toBeInTheDocument();
      expect(screen.getByText('Python')).toBeInTheDocument();
      expect(screen.getByText('Alpha')).toBeInTheDocument();
    });
  });

  it('loads detail for another portfolio when selected', async () => {
    portfoliosAPI.listPortfolios.mockResolvedValue(mockPortfolioList);
    portfoliosAPI.getPortfolioDetail
      .mockResolvedValueOnce(mockDetailFirst)
      .mockResolvedValueOnce(mockDetailSecond);

    renderWithAuth();

    await waitFor(() => {
      expect(screen.getByText('Summary of run 1')).toBeInTheDocument();
    });

    const secondCard = screen.getByTestId('portfolio-card-run-2');
    secondCard.click();

    await waitFor(() => {
      expect(screen.getByText('Summary of run 2')).toBeInTheDocument();
    });

    expect(portfoliosAPI.getPortfolioDetail).toHaveBeenCalledWith('run-2');
  });
});
