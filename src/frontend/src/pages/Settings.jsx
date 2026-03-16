import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import { consentAPI, resumeAPI, authAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';

const Settings = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Consent
  const [currentConsent, setCurrentConsent] = useState(null);
  const [toggleConsent, setToggleConsent] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingConsent, setPendingConsent] = useState(null);

  const [statusMsg, setStatusMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [changingPassword, setChangingPassword] = useState(false);
  const [passwordStatusMsg, setPasswordStatusMsg] = useState('');
  const [passwordErrorMsg, setPasswordErrorMsg] = useState('');

  // --- Personal Info state ---
  const emptyPersonal = {
    name: '',
    email: '',
    phone: '',
    location: '',
    linkedIn: '',
    github: '',
    website: '',
    education: '',
    education_university: '',
    education_location: '',
    education_degree: '',
    education_start_date: '',
    education_end_date: '',
    education_awards: '',
  };

  const [personalInfo, setPersonalInfo] = useState(emptyPersonal);

  // what we loaded from DB last time (used to detect changes)
  const [originalPersonalInfo, setOriginalPersonalInfo] = useState(emptyPersonal);

  const [loadingPersonalInfo, setLoadingPersonalInfo] = useState(true);
  const [savingPersonalInfo, setSavingPersonalInfo] = useState(false);

  const [personalStatusMsg, setPersonalStatusMsg] = useState('');
  const [personalErrorMsg, setPersonalErrorMsg] = useState('');

  // New state for remove personal info flow
  const [removingPersonalInfo, setRemovingPersonalInfo] = useState(false);
  const [showRemoveConfirm, setShowRemoveConfirm] = useState(false);

  // Delete account state
  const [deletingAccount, setDeletingAccount] = useState(false);
  const [showDeleteAccountConfirm, setShowDeleteAccountConfirm] = useState(false);

  const normalize = (v) => (v || '').trim();

  const infosEqual = (a, b) => {
    const keys = Object.keys(emptyPersonal);
    for (const k of keys) {
      if (normalize(a[k]) !== normalize(b[k])) return false;
    }
    return true;
  };

  const hasPersonalChanges = !infosEqual(personalInfo, originalPersonalInfo);

  const hasAnyPersonalInfoSaved = () => {
    const values = Object.values(personalInfo || {});
    for (let i = 0; i < values.length; i++) {
      const v = (values[i] || '').toString().trim();
      if (v.length > 0) return true;
    }
    return false;
  };

  useEffect(() => {
    const loadConsent = async () => {
      setErrorMsg('');
      setStatusMsg('');

      try {
        const res = await consentAPI.getConsent();
        const hasConsented = !!res?.has_consented;

        setCurrentConsent(hasConsented);
        setToggleConsent(hasConsented);
      } catch (err) {
        setErrorMsg(
          err?.response?.data?.detail ||
            'Failed to load your consent status. Please try again.'
        );
      }
    };

    const loadPersonalInfo = async () => {
      setLoadingPersonalInfo(true);
      setPersonalErrorMsg('');
      setPersonalStatusMsg('');

      try {
        const res = await resumeAPI.getPersonalInfo();
        const info = res?.personal_info || {};

        const loaded = {
          name: info?.name || '',
          email: info?.email || '',
          phone: info?.phone || '',
          location: info?.location || '',
          linkedIn: info?.linkedIn || '',
          github: info?.github || '',
          website: info?.website || '',
        };

        setPersonalInfo(loaded);
        setOriginalPersonalInfo(loaded);
      } catch (err) {
        setPersonalErrorMsg(
          err?.response?.data?.detail ||
            'Failed to load personal info. Please try again.'
        );
      } finally {
        setLoadingPersonalInfo(false);
      }
    };

    const loadAll = async () => {
      setLoading(true);
      try {
        await Promise.all([loadConsent(), loadPersonalInfo()]);
      } finally {
        setLoading(false);
      }
    };

    loadAll();
  }, []);

  const consentLabel =
    currentConsent === null ? 'Unknown' : currentConsent ? 'Consented' : 'Not Consented';

  const onToggleClick = () => {
    if (loading || saving || currentConsent === null) return;

    const nextValue = !toggleConsent;
    setPendingConsent(nextValue);
    setShowConfirm(true);
  };

  const onCancelChange = () => {
    setToggleConsent(!!currentConsent);
    setPendingConsent(null);
    setShowConfirm(false);
  };

  const onConfirmChange = async () => {
    if (pendingConsent === null) return;

    setSaving(true);
    setErrorMsg('');
    setStatusMsg('');

    try {
      const res = await consentAPI.saveConsent(pendingConsent);
      const updated = !!res?.has_consented;

      setCurrentConsent(updated);
      setToggleConsent(updated);

      setStatusMsg(res?.message || 'Consent updated successfully.');
    } catch (err) {
      setToggleConsent(!!currentConsent);

      setErrorMsg(
        err?.response?.data?.detail || 'Failed to update consent. Please try again.'
      );
    } finally {
      setPendingConsent(null);
      setShowConfirm(false);
      setSaving(false);
    }
  };

  const onChangePersonalField = (key, value) => {
    setPersonalInfo((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const onSavePersonalInfo = async () => {
    setPersonalErrorMsg('');
    setPersonalStatusMsg('');

    // ✅ Nothing changed -> do nothing (and show no "saved" popup)
    if (!hasPersonalChanges) return;

    setSavingPersonalInfo(true);

    try {
      await resumeAPI.savePersonalInfo(personalInfo);

      // ✅ Only show this because we *know* something changed
      setPersonalStatusMsg('Personal info saved successfully.');

      // ✅ mark the form as "clean" now
      setOriginalPersonalInfo(personalInfo);
    } catch (err) {
      setPersonalErrorMsg(
        err?.response?.data?.detail || 'Failed to save personal info. Please try again.'
      );
    } finally {
      setSavingPersonalInfo(false);
    }
  };

  // --- Remove Personal Info Handlers ---
  const onClickRemovePersonalInfo = () => {
    setPersonalErrorMsg('');
    setPersonalStatusMsg('');
    setShowRemoveConfirm(true);
  };

  const onCancelRemovePersonalInfo = () => {
    setShowRemoveConfirm(false);
  };

  const onConfirmRemovePersonalInfo = async () => {
    setPersonalErrorMsg('');
    setPersonalStatusMsg('');
    setRemovingPersonalInfo(true);

    try {
      await resumeAPI.deletePersonalInfo();

      // clear UI + mark clean
      setPersonalInfo(emptyPersonal);
      setOriginalPersonalInfo(emptyPersonal);

      setPersonalStatusMsg('Personal info removed.');
    } catch (err) {
      setPersonalErrorMsg(
        err?.response?.data?.detail ||
          'Failed to remove personal info. Please try again.'
      );
    } finally {
      setRemovingPersonalInfo(false);
      setShowRemoveConfirm(false);
    }
  };

  // --- Change Password Handlers ---
  const onChangePassword = async () => {
    setPasswordErrorMsg('');
    setPasswordStatusMsg('');

    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      setPasswordErrorMsg('All fields are required.');
      return;
    }

    if (newPassword.length < 6) {
      setPasswordErrorMsg('New password must be at least 6 characters.');
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordErrorMsg('New passwords do not match.');
      return;
    }

    setChangingPassword(true);

    try {
      await authAPI.changePassword(currentPassword, newPassword);
      setPasswordStatusMsg('Password changed successfully!');

      // Clear form
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setPasswordErrorMsg(
        err?.response?.data?.detail || 'Failed to change password. Please try again.'
      );
    } finally {
      setChangingPassword(false);
    }
  };

  // --- Logout Handler ---
  const onLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (err) {
      console.error('Logout error:', err);
      // Even if logout fails, still redirect to login
      navigate('/login');
    }
  };

  const onClickDeleteAccount = () => {
    setErrorMsg('');
    setStatusMsg('');
    setPersonalErrorMsg('');
    setPersonalStatusMsg('');
    setShowDeleteAccountConfirm(true);
  };

  const onCancelDeleteAccount = () => {
    if (deletingAccount) return;
    setShowDeleteAccountConfirm(false);
  };

  const onConfirmDeleteAccount = async () => {
    setDeletingAccount(true);
    setErrorMsg('');
    setStatusMsg('');
    setPersonalErrorMsg('');
    setPersonalStatusMsg('');

    try {
      await authAPI.deleteAccount();

      localStorage.removeItem('access_token');
      localStorage.removeItem('username');
      localStorage.removeItem('token_expiry');

      navigate('/login');
    } catch (err) {
      setErrorMsg(
        err?.response?.data?.detail || 'Failed to delete account. Please try again.'
      );
      setDeletingAccount(false);
      setShowDeleteAccountConfirm(false);
    }
  };

  const Toggle = ({ checked, disabled, onClick }) => {
    return (
      <button
        type="button"
        onClick={onClick}
        disabled={disabled}
        aria-pressed={checked}
        style={{
          width: '54px',
          height: '32px',
          borderRadius: '999px',
          border: '1px solid #e5e5e5',
          backgroundColor: checked ? '#16a34a' : '#e5e5e5',
          position: 'relative',
          cursor: disabled ? 'not-allowed' : 'pointer',
          opacity: disabled ? 0.6 : 1,
          padding: 0,
        }}
      >
        <span
          style={{
            width: '26px',
            height: '26px',
            borderRadius: '999px',
            backgroundColor: '#ffffff',
            position: 'absolute',
            top: '50%',
            transform: 'translateY(-50%)',
            left: checked ? '26px' : '2px',
            transition: 'left 180ms ease',
            boxShadow: '0 1px 2px rgba(0,0,0,0.2)',
          }}
        />
      </button>
    );
  };

  const pageStyles = { minHeight: '100vh', backgroundColor: '#fafafa' };
  const containerStyles = { maxWidth: '1100px', margin: '0 auto', padding: '48px 32px' };
  const cardStyles = {
    backgroundColor: 'white',
    border: '1px solid #e5e5e5',
    borderRadius: '16px',
  };
  const secondaryText = { color: '#737373' };
  const headingText = { color: '#1a1a1a' };

  const personalButtonLabel = hasAnyPersonalInfoSaved()
    ? 'Update Personal Info'
    : 'Save Personal Info';

  const inputStyle = {
    width: '100%',
    padding: '10px 12px',
    borderRadius: '10px',
    border: '1px solid #e5e5e5',
    outline: 'none',
    fontSize: '14px',
    backgroundColor: '#ffffff',
  };

  const labelStyle = {
    fontSize: '13px',
    color: '#374151',
    fontWeight: 600,
    marginBottom: '6px',
  };

  return (
    <div style={pageStyles}>
      <Navigation />

      <div style={containerStyles}>
        {/* Header */}
        <div
          style={{
            marginBottom: '32px',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: '16px',
          }}
        >
          <div>
            <h1
              style={{
                fontSize: '36px',
                fontWeight: '600',
                margin: '0 0 12px 0',
                ...headingText,
                letterSpacing: '-0.5px',
              }}
            >
              Settings
            </h1>
            <p style={{ fontSize: '16px', margin: 0, ...secondaryText }}>
              Manage your account preferences.
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <button
              onClick={onLogout}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                backgroundColor: '#dc2626',
                color: 'white',
                border: 'none',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#b91c1c';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = '#dc2626';
              }}
            >
              Logout
            </button>

            <button
              onClick={() => navigate('/dashboard')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 20px',
                backgroundColor: 'white',
                color: '#1a1a1a',
                border: '1px solid #e5e5e5',
                borderRadius: '8px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                transition: 'all 0.2s',
                whiteSpace: 'nowrap',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.backgroundColor = '#f5f5f5';
                e.currentTarget.style.borderColor = '#d4d4d4';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.backgroundColor = 'white';
                e.currentTarget.style.borderColor = '#e5e5e5';
              }}
            >
              <span style={{ opacity: 0.8 }}>←</span>
              <span>Back to Dashboard</span>
            </button>
          </div>
        </div>

        {/* Consent Card */}
        <div style={{ ...cardStyles, padding: '24px', marginBottom: '20px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: '16px',
              flexWrap: 'wrap',
            }}
          >
            <div style={{ flex: 1, minWidth: '260px' }}>
              <h2
                style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: '0 0 8px 0',
                }}
              >
                Research / LLM Consent
              </h2>

              <p style={{ fontSize: '14px', color: '#666', margin: 0, lineHeight: 1.5 }}>
                Toggle whether you consent to LLM-related analysis features where applicable.
                You can update this anytime.
              </p>

              <div style={{ marginTop: '14px' }}>
                <span style={{ fontSize: '13px', color: '#737373' }}>Current status: </span>
                <span
                  style={{
                    fontSize: '13px',
                    fontWeight: '600',
                    color:
                      currentConsent === null
                        ? '#737373'
                        : currentConsent
                        ? '#166534'
                        : '#991b1b',
                    backgroundColor:
                      currentConsent === null
                        ? '#f5f5f5'
                        : currentConsent
                        ? '#dcfce7'
                        : '#fee2e2',
                    padding: '4px 10px',
                    borderRadius: '999px',
                    border: '1px solid #e5e5e5',
                    display: 'inline-block',
                  }}
                >
                  {loading ? 'Loading…' : consentLabel}
                </span>
              </div>
            </div>

            <div
              style={{
                minWidth: '280px',
                flex: 0,
                display: 'flex',
                flexDirection: 'column',
                gap: '12px',
              }}
            >
              <div
                style={{
                  backgroundColor: '#fafafa',
                  border: '1px solid #e5e5e5',
                  borderRadius: '12px',
                  padding: '14px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    gap: '12px',
                  }}
                >
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 600, color: '#1a1a1a' }}>
                      Consent
                    </div>
                    <div style={{ fontSize: '13px', color: '#737373', marginTop: '4px' }}>
                      {toggleConsent ? 'Enabled' : 'Disabled'}
                    </div>
                  </div>

                  <Toggle
                    checked={toggleConsent}
                    disabled={loading || saving || currentConsent === null}
                    onClick={onToggleClick}
                  />
                </div>
              </div>

              {(statusMsg || errorMsg) && (
                <div
                  style={{
                    borderRadius: '12px',
                    padding: '12px 14px',
                    border: '1px solid #e5e5e5',
                    backgroundColor: errorMsg ? '#fff1f2' : '#ecfeff',
                    color: errorMsg ? '#991b1b' : '#0f766e',
                    fontSize: '13px',
                    lineHeight: 1.4,
                  }}
                >
                  {errorMsg || statusMsg}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Personal Info Card */}
        <div style={{ ...cardStyles, padding: '24px' }}>
          {/* Header Row */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: '16px',
              flexWrap: 'wrap',
              marginBottom: '18px',
            }}
          >
            <div style={{ minWidth: '260px', flex: 1 }}>
              <h2
                style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: '0 0 8px 0',
                }}
              >
                Personal Information
              </h2>
              <p style={{ fontSize: '14px', color: '#666', margin: 0, lineHeight: 1.5 }}>
                Save your personal details so Resume Generator can auto-fill them.
              </p>

              <div style={{ marginTop: '12px' }}>
                <span
                  style={{
                    fontSize: '13px',
                    fontWeight: 600,
                    color: loadingPersonalInfo
                      ? '#737373'
                      : hasAnyPersonalInfoSaved()
                      ? '#166534'
                      : '#991b1b',
                    backgroundColor: loadingPersonalInfo
                      ? '#f5f5f5'
                      : hasAnyPersonalInfoSaved()
                      ? '#dcfce7'
                      : '#fee2e2',
                    padding: '4px 10px',
                    borderRadius: '999px',
                    border: '1px solid #e5e5e5',
                    display: 'inline-block',
                  }}
                >
                  {loadingPersonalInfo
                    ? 'Loading…'
                    : hasAnyPersonalInfoSaved()
                    ? 'Saved'
                    : 'Not saved yet'}
                </span>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <button
                type="button"
                onClick={onClickRemovePersonalInfo}
                disabled={
                  loadingPersonalInfo ||
                  savingPersonalInfo ||
                  removingPersonalInfo ||
                  !hasAnyPersonalInfoSaved()
                }
                style={{
                  padding: '10px 14px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#ffffff',
                  color: '#991b1b',
                  fontWeight: 700,
                  cursor:
                    loadingPersonalInfo ||
                    savingPersonalInfo ||
                    removingPersonalInfo ||
                    !hasAnyPersonalInfoSaved()
                      ? 'not-allowed'
                      : 'pointer',
                  minWidth: '160px',
                }}
              >
                {removingPersonalInfo ? 'Removing…' : 'Remove Info'}
              </button>

              <button
                type="button"
                onClick={onSavePersonalInfo}
                disabled={
                  loadingPersonalInfo ||
                  savingPersonalInfo ||
                  removingPersonalInfo ||
                  !hasPersonalChanges
                }
                style={{
                  padding: '10px 14px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#111827',
                  color: '#ffffff',
                  fontWeight: 700,
                  cursor:
                    loadingPersonalInfo ||
                    savingPersonalInfo ||
                    removingPersonalInfo ||
                    !hasPersonalChanges
                      ? 'not-allowed'
                      : 'pointer',
                  minWidth: '190px',
                  transition: 'transform 0.05s ease',
                }}
                onMouseDown={(e) => {
                  e.currentTarget.style.transform = 'scale(0.98)';
                }}
                onMouseUp={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                {savingPersonalInfo ? 'Saving…' : personalButtonLabel}
              </button>
            </div>
          </div>

          {/* Divider */}
          <div style={{ height: '1px', backgroundColor: '#e5e5e5', marginBottom: '18px' }} />

          {/* Form Grid */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
              gap: '14px',
            }}
          >
            {/* Full Name (full width) */}
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={labelStyle}>Full Name</div>
              <input
                style={inputStyle}
                value={personalInfo.name}
                onChange={(e) => onChangePersonalField('name', e.target.value)}
                placeholder="Full Name"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>

            <div>
              <div style={labelStyle}>Email</div>
              <input
                style={inputStyle}
                value={personalInfo.email}
                onChange={(e) => onChangePersonalField('email', e.target.value)}
                placeholder="Email Address"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>

            <div>
              <div style={labelStyle}>Phone</div>
              <input
                style={inputStyle}
                value={personalInfo.phone}
                onChange={(e) => onChangePersonalField('phone', e.target.value)}
                placeholder="Phone Number"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>

            {/* Location (full width) */}
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={labelStyle}>Location</div>
              <input
                style={inputStyle}
                value={personalInfo.location}
                onChange={(e) => onChangePersonalField('location', e.target.value)}
                placeholder="Location (e.g., City, State)"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>

            <div>
              <div style={labelStyle}>LinkedIn</div>
              <input
                style={inputStyle}
                value={personalInfo.linkedIn}
                onChange={(e) => onChangePersonalField('linkedIn', e.target.value)}
                placeholder="LinkedIn URL"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>

            <div>
              <div style={labelStyle}>GitHub</div>
              <input
                style={inputStyle}
                value={personalInfo.github}
                onChange={(e) => onChangePersonalField('github', e.target.value)}
                placeholder="GitHub URL"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>

            {/* Website (full width) */}
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={labelStyle}>Website</div>
              <input
                style={inputStyle}
                value={personalInfo.website}
                onChange={(e) => onChangePersonalField('website', e.target.value)}
                placeholder="Personal Website"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>

            {/* Education (for PDF resume) */}
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={labelStyle}>Education (University)</div>
              <input
                style={inputStyle}
                value={personalInfo.education_university}
                onChange={(e) => onChangePersonalField('education_university', e.target.value)}
                placeholder="University Name"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={labelStyle}>Education (Location)</div>
              <input
                style={inputStyle}
                value={personalInfo.education_location}
                onChange={(e) => onChangePersonalField('education_location', e.target.value)}
                placeholder="City, State"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={labelStyle}>Education (Degree)</div>
              <input
                style={inputStyle}
                value={personalInfo.education_degree}
                onChange={(e) => onChangePersonalField('education_degree', e.target.value)}
                placeholder="e.g., B.S. Computer Science"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>
            <div>
              <div style={labelStyle}>Start Date</div>
              <input
                style={inputStyle}
                value={personalInfo.education_start_date}
                onChange={(e) => onChangePersonalField('education_start_date', e.target.value)}
                placeholder="e.g., Aug 2020"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>
            <div>
              <div style={labelStyle}>End Date</div>
              <input
                style={inputStyle}
                value={personalInfo.education_end_date}
                onChange={(e) => onChangePersonalField('education_end_date', e.target.value)}
                placeholder="e.g., May 2024"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>
            <div style={{ gridColumn: '1 / -1' }}>
              <div style={labelStyle}>Education (Awards)</div>
              <input
                style={inputStyle}
                value={personalInfo.education_awards}
                onChange={(e) => onChangePersonalField('education_awards', e.target.value)}
                placeholder="e.g., Dean's List, Scholarship Name"
                disabled={loadingPersonalInfo || savingPersonalInfo || removingPersonalInfo}
              />
            </div>
          </div>

          {/* Status messages */}
          {(personalStatusMsg || personalErrorMsg) && (
            <div
              style={{
                marginTop: '16px',
                borderRadius: '12px',
                padding: '12px 14px',
                border: '1px solid #e5e5e5',
                backgroundColor: personalErrorMsg ? '#fff1f2' : '#ecfeff',
                color: personalErrorMsg ? '#991b1b' : '#0f766e',
                fontSize: '13px',
                lineHeight: 1.4,
              }}
            >
              {personalErrorMsg || personalStatusMsg}
            </div>
          )}
        </div>

        {/* Change Password Card */}
        <div style={{ ...cardStyles, padding: '24px', marginTop: '20px' }}>
          <div style={{ marginBottom: '18px' }}>
            <h2
              style={{
                fontSize: '18px',
                fontWeight: '600',
                color: '#1a1a1a',
                margin: '0 0 8px 0',
              }}
            >
              Change Password
            </h2>
            <p style={{ fontSize: '14px', color: '#666', margin: 0, lineHeight: 1.5 }}>
              Update your password to keep your account secure.
            </p>
          </div>

          {/* Divider */}
          <div style={{ height: '1px', backgroundColor: '#e5e5e5', marginBottom: '18px' }} />

          {/* Password Form */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(1, minmax(0, 1fr))',
              gap: '14px',
              maxWidth: '500px',
            }}
          >
            <div>
              <div style={labelStyle}>Current Password</div>
              <input
                type="password"
                style={inputStyle}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                placeholder="Enter current password"
                disabled={changingPassword}
              />
            </div>

            <div>
              <div style={labelStyle}>New Password</div>
              <input
                type="password"
                style={inputStyle}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password (min. 6 characters)"
                disabled={changingPassword}
              />
            </div>

            <div>
              <div style={labelStyle}>Confirm New Password</div>
              <input
                type="password"
                style={inputStyle}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
                disabled={changingPassword}
              />
            </div>

            <div style={{ marginTop: '8px' }}>
              <button
                type="button"
                onClick={onChangePassword}
                disabled={changingPassword}
                style={{
                  padding: '10px 20px',
                  borderRadius: '12px',
                  border: 'none',
                  backgroundColor: '#111827',
                  color: '#ffffff',
                  fontWeight: 700,
                  cursor: changingPassword ? 'not-allowed' : 'pointer',
                  fontSize: '14px',
                  opacity: changingPassword ? 0.6 : 1,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (!changingPassword) {
                    e.currentTarget.style.backgroundColor = '#1f2937';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = '#111827';
                }}
              >
                {changingPassword ? 'Changing Password...' : 'Change Password'}
              </button>
            </div>
          </div>

          {(passwordStatusMsg || passwordErrorMsg) && (
            <div
              style={{
                marginTop: '16px',
                borderRadius: '12px',
                padding: '12px 14px',
                border: '1px solid #e5e5e5',
                backgroundColor: passwordErrorMsg ? '#fff1f2' : '#ecfeff',
                color: passwordErrorMsg ? '#991b1b' : '#0f766e',
                fontSize: '13px',
                lineHeight: 1.4,
              }}
            >
              {passwordErrorMsg || passwordStatusMsg}
            </div>
          )}
        </div>

        {/* Delete Account Card */}
        <div style={{ ...cardStyles, padding: '24px', marginTop: '20px' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start',
              gap: '16px',
              flexWrap: 'wrap',
            }}
          >
            <div style={{ flex: 1, minWidth: '260px' }}>
              <h2
                style={{
                  fontSize: '18px',
                  fontWeight: '600',
                  color: '#1a1a1a',
                  margin: '0 0 8px 0',
                }}
              >
                Delete Account
              </h2>

              <p style={{ fontSize: '14px', color: '#666', margin: 0, lineHeight: 1.5 }}>
                Permanently delete your account and all associated data, including your
                projects, analyses, saved resumes, personal info, and consent settings.
                This action cannot be undone.
              </p>
            </div>

            <div>
              <button
                type="button"
                onClick={onClickDeleteAccount}
                disabled={
                  deletingAccount ||
                  loading ||
                  saving ||
                  loadingPersonalInfo ||
                  savingPersonalInfo ||
                  removingPersonalInfo
                }
                style={{
                  padding: '10px 14px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#991b1b',
                  color: '#ffffff',
                  fontWeight: 700,
                  cursor:
                    deletingAccount ||
                    loading ||
                    saving ||
                    loadingPersonalInfo ||
                    savingPersonalInfo ||
                    removingPersonalInfo
                      ? 'not-allowed'
                      : 'pointer',
                  minWidth: '170px',
                }}
              >
                {deletingAccount ? 'Deleting…' : 'Delete Account'}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            zIndex: 9999,
          }}
          onClick={onCancelChange}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '520px',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #e5e5e5',
              boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
              padding: '18px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ marginBottom: '12px' }}>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#111827' }}>
                Are you sure?
              </h3>
              <p
                style={{
                  margin: '8px 0 0 0',
                  fontSize: '14px',
                  color: '#4b5563',
                  lineHeight: 1.5,
                }}
              >
                You are about to{' '}
                <span style={{ fontWeight: 700 }}>{pendingConsent ? 'enable' : 'disable'}</span>{' '}
                consent for LLM-related analysis features. Do you want to continue?
              </p>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: '10px',
                marginTop: '16px',
              }}
            >
              <button
                type="button"
                onClick={onCancelChange}
                disabled={saving}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#ffffff',
                  color: '#111827',
                  fontWeight: 600,
                  cursor: saving ? 'not-allowed' : 'pointer',
                }}
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={onConfirmChange}
                disabled={saving}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#111827',
                  color: '#ffffff',
                  fontWeight: 600,
                  cursor: saving ? 'not-allowed' : 'pointer',
                }}
              >
                {saving ? 'Saving…' : 'Yes, update'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* End Confirmation Modal */}

      {/* Remove Personal Info Confirmation Modal */}
      {showRemoveConfirm && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            zIndex: 9999,
          }}
          onClick={onCancelRemovePersonalInfo}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '520px',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #e5e5e5',
              boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
              padding: '18px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ marginBottom: '12px' }}>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#111827' }}>
                Remove personal info?
              </h3>
              <p
                style={{
                  margin: '8px 0 0 0',
                  fontSize: '14px',
                  color: '#4b5563',
                  lineHeight: 1.5,
                }}
              >
                This will permanently remove your saved personal info from the database. You can
                add it again anytime.
              </p>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: '10px',
                marginTop: '16px',
              }}
            >
              <button
                type="button"
                onClick={onCancelRemovePersonalInfo}
                disabled={removingPersonalInfo}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#ffffff',
                  color: '#111827',
                  fontWeight: 600,
                  cursor: removingPersonalInfo ? 'not-allowed' : 'pointer',
                }}
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={onConfirmRemovePersonalInfo}
                disabled={removingPersonalInfo}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#991b1b',
                  color: '#ffffff',
                  fontWeight: 600,
                  cursor: removingPersonalInfo ? 'not-allowed' : 'pointer',
                }}
              >
                {removingPersonalInfo ? 'Removing…' : 'Yes, remove'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* End Remove Personal Info Confirmation Modal */}

      {/* Delete Account Confirmation Modal */}
      {showDeleteAccountConfirm && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(0,0,0,0.35)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '24px',
            zIndex: 9999,
          }}
          onClick={onCancelDeleteAccount}
        >
          <div
            style={{
              width: '100%',
              maxWidth: '520px',
              backgroundColor: '#ffffff',
              borderRadius: '16px',
              border: '1px solid #e5e5e5',
              boxShadow: '0 10px 25px rgba(0,0,0,0.15)',
              padding: '18px',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ marginBottom: '12px' }}>
              <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#111827' }}>
                Delete account?
              </h3>
              <p
                style={{
                  margin: '8px 0 0 0',
                  fontSize: '14px',
                  color: '#4b5563',
                  lineHeight: 1.5,
                }}
              >
                This will permanently delete your account and everything associated with it.
                This action cannot be undone.
              </p>
            </div>

            <div
              style={{
                display: 'flex',
                justifyContent: 'flex-end',
                gap: '10px',
                marginTop: '16px',
              }}
            >
              <button
                type="button"
                onClick={onCancelDeleteAccount}
                disabled={deletingAccount}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#ffffff',
                  color: '#111827',
                  fontWeight: 600,
                  cursor: deletingAccount ? 'not-allowed' : 'pointer',
                }}
              >
                Cancel
              </button>

              <button
                type="button"
                onClick={onConfirmDeleteAccount}
                disabled={deletingAccount}
                style={{
                  padding: '10px 12px',
                  borderRadius: '12px',
                  border: '1px solid #e5e5e5',
                  backgroundColor: '#991b1b',
                  color: '#ffffff',
                  fontWeight: 600,
                  cursor: deletingAccount ? 'not-allowed' : 'pointer',
                }}
              >
                {deletingAccount ? 'Deleting…' : 'Yes, delete'}
              </button>
            </div>
          </div>
        </div>
      )}
      {/* End Delete Account Confirmation Modal */}
    </div>
  );
};

export default Settings;