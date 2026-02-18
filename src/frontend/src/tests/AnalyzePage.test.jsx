import { render, screen, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

vi.mock('../services/analysisApi', () => ({
  getTaskStatus: vi.fn(),
}));

import AnalyzePage from '../pages/AnalyzePage';
import { useAuth } from '../contexts/AuthContext';
import { getTaskStatus } from '../services/analysisApi';

const renderWithRouter = (state = { taskId: 'test-task-123' }) => {
  return render(
    <MemoryRouter initialEntries={['/analyze']} initialIndex={0}>
      <AnalyzePage state={state} />
    </MemoryRouter>
  );
};

// Need to pass state via location - MemoryRouter doesn't support initial state directly
// We need to use a custom route that provides state
const renderWithState = (taskId = 'test-task-123') => {
  const location = { pathname: '/analyze', state: { taskId } };
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/analyze', state: { taskId } }]}>
      <AnalyzePage />
    </MemoryRouter>
  );
};

describe('AnalyzePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useAuth.mockReturnValue({ user: { token: 'test-token' } });
  });

  describe('Initial state', () => {
    it('shows error when taskId is missing', () => {
      render(
        <MemoryRouter initialEntries={['/analyze']}>
          <AnalyzePage />
        </MemoryRouter>
      );
      expect(screen.getByText(/Missing taskId\. Please go back to Upload/i)).toBeInTheDocument();
    });

    it('shows error when auth token is missing', () => {
      useAuth.mockReturnValue({ user: null });
      renderWithState();
      expect(screen.getByText(/Missing auth token/i)).toBeInTheDocument();
    });
  });

  describe('With taskId from navigation', () => {
    it('displays task info and starts polling', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      renderWithState('task-abc-123');

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalledWith('task-abc-123', 'test-token');
      });
      expect(screen.getAllByText(/Task: task-abc-123/).length).toBeGreaterThan(0);
      expect(screen.getByText('Analyzing Project')).toBeInTheDocument();
    });

    it('shows progress bar', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      renderWithState();

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      expect(screen.getByText(/50%/)).toBeInTheDocument();
    });

    it('navigates to projects when analysis completes', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'completed',
        progress: 100,
        result: { analysis_uuid: 'portfolio-uuid-123' },
      });
      renderWithState();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/projects');
      });
    });

    it('stores portfolio_id in sessionStorage when complete', async () => {
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');
      getTaskStatus.mockResolvedValue({
        status: 'completed',
        progress: 100,
        result: { analysis_uuid: 'portfolio-uuid-123' },
      });
      renderWithState();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/projects');
      });
      expect(setItemSpy).toHaveBeenCalledWith('portfolio_id', 'portfolio-uuid-123');
      setItemSpy.mockRestore();
    });

    it('shows failed state when task fails', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'failed',
        progress: 0,
        error: 'Analysis failed: Invalid ZIP',
      });
      renderWithState();

      await waitFor(() => {
        expect(screen.getByText(/Invalid ZIP/)).toBeInTheDocument();
      });
      expect(screen.getByText(/Analysis failed: Invalid ZIP/)).toBeInTheDocument();
    });

    it('has Go to Projects button disabled until complete', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      renderWithState();

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      const goButton = screen.getByText('Go to Projects');
      expect(goButton).toBeDisabled();
    });
  });
});
