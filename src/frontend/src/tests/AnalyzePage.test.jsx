import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
const renderWithState = (taskId = 'test-task-123') => {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/analyze', state: { taskId } }]}>
      <AnalyzePage />
    </MemoryRouter>
  );
};

const renderWithTaskIds = (taskIds = ['task-1', 'task-2']) => {
  return render(
    <MemoryRouter initialEntries={[{ pathname: '/analyze', state: { taskIds } }]}>
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
      sessionStorage.removeItem('analyze_task_id');
      render(
        <MemoryRouter initialEntries={['/analyze']}>
          <AnalyzePage />
        </MemoryRouter>
      );
      expect(screen.getByText(/Missing task\. Please go back to Upload/i)).toBeInTheDocument();
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
      expect(screen.getByText('Analyzing Project')).toBeInTheDocument();
    });

    it('shows progress bar', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      renderWithState();

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument();
      });
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
      getTaskStatus.mockResolvedValue({
        status: 'completed',
        progress: 100,
        result: { analysis_uuid: 'portfolio-uuid-123' },
      });
      renderWithState();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/projects');
      });
      expect(sessionStorage.getItem('portfolio_id')).toBe('portfolio-uuid-123');
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
      expect(screen.getAllByText(/Analysis failed: Invalid ZIP/).length).toBeGreaterThan(0);
    });

    it('has Go to Projects button disabled until complete', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      renderWithState();

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      const goButton = screen.getByText(/Go to Projects/);
      expect(goButton).toBeDisabled();
    });

    it('uses sessionStorage fallback when location.state has no taskId', async () => {
      sessionStorage.setItem('analyze_task_id', 'task-from-storage');
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      render(
        <MemoryRouter initialEntries={[{ pathname: '/analyze', state: {} }]}>
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalledWith('task-from-storage', 'test-token');
      });
      expect(screen.getByText('Analyzing Project')).toBeInTheDocument();
      sessionStorage.removeItem('analyze_task_id');
    });

    it('shows analysis phase when running (non-LLM)', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'running',
        progress: 60,
        analysis_phase: 'non_llm',
      });
      renderWithState();

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      await waitFor(() => {
        expect(screen.getByText(/Running non-LLM analysis/)).toBeInTheDocument();
      });
    });

    it('shows analysis phase when running (LLM)', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'running',
        progress: 95,
        analysis_phase: 'llm',
      });
      render(
        <MemoryRouter initialEntries={[{ pathname: '/analyze', state: { taskId: 'test-task-123', analysisType: 'llm' } }]}>
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      await waitFor(() => {
        expect(screen.getByText(/Running LLM analysis/)).toBeInTheDocument();
      });
    });
  });

  describe('Analysis type badge', () => {
    it('shows LLM Analysis badge when analysisType is llm', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 10 });
      render(
        <MemoryRouter
          initialEntries={[{ pathname: '/analyze', state: { taskId: 'task-1', analysisType: 'llm' } }]}
        >
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      expect(screen.getByText(/LLM Analysis/)).toBeInTheDocument();
    });

    it('shows Non-LLM Analysis badge when analysisType is non_llm', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 10 });
      render(
        <MemoryRouter
          initialEntries={[
            { pathname: '/analyze', state: { taskId: 'task-1', analysisType: 'non_llm' } },
          ]}
        >
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      expect(screen.getByText(/Non-LLM Analysis/)).toBeInTheDocument();
    });

    it('defaults to Non-LLM Analysis badge when no analysisType is provided', async () => {
      sessionStorage.removeItem('analyze_analysis_type');
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 10 });
      render(
        <MemoryRouter
          initialEntries={[{ pathname: '/analyze', state: { taskId: 'task-1' } }]}
        >
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      expect(screen.getByText(/Non-LLM Analysis/)).toBeInTheDocument();
    });

    it('shows Running LLM analysis phase message when server reports llm phase', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'running',
        progress: 50,
        analysis_phase: 'llm',
      });
      render(
        <MemoryRouter
          initialEntries={[{ pathname: '/analyze', state: { taskId: 'task-1', analysisType: 'llm' } }]}
        >
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Running LLM analysis/)).toBeInTheDocument();
      });
    });

    it('shows Running non-LLM analysis phase message when server reports non_llm phase', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'running',
        progress: 50,
        analysis_phase: 'non_llm',
      });
      render(
        <MemoryRouter
          initialEntries={[
            { pathname: '/analyze', state: { taskId: 'task-1', analysisType: 'non_llm' } },
          ]}
        >
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(screen.getByText(/Running non-LLM analysis/)).toBeInTheDocument();
      });
    });

    it('does NOT show Running LLM analysis when server reports llm phase but user chose non_llm', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'running',
        progress: 50,
        analysis_phase: 'llm',
      });
      render(
        <MemoryRouter
          initialEntries={[
            { pathname: '/analyze', state: { taskId: 'task-1', analysisType: 'non_llm' } },
          ]}
        >
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      expect(screen.queryByText(/Running LLM analysis/)).not.toBeInTheDocument();
    });
  });

  describe('Multi-task polling', () => {
    it('polls all task IDs when taskIds is passed', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      renderWithTaskIds(['task-a', 'task-b']);

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalledWith('task-a', 'test-token');
        expect(getTaskStatus).toHaveBeenCalledWith('task-b', 'test-token');
      });
    });

    it('navigates to projects only when all tasks are completed', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'completed',
        progress: 100,
        result: { analysis_uuid: 'uuid-1' },
      });
      renderWithTaskIds(['task-1', 'task-2']);

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/projects');
      });
      expect(getTaskStatus).toHaveBeenCalledWith('task-1', 'test-token');
      expect(getTaskStatus).toHaveBeenCalledWith('task-2', 'test-token');
    });

    it('uses sessionStorage analyze_task_ids fallback for multi-task', async () => {
      sessionStorage.setItem('analyze_task_ids', JSON.stringify(['stored-task-1', 'stored-task-2']));
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      render(
        <MemoryRouter initialEntries={[{ pathname: '/analyze', state: {} }]}>
          <AnalyzePage />
        </MemoryRouter>
      );

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalledWith('stored-task-1', 'test-token');
        expect(getTaskStatus).toHaveBeenCalledWith('stored-task-2', 'test-token');
      });
      expect(screen.getByText(/projects completed/)).toBeInTheDocument();
      sessionStorage.removeItem('analyze_task_ids');
    });

    it('shows average of per-task progress while multi-task analyses run (not only completion count)', async () => {
      getTaskStatus.mockImplementation(async (taskId) => {
        if (taskId === 'task-a') return { status: 'running', progress: 40 };
        return { status: 'running', progress: 60 };
      });
      renderWithTaskIds(['task-a', 'task-b']);

      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument();
      });
    });

    it('when first task completes, bar is 50% even if API reports progress < 100 on completed', async () => {
      getTaskStatus.mockImplementation(async (taskId) => {
        if (taskId === 'task-a') {
          return {
            status: 'completed',
            progress: 92,
            result: { analysis_uuid: 'uuid-a' },
          };
        }
        return { status: 'running', progress: 0 };
      });
      renderWithTaskIds(['task-a', 'task-b']);

      await waitFor(() => {
        expect(screen.getByText(/50%/)).toBeInTheDocument();
      });
    });
  });

  describe('Retry button', () => {
    it('shows "Try Again" button when analysis fails', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'failed',
        error: 'Something went wrong',
      });
      renderWithState();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
      });
    });

    it('does not show "Try Again" button while analysis is running', async () => {
      getTaskStatus.mockResolvedValue({ status: 'running', progress: 50 });
      renderWithState();

      await waitFor(() => {
        expect(getTaskStatus).toHaveBeenCalled();
      });
      expect(screen.queryByRole('button', { name: /Try Again/i })).not.toBeInTheDocument();
    });

    it('does not show "Try Again" button when analysis succeeds', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'completed',
        progress: 100,
        result: { analysis_uuid: 'uuid-1' },
      });
      renderWithState();

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/projects');
      });
      expect(screen.queryByRole('button', { name: /Try Again/i })).not.toBeInTheDocument();
    });

    it('navigates to /upload when "Try Again" is clicked', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'failed',
        error: 'Analysis failed: timeout',
      });
      renderWithState();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
      });

      await userEvent.click(screen.getByRole('button', { name: /Try Again/i }));

      expect(mockNavigate).toHaveBeenCalledWith('/upload');
    });

    it('does not trigger additional getTaskStatus calls when "Try Again" is clicked', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'failed',
        error: 'Analysis failed',
      });
      renderWithState();

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
      });

      const callsBefore = getTaskStatus.mock.calls.length;
      await userEvent.click(screen.getByRole('button', { name: /Try Again/i }));

      expect(getTaskStatus.mock.calls.length).toBe(callsBefore);
    });

    it('shows "Try Again" button when all tasks in a multi-task run fail', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'failed',
        error: 'All analyses failed',
      });
      renderWithTaskIds(['task-1', 'task-2']);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
      });
    });

    it('navigates to /upload when "Try Again" is clicked after a multi-task failure', async () => {
      getTaskStatus.mockResolvedValue({
        status: 'failed',
        error: 'All analyses failed',
      });
      renderWithTaskIds(['task-1', 'task-2']);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /Try Again/i })).toBeInTheDocument();
      });

      await userEvent.click(screen.getByRole('button', { name: /Try Again/i }));

      expect(mockNavigate).toHaveBeenCalledWith('/upload');
    });
  });
});
