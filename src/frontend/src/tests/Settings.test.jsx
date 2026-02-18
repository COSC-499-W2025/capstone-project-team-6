import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock useNavigate
const mockNavigate = vi.fn();

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock Navigation (so tests don’t depend on it)
vi.mock('../components/Navigation', () => {
  return {
    default: () => <div data-testid="nav">Navigation</div>,
  };
});

// Mock API module
vi.mock('../services/api', () => {
  return {
    consentAPI: {
      getConsent: vi.fn(),
      saveConsent: vi.fn(),
    },
  };
});

// Import after mocks
import Settings from '../pages/Settings';
import { consentAPI } from '../services/api';

const renderSettings = () => {
  return render(
    <BrowserRouter>
      <Settings />
    </BrowserRouter>
  );
};

describe('Settings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Header + Navigation', () => {
    it('renders the page title', () => {
      consentAPI.getConsent.mockImplementation(() => new Promise(() => {}));
      renderSettings();

      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Manage your account preferences.')).toBeInTheDocument();
    });

    it('has a Back to Dashboard button', () => {
      consentAPI.getConsent.mockImplementation(() => new Promise(() => {}));
      renderSettings();

      expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();
    });

    it('navigates to dashboard when Back to Dashboard is clicked', () => {
      consentAPI.getConsent.mockImplementation(() => new Promise(() => {}));
      renderSettings();

      fireEvent.click(screen.getByText('Back to Dashboard'));
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  describe('Loading + Consent Display', () => {
    it('shows Loading… in the status badge initially', () => {
      consentAPI.getConsent.mockImplementation(() => new Promise(() => {}));
      renderSettings();

      expect(screen.getByText('Loading…')).toBeInTheDocument();
    });

    it('shows Consented when API returns has_consented = true', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: true });
      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Consented')).toBeInTheDocument();
      });

      // Toggle label should match state
      expect(screen.getByText('Enabled')).toBeInTheDocument();
    });

    it('shows Not Consented when API returns has_consented = false', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Not Consented')).toBeInTheDocument();
      });

      expect(screen.getByText('Disabled')).toBeInTheDocument();
    });

    it('shows error message when getConsent fails', async () => {
      const errorMessage = 'Failed to load consent';
      consentAPI.getConsent.mockRejectedValue({
        response: { data: { detail: errorMessage } },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });
  });

  describe('Toggle + Confirmation Modal', () => {
    it('opens confirmation modal when toggle is clicked', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Not Consented')).toBeInTheDocument();
      });

      // Click the toggle switch button (it is a <button aria-pressed=...>)
      const toggleButton = screen.getByRole('button', { pressed: false });
      fireEvent.click(toggleButton);

      expect(screen.getByText('Are you sure?')).toBeInTheDocument();
      expect(screen.getByText(/enable/i)).toBeInTheDocument(); // message says enable/disable
      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Yes, update')).toBeInTheDocument();
    });

    it('cancel closes modal and does not call saveConsent', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Not Consented')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { pressed: false });
      fireEvent.click(toggleButton);

      expect(screen.getByText('Are you sure?')).toBeInTheDocument();

      fireEvent.click(screen.getByText('Cancel'));

      await waitFor(() => {
        expect(screen.queryByText('Are you sure?')).not.toBeInTheDocument();
      });

      expect(consentAPI.saveConsent).not.toHaveBeenCalled();
      // Still disabled
      expect(screen.getByText('Disabled')).toBeInTheDocument();
    });

    it('confirm calls saveConsent and updates UI to enabled', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      consentAPI.saveConsent.mockResolvedValue({ has_consented: true, message: 'Updated' });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Not Consented')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { pressed: false });
      fireEvent.click(toggleButton);

      fireEvent.click(screen.getByText('Yes, update'));

      await waitFor(() => {
        expect(consentAPI.saveConsent).toHaveBeenCalledTimes(1);
        expect(consentAPI.saveConsent).toHaveBeenCalledWith(true);
      });

      await waitFor(() => {
        expect(screen.getByText('Consented')).toBeInTheDocument();
      });

      expect(screen.getByText('Enabled')).toBeInTheDocument();
      expect(screen.getByText('Updated')).toBeInTheDocument();
    });

    it('confirm calls saveConsent and updates UI to disabled', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: true });
      consentAPI.saveConsent.mockResolvedValue({ has_consented: false, message: 'Updated' });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Consented')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { pressed: true });
      fireEvent.click(toggleButton);

      fireEvent.click(screen.getByText('Yes, update'));

      await waitFor(() => {
        expect(consentAPI.saveConsent).toHaveBeenCalledTimes(1);
        expect(consentAPI.saveConsent).toHaveBeenCalledWith(false);
      });

      await waitFor(() => {
        expect(screen.getByText('Not Consented')).toBeInTheDocument();
      });

      expect(screen.getByText('Disabled')).toBeInTheDocument();
      expect(screen.getByText('Updated')).toBeInTheDocument();
    });

    it('shows error message when saveConsent fails and keeps previous state', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      consentAPI.saveConsent.mockRejectedValue({
        response: { data: { detail: 'Failed to update consent' } },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Not Consented')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { pressed: false });
      fireEvent.click(toggleButton);

      fireEvent.click(screen.getByText('Yes, update'));

      await waitFor(() => {
        expect(screen.getByText('Failed to update consent')).toBeInTheDocument();
      });

      // Should still be disabled + not consented (reverted)
      expect(screen.getByText('Not Consented')).toBeInTheDocument();
      expect(screen.getByText('Disabled')).toBeInTheDocument();
    });
  });
});
