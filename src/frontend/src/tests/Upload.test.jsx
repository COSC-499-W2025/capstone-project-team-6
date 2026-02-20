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
import api from '../services/api';

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
});
