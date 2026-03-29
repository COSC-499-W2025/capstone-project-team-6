import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('../components/Navigation', () => ({
  default: () => <nav data-testid="mock-navigation">Navigation</nav>,
}));

vi.mock('../services/api', () => ({
  portfoliosAPI: {
    listPublicPortfolios: vi.fn(),
    getPublicPortfolioDetail: vi.fn(),
  },
}));

import PublicPortfolios from '../pages/PublicPortfolios';
import { portfoliosAPI } from '../services/api';

const mockListResponse = {
  items: [
    {
      analysis_uuid: 'public-1',
      username: 'alice',
      analysis_type: 'llm',
      analysis_timestamp: '2026-01-24T10:00:00',
      published_at: '2026-01-25T10:00:00',
      total_projects: 3,
      project_names: ['Alpha', 'Portfolio Service'],
      project_types: ['Backend Developer'],
      top_languages: ['Python', 'TypeScript'],
      top_skills: ['FastAPI', 'Testing'],
      has_tests: true,
    },
  ],
  total: 1,
  page: 1,
  page_size: 12,
};

const mockDetailResponse = {
  analysis_uuid: 'public-1',
  username: 'alice',
  analysis_type: 'llm',
  zip_file: 'alice.zip',
  analysis_timestamp: '2026-01-24T10:00:00',
  published_at: '2026-01-25T10:00:00',
  total_projects: 3,
  projects: [
    { project_name: 'Alpha', primary_language: 'Python', predicted_role: 'Backend Developer' },
    { project_name: 'Portfolio Service', primary_language: 'Python', predicted_role: 'Backend Developer' },
  ],
  skills: [{ skill: 'FastAPI' }, { skill: 'Testing' }],
  summary: {},
  portfolio_items: [],
  portfolio_settings: {},
};

const renderPage = () =>
  render(
    <MemoryRouter>
      <PublicPortfolios />
    </MemoryRouter>
  );

describe('PublicPortfolios page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    portfoliosAPI.listPublicPortfolios.mockResolvedValue(mockListResponse);
    portfoliosAPI.getPublicPortfolioDetail.mockResolvedValue(mockDetailResponse);
  });

  it('shows visibility banner and loads public cards', async () => {
    renderPage();

    expect(
      screen.getByText('Only portfolios marked Public by their owners are shown here.')
    ).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('@alice')).toBeInTheDocument();
      expect(screen.getByText(/3 projects/i)).toBeInTheDocument();
    });
  });

  it('search input triggers list call with q', async () => {
    renderPage();

    await waitFor(() => {
      expect(portfoliosAPI.listPublicPortfolios).toHaveBeenCalled();
    });

    fireEvent.change(screen.getByPlaceholderText('Search users, projects, skills...'), {
      target: { value: 'alice' },
    });

    await waitFor(() => {
      expect(portfoliosAPI.listPublicPortfolios).toHaveBeenLastCalledWith(
        expect.objectContaining({ q: 'alice' })
      );
    });
  });

  it('loads detail panel when a card is selected', async () => {
    renderPage();

    await waitFor(() => {
      expect(screen.getByText('@alice')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('@alice'));

    await waitFor(() => {
      expect(portfoliosAPI.getPublicPortfolioDetail).toHaveBeenCalledWith('public-1');
      expect(screen.getByText('Developer Profile')).toBeInTheDocument();
      expect(screen.getByText('Core Skills')).toBeInTheDocument();
      expect(screen.getByText('FastAPI')).toBeInTheDocument();
      expect(screen.getByText('Portfolio Service')).toBeInTheDocument();
      expect(screen.getByText('Primary Role')).toBeInTheDocument();
      expect(screen.getAllByText('Backend Developer').length).toBeGreaterThan(0);
    });
  });

  it('shows empty state when there are no public portfolios', async () => {
    portfoliosAPI.listPublicPortfolios.mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      page_size: 12,
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('No published portfolios match your filters yet.')).toBeInTheDocument();
    });
  });
});
