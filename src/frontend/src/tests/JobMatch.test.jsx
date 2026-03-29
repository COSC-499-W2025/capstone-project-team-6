import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../components/Navigation', () => ({
  default: () => <div data-testid="nav">Navigation</div>,
}));

vi.mock('../services/api', () => ({
  resumeAPI: {
    analyzeJobMatch: vi.fn(),
    listJobMatches: vi.fn(),
    deleteJobMatch: vi.fn(),
  },
}));

import JobMatch from '../pages/JobMatch';
import { resumeAPI } from '../services/api';
import { NavigationBlockProvider } from '../contexts/NavigationBlockContext';

const MOCK_MATCH = {
  id: 42,
  job_description: 'We need a senior engineer with Python and distributed systems experience for our platform team.',
  overall_score: 71,
  skills_score: 75,
  experience_score: 68,
  matched_skills: ['Python'],
  missing_skills: ['Kafka'],
  matched_requirements: ['Degree'],
  unmet_requirements: ['Ten years'],
  recommendations: ['Study streaming'],
  summary: 'Solid match overall.',
  created_at: '2026-03-28T12:00:00',
};

const MOCK_ANALYZE_RESPONSE = {
  id: 99,
  job_description: 'x'.repeat(50),
  overall_score: 88,
  skills_score: 90,
  experience_score: 85,
  matched_skills: ['TypeScript'],
  missing_skills: [],
  matched_requirements: [],
  unmet_requirements: [],
  recommendations: [],
  summary: 'Excellent fit.',
};

function renderJobMatch() {
  return render(
    <BrowserRouter>
      <NavigationBlockProvider>
        <JobMatch />
      </NavigationBlockProvider>
    </BrowserRouter>
  );
}

describe('JobMatch', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    resumeAPI.listJobMatches.mockResolvedValue([]);
    resumeAPI.analyzeJobMatch.mockResolvedValue(MOCK_ANALYZE_RESPONSE);
    resumeAPI.deleteJobMatch.mockResolvedValue({ ok: true });
  });

  it('loads saved matches on mount', async () => {
    renderJobMatch();
    await waitFor(() => {
      expect(resumeAPI.listJobMatches).toHaveBeenCalledTimes(1);
    });
  });

  it('renders saved match cards when list returns data', async () => {
    resumeAPI.listJobMatches.mockResolvedValue([MOCK_MATCH]);
    renderJobMatch();
    expect(await screen.findByText(/Saved Matches \(1\)/i)).toBeInTheDocument();
    expect(screen.getByText(/71/)).toBeInTheDocument();
  });

  it('expands a saved card to show analysis details', async () => {
    resumeAPI.listJobMatches.mockResolvedValue([MOCK_MATCH]);
    renderJobMatch();
    const snippet = await screen.findByText(/We need a senior engineer/i);
    fireEvent.click(snippet.parentElement.parentElement);

    expect(await screen.findByText('Overall Match')).toBeInTheDocument();
    expect(screen.getByText('Minimize')).toBeInTheDocument();
  });

  it('runs analyze and shows latest analysis', async () => {
    renderJobMatch();
    await waitFor(() => expect(resumeAPI.listJobMatches).toHaveBeenCalled());

    const input = screen.getByPlaceholderText(/Paste the full job description/i);
    fireEvent.change(input, { target: { value: 'y'.repeat(52) } });
    fireEvent.click(screen.getByRole('button', { name: /Analyze Match/i }));

    await waitFor(() => {
      expect(resumeAPI.analyzeJobMatch).toHaveBeenCalled();
    });
    expect(await screen.findByText('Latest Analysis')).toBeInTheDocument();
    expect(screen.getByText('Excellent fit.')).toBeInTheDocument();
  });

  it('deletes a saved match when delete is triggered', async () => {
    resumeAPI.listJobMatches.mockResolvedValue([MOCK_MATCH]);
    renderJobMatch();
    await screen.findByText(/Saved Matches \(1\)/i);

    const deleteBtn = screen.getByTitle('Delete match');
    fireEvent.click(deleteBtn);

    await waitFor(() => {
      expect(resumeAPI.deleteJobMatch).toHaveBeenCalledWith(42);
    });
  });
});
