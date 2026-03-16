import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// Mock useNavigate
const mockNavigate = vi.fn();

// Mock AuthContext
vi.mock('../contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}));

// Mock react-router-dom
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

// Mock Navigation
vi.mock('../components/Navigation', () => {
  return {
    default: () => <div data-testid="nav">Navigation</div>,
  };
});

// Mock API module
vi.mock('../services/api', () => {
  return {
    authAPI: {
      deleteAccount: vi.fn(),
    },
    consentAPI: {
      getConsent: vi.fn(),
      saveConsent: vi.fn(),
    },
    resumeAPI: {
      getPersonalInfo: vi.fn(),
      savePersonalInfo: vi.fn(),
      deletePersonalInfo: vi.fn(),
    },
  };
});

// Import after mocks
import Settings from '../pages/Settings';
import { authAPI, consentAPI, resumeAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const renderSettings = () => {
  useAuth.mockReturnValue({ logout: vi.fn() });
  return render(
    <BrowserRouter>
      <Settings />
    </BrowserRouter>
  );
};

describe('Settings Page', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.clear();

    localStorage.setItem('access_token', 'fake-token');
    localStorage.setItem('username', 'deleteaccount');
    localStorage.setItem('token_expiry', 'fake-expiry');
  });

  describe('Header + Navigation', () => {
    it('renders the page title', () => {
      consentAPI.getConsent.mockImplementation(() => new Promise(() => {}));
      resumeAPI.getPersonalInfo.mockImplementation(() => new Promise(() => {}));
      renderSettings();

      expect(screen.getByText('Settings')).toBeInTheDocument();
      expect(screen.getByText('Manage your account preferences.')).toBeInTheDocument();
    });

    it('has a Back to Dashboard button', () => {
      consentAPI.getConsent.mockImplementation(() => new Promise(() => {}));
      resumeAPI.getPersonalInfo.mockImplementation(() => new Promise(() => {}));
      renderSettings();

      expect(screen.getByText('Back to Dashboard')).toBeInTheDocument();
    });

    it('navigates to dashboard when Back to Dashboard is clicked', () => {
      consentAPI.getConsent.mockImplementation(() => new Promise(() => {}));
      resumeAPI.getPersonalInfo.mockImplementation(() => new Promise(() => {}));
      renderSettings();

      fireEvent.click(screen.getByText('Back to Dashboard'));
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  describe('Loading + Consent Display', () => {
    it('shows Loading… badges initially', async () => {
      consentAPI.getConsent.mockImplementation(() => new Promise(() => {}));
      resumeAPI.getPersonalInfo.mockImplementation(() => new Promise(() => {}));

      renderSettings();

      const loadingBadges = await screen.findAllByText('Loading…');
      expect(loadingBadges.length).toBeGreaterThanOrEqual(2);
    });

    it('shows Consented when API returns has_consented = true', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: true });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });
      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Consented')).toBeInTheDocument();
      });

      expect(screen.getByText('Enabled')).toBeInTheDocument();
    });

    it('shows Not Consented when API returns has_consented = false', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });
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
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByText(errorMessage)).toBeInTheDocument();
      });
    });
  });

  describe('Toggle + Confirmation Modal', () => {
    it('opens confirmation modal when toggle is clicked', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });
      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Not Consented')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { pressed: false });
      fireEvent.click(toggleButton);

      expect(screen.getByText('Are you sure?')).toBeInTheDocument();
      expect(screen.getByText(/enable/i)).toBeInTheDocument();
      expect(screen.getByText('Cancel')).toBeInTheDocument();
      expect(screen.getByText('Yes, update')).toBeInTheDocument();
    });

    it('cancel closes modal and does not call saveConsent', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });
      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Not Consented')).toBeInTheDocument();
      });

      const toggleButton = screen.getByRole('button', { pressed: false });
      fireEvent.click(toggleButton);

      fireEvent.click(screen.getByText('Cancel'));

      await waitFor(() => {
        expect(screen.queryByText('Are you sure?')).not.toBeInTheDocument();
      });

      expect(consentAPI.saveConsent).not.toHaveBeenCalled();
      expect(screen.getByText('Disabled')).toBeInTheDocument();
    });

    it('confirm calls saveConsent and updates UI to enabled', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      consentAPI.saveConsent.mockResolvedValue({ has_consented: true, message: 'Updated' });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });

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
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });

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
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });

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

      expect(screen.getByText('Not Consented')).toBeInTheDocument();
      expect(screen.getByText('Disabled')).toBeInTheDocument();
    });
  });

  describe('Personal Info', () => {
    it('loads personal info and populates fields', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: {
          name: 'Harjot',
          email: 'h@h.com',
          phone: '123',
          location: 'Kelowna',
          linkedIn: 'https://linkedin.com/in/x',
          github: 'https://github.com/x',
          website: 'https://x.com',
        },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      expect(screen.getByDisplayValue('h@h.com')).toBeInTheDocument();
      expect(screen.getByDisplayValue('123')).toBeInTheDocument();
      expect(screen.getByDisplayValue('Kelowna')).toBeInTheDocument();
      expect(screen.getByDisplayValue('https://linkedin.com/in/x')).toBeInTheDocument();
      expect(screen.getByDisplayValue('https://github.com/x')).toBeInTheDocument();
      expect(screen.getByDisplayValue('https://x.com')).toBeInTheDocument();
    });

    it('save button is disabled when nothing changed, enabled after change', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: { name: 'Harjot' } });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      const saveBtn = screen.getByRole('button', { name: /update personal info|save personal info/i });
      expect(saveBtn).toBeDisabled();

      fireEvent.change(screen.getByPlaceholderText('Full Name'), {
        target: { value: 'Harjot Sahota' },
      });

      expect(saveBtn).not.toBeDisabled();
    });

    it('clicking save calls savePersonalInfo and shows success message', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot', email: 'h@h.com' },
      });
      resumeAPI.savePersonalInfo.mockResolvedValue({ ok: true });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByPlaceholderText('Full Name'), {
        target: { value: 'Harjot Sahota' },
      });

      const saveBtn = screen.getByRole('button', { name: /update personal info|save personal info/i });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(resumeAPI.savePersonalInfo).toHaveBeenCalledTimes(1);
      });

      expect(resumeAPI.savePersonalInfo).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'Harjot Sahota',
        })
      );

      await waitFor(() => {
        expect(screen.getByText('Personal info saved successfully.')).toBeInTheDocument();
      });

      await waitFor(() => {
        expect(saveBtn).toBeDisabled();
      });
    });

    it('shows error message when getPersonalInfo fails', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockRejectedValue({
        response: { data: { detail: 'Failed to load personal info' } },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByText('Failed to load personal info')).toBeInTheDocument();
      });
    });

    it('remove button opens modal, confirm calls deletePersonalInfo and clears fields', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot', email: 'h@h.com' },
      });
      resumeAPI.deletePersonalInfo.mockResolvedValue({ ok: true });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      const removeBtn = screen.getByRole('button', { name: /remove info/i });
      expect(removeBtn).not.toBeDisabled();

      fireEvent.click(removeBtn);

      expect(screen.getByText('Remove personal info?')).toBeInTheDocument();
      expect(screen.getByText(/permanently remove/i)).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /yes, remove/i }));

      await waitFor(() => {
        expect(resumeAPI.deletePersonalInfo).toHaveBeenCalledTimes(1);
      });

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Full Name')).toHaveValue('');
      });

      expect(screen.getByPlaceholderText('Email Address')).toHaveValue('');
      expect(screen.getByText('Personal info removed.')).toBeInTheDocument();
    });

    it('remove error shows error message and does not clear fields', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot', email: 'h@h.com' },
      });
      resumeAPI.deletePersonalInfo.mockRejectedValue({
        response: { data: { detail: 'Failed to remove personal info' } },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /remove info/i }));
      fireEvent.click(screen.getByRole('button', { name: /yes, remove/i }));

      await waitFor(() => {
        expect(screen.getByText('Failed to remove personal info')).toBeInTheDocument();
      });

      expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      expect(screen.getByDisplayValue('h@h.com')).toBeInTheDocument();
    });

    it('cancel remove closes modal and does not call deletePersonalInfo', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot' },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByRole('button', { name: /remove info/i }));
      expect(screen.getByText('Remove personal info?')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /^cancel$/i }));

      await waitFor(() => {
        expect(screen.queryByText('Remove personal info?')).not.toBeInTheDocument();
      });

      expect(resumeAPI.deletePersonalInfo).not.toHaveBeenCalled();
    });

    it('validation blocks save when email is invalid', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot', email: 'h@h.com' },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByPlaceholderText('Email Address'), {
        target: { value: 'not-an-email' },
      });

      const saveBtn = screen.getByRole('button', { name: /update personal info|save personal info/i });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(screen.getByText(/enter a valid email address/i)).toBeInTheDocument();
      });

      expect(resumeAPI.savePersonalInfo).not.toHaveBeenCalled();
    });

    it('validation blocks save when phone contains letters', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot', email: 'h@h.com', phone: '5551234567' },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByPlaceholderText('Phone Number'), {
        target: { value: '555-abc-1234' },
      });

      const saveBtn = screen.getByRole('button', { name: /update personal info|save personal info/i });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(screen.getByText(/phone may only contain digits/i)).toBeInTheDocument();
      });

      expect(resumeAPI.savePersonalInfo).not.toHaveBeenCalled();
    });

    it('validation blocks save when name is empty', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot', email: 'h@h.com' },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByPlaceholderText('Full Name'), {
        target: { value: '' },
      });

      const saveBtn = screen.getByRole('button', { name: /update personal info|save personal info/i });
      fireEvent.click(saveBtn);

      await waitFor(() => {
        expect(screen.getByText(/full name is required/i)).toBeInTheDocument();
      });

      expect(resumeAPI.savePersonalInfo).not.toHaveBeenCalled();
    });

    it('Cancel button reverts to original when user has unsaved changes', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot', email: 'h@h.com' },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByPlaceholderText('Full Name'), {
        target: { value: 'Harjot Sahota' },
      });

      expect(screen.getByDisplayValue('Harjot Sahota')).toBeInTheDocument();

      const cancelBtn = screen.getByRole('button', { name: /^cancel$/i });
      fireEvent.click(cancelBtn);

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      expect(screen.getByPlaceholderText('Full Name')).toHaveValue('Harjot');
    });

    it('Cancel button does not show when no saved data', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByPlaceholderText('Full Name')).toBeInTheDocument();
      });

      expect(screen.queryByRole('button', { name: /^cancel$/i })).not.toBeInTheDocument();
    });

    it('Cancel button does not show when no changes', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({
        personal_info: { name: 'Harjot', email: 'h@h.com' },
      });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByDisplayValue('Harjot')).toBeInTheDocument();
      });

      expect(screen.queryByRole('button', { name: /^cancel$/i })).not.toBeInTheDocument();
    });
  });

  describe('Delete Account', () => {
    it('renders the delete account section', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });

      renderSettings();

      await waitFor(() => {
        expect(screen.getByRole('heading', { name: /delete account/i })).toBeInTheDocument();
      });
      
      expect(screen.getByRole('button', { name: /delete account/i })).toBeInTheDocument();
      
      expect(
        screen.getByText(/permanently delete your account and all associated data/i)
      ).toBeInTheDocument();
    });

    it('opens delete account confirmation modal', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });

      renderSettings();

      await waitFor(() => {
        expect(screen.getAllByText('Delete Account').length).toBeGreaterThan(0);
      });

      const deleteButtons = screen.getAllByRole('button', { name: /delete account/i });
      fireEvent.click(deleteButtons[0]);

      expect(screen.getByText('Delete account?')).toBeInTheDocument();
      expect(
        screen.getByText(/this will permanently delete your account and everything associated with it/i)
      ).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /yes, delete/i })).toBeInTheDocument();
    });

    it('cancel delete account closes modal and does not call API', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });

      renderSettings();

      await waitFor(() => {
        expect(screen.getAllByText('Delete Account').length).toBeGreaterThan(0);
      });

      const deleteButtons = screen.getAllByRole('button', { name: /delete account/i });
      fireEvent.click(deleteButtons[0]);

      expect(screen.getByText('Delete account?')).toBeInTheDocument();

      fireEvent.click(screen.getByRole('button', { name: /^cancel$/i }));

      await waitFor(() => {
        expect(screen.queryByText('Delete account?')).not.toBeInTheDocument();
      });

      expect(authAPI.deleteAccount).not.toHaveBeenCalled();
    });

    it('confirm delete account calls API, clears localStorage, and navigates to login', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });
      authAPI.deleteAccount.mockResolvedValue({ message: 'Account deleted successfully' });
    
      const removeItemSpy = vi.spyOn(window.localStorage, 'removeItem');
    
      renderSettings();
    
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /delete account/i })).toBeInTheDocument();
      });
    
      fireEvent.click(screen.getByRole('button', { name: /delete account/i }));
      fireEvent.click(screen.getByRole('button', { name: /yes, delete/i }));
    
      await waitFor(() => {
        expect(authAPI.deleteAccount).toHaveBeenCalledTimes(1);
      });
    
      await waitFor(() => {
        expect(removeItemSpy).toHaveBeenCalledWith('access_token');
        expect(removeItemSpy).toHaveBeenCalledWith('username');
        expect(removeItemSpy).toHaveBeenCalledWith('token_expiry');
      });
    
      expect(mockNavigate).toHaveBeenCalledWith('/login');
    
      removeItemSpy.mockRestore();
    });

    it('shows error message when delete account fails', async () => {
      consentAPI.getConsent.mockResolvedValue({ has_consented: false });
      resumeAPI.getPersonalInfo.mockResolvedValue({ personal_info: {} });
      authAPI.deleteAccount.mockRejectedValue({
        response: { data: { detail: 'Failed to delete account' } },
      });
    
      const removeItemSpy = vi.spyOn(Storage.prototype, 'removeItem');
    
      renderSettings();
    
      await waitFor(() => {
        expect(screen.getByRole('button', { name: /delete account/i })).toBeInTheDocument();
      });
    
      fireEvent.click(screen.getByRole('button', { name: /delete account/i }));
      fireEvent.click(screen.getByRole('button', { name: /yes, delete/i }));
    
      await waitFor(() => {
        expect(screen.getByText('Failed to delete account')).toBeInTheDocument();
      });
    
      expect(mockNavigate).not.toHaveBeenCalledWith('/login');
      expect(removeItemSpy).not.toHaveBeenCalledWith('access_token');
      expect(removeItemSpy).not.toHaveBeenCalledWith('username');
      expect(removeItemSpy).not.toHaveBeenCalledWith('token_expiry');
    
      removeItemSpy.mockRestore();
    });
  });
});