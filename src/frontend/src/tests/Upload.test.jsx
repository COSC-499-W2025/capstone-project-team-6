import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

vi.mock('../services/api', () => ({
  default: {
    post: vi.fn(),
  },
  consentAPI: {
    getConsent: vi.fn().mockResolvedValue({ has_consented: false }),
  },
  portfoliosAPI: {
    listPortfolios: vi.fn().mockResolvedValue([]),
    addToPortfolio: vi.fn(),
  },
}));

import Upload from '../pages/Upload';
import api, { consentAPI } from '../services/api';

describe('Upload', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Single project upload flow', () => {
    it('extracts task_id from details and navigates to analyze page', async () => {
      const taskId = 'task-uuid-12345';
      api.post.mockResolvedValue({
        data: {
          message: 'Upload accepted',
          details: {
            task_id: taskId,
            filename: 'project.zip',
            status: 'processing',
          },
        },
      });

      const file = new File(['content'], 'project.zip', { type: 'application/zip' });
      const { container } = render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );

      // Select file and enter project name (both required for Analyze to be enabled)
      const input = container.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });
      const nameInput = screen.getByPlaceholderText('My Awesome Project');
      fireEvent.change(nameInput, { target: { value: 'My Project' } });

      // Click Analyze Project
      const submitButton = screen.getByText('Analyze Project');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledWith(
          '/portfolios/upload',
          expect.any(FormData),
          expect.objectContaining({ headers: { 'Content-Type': 'multipart/form-data' } })
        );
      });

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/analyze', { state: { taskId } });
      });
    });

    it('extracts task_id from top-level when details not present', async () => {
      const taskId = 'task-top-level';
      api.post.mockResolvedValue({
        data: {
          task_id: taskId,
          message: 'Upload accepted',
        },
      });

      const file = new File(['content'], 'project.zip', { type: 'application/zip' });
      const { container } = render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );

      const input = container.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });
      fireEvent.change(screen.getByPlaceholderText('My Awesome Project'), { target: { value: 'My Project' } });

      fireEvent.click(screen.getByText('Analyze Project'));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith('/analyze', { state: { taskId } });
      });
    });

    it('shows error when no task_id returned', async () => {
      api.post.mockResolvedValue({
        data: {
          message: 'Upload accepted',
          details: { filename: 'project.zip' },
          // No task_id
        },
      });

      const file = new File(['content'], 'project.zip', { type: 'application/zip' });
      const { container } = render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );

      const input = container.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });
      fireEvent.change(screen.getByPlaceholderText('My Awesome Project'), { target: { value: 'My Project' } });

      fireEvent.click(screen.getByText('Analyze Project'));

      await waitFor(() => {
        expect(screen.getByText(/no task_id was returned/i)).toBeInTheDocument();
      });
      expect(mockNavigate).not.toHaveBeenCalled();
    });

    it('displays Analyze Project button for single tab', () => {
      render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );
      expect(screen.getByText('Analyze Project')).toBeInTheDocument();
    });
  });

  describe('Multiple projects upload flow', () => {
    it('navigates to analyze with all task IDs for multiple uploads', async () => {
      const taskId1 = 'task-uuid-1';
      const taskId2 = 'task-uuid-2';
      api.post
        .mockResolvedValueOnce({
          data: {
            message: 'Upload accepted',
            details: { task_id: taskId1, filename: 'project1.zip', status: 'processing' },
          },
        })
        .mockResolvedValueOnce({
          data: {
            message: 'Upload accepted',
            details: { task_id: taskId2, filename: 'project2.zip', status: 'processing' },
          },
        });

      const file1 = new File(['a'], 'project1.zip', { type: 'application/zip' });
      const file2 = new File(['b'], 'project2.zip', { type: 'application/zip' });
      const { container } = render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );

      fireEvent.click(screen.getByText('Multiple Projects'));
      const input = container.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file1, file2] } });

      await waitFor(() => {
        expect(screen.getByText('Analyze Projects')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Analyze Projects'));

      await waitFor(() => {
        expect(api.post).toHaveBeenCalledTimes(2);
      });
      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(
          '/analyze',
          expect.objectContaining({
            state: expect.objectContaining({ taskIds: [taskId1, taskId2] }),
          })
        );
      });
    });
  });

  describe('LLM analysis type gating', () => {
    it('sends non_llm analysis_type when user has not consented', async () => {
      // Default mock: has_consented: false
      const taskId = 'task-no-consent';
      api.post.mockResolvedValue({
        data: { task_id: taskId },
      });

      const file = new File(['content'], 'project.zip', { type: 'application/zip' });
      const { container } = render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );

      const input = container.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });
      fireEvent.change(screen.getByPlaceholderText('My Awesome Project'), {
        target: { value: 'My Project' },
      });

      fireEvent.click(screen.getByText('Analyze Project'));

      await waitFor(() => {
        const formData = api.post.mock.calls[0][1];
        expect(formData.get('analysis_type')).toBe('non_llm');
      });
    });

    it('sends non_llm analysis_type when consent given but checkbox is unchecked', async () => {
      consentAPI.getConsent.mockResolvedValueOnce({ has_consented: true });
      const taskId = 'task-unchecked';
      api.post.mockResolvedValue({
        data: { task_id: taskId },
      });

      const file = new File(['content'], 'project.zip', { type: 'application/zip' });
      const { container } = render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );

      // Wait for the consent fetch to resolve so the checkbox becomes enabled
      await waitFor(() => {
        expect(container.querySelector('input[type="checkbox"]')).not.toBeDisabled();
      });

      // Uncheck the LLM analysis checkbox
      const checkbox = container.querySelector('input[type="checkbox"]');
      fireEvent.click(checkbox);

      const input = container.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });
      fireEvent.change(screen.getByPlaceholderText('My Awesome Project'), {
        target: { value: 'My Project' },
      });

      fireEvent.click(screen.getByText('Analyze Project'));

      await waitFor(() => {
        const formData = api.post.mock.calls[0][1];
        expect(formData.get('analysis_type')).toBe('non_llm');
      });
    });

    it('includes analysisType in navigate state for multiple uploads', async () => {
      // Default mock: has_consented: false → effectiveAnalysisType = 'non_llm'
      const taskId1 = 'task-multi-1';
      const taskId2 = 'task-multi-2';
      api.post
        .mockResolvedValueOnce({
          data: { details: { task_id: taskId1 } },
        })
        .mockResolvedValueOnce({
          data: { details: { task_id: taskId2 } },
        });

      const file1 = new File(['a'], 'p1.zip', { type: 'application/zip' });
      const file2 = new File(['b'], 'p2.zip', { type: 'application/zip' });
      const { container } = render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );

      fireEvent.click(screen.getByText('Multiple Projects'));
      const input = container.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file1, file2] } });

      await waitFor(() => {
        expect(screen.getByText('Analyze Projects')).toBeInTheDocument();
      });
      fireEvent.click(screen.getByText('Analyze Projects'));

      await waitFor(() => {
        expect(mockNavigate).toHaveBeenCalledWith(
          '/analyze',
          expect.objectContaining({
            state: expect.objectContaining({
              taskIds: [taskId1, taskId2],
              analysisType: 'non_llm',
            }),
          })
        );
      });
    });

    it('stores analysisType in sessionStorage for multiple uploads', async () => {
      const setItemSpy = vi.spyOn(Storage.prototype, 'setItem');
      const taskId = 'task-storage';
      api.post.mockResolvedValue({ data: { details: { task_id: taskId } } });

      const file = new File(['a'], 'p.zip', { type: 'application/zip' });
      const { container } = render(
        <BrowserRouter>
          <Upload />
        </BrowserRouter>
      );

      fireEvent.click(screen.getByText('Multiple Projects'));
      const input = container.querySelector('input[type="file"]');
      fireEvent.change(input, { target: { files: [file] } });

      await waitFor(() => expect(screen.getByText('Analyze Projects')).toBeInTheDocument());
      fireEvent.click(screen.getByText('Analyze Projects'));

      await waitFor(() => {
        expect(setItemSpy).toHaveBeenCalledWith('analyze_analysis_type', 'non_llm');
      });
      setItemSpy.mockRestore();
    });
  });
});
