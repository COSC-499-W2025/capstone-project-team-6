import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Navigation from '../components/Navigation';
import { consentAPI } from '../services/api';

const Settings = () => {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Current saved value from DB
  const [currentConsent, setCurrentConsent] = useState(null); // true/false when loaded

  // What the toggle UI currently shows
  const [toggleConsent, setToggleConsent] = useState(false);

  // Confirmation modal state
  const [showConfirm, setShowConfirm] = useState(false);
  const [pendingConsent, setPendingConsent] = useState(null); // the value user is trying to change to

  const [statusMsg, setStatusMsg] = useState('');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    const loadConsent = async () => {
      setLoading(true);
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
      } finally {
        setLoading(false);
      }
    };

    loadConsent();
  }, []);

  const consentLabel =
    currentConsent === null ? 'Unknown' : currentConsent ? 'Consented' : 'Not Consented';

  // User clicks toggle => we DO NOT save immediately.
  // We open confirmation modal first.
  const onToggleClick = () => {
    if (loading || saving || currentConsent === null) return;

    const nextValue = !toggleConsent;
    setPendingConsent(nextValue);
    setShowConfirm(true);
  };

  const onCancelChange = () => {
    // Revert UI back to the saved value
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

      // Save succeeded => reflect new saved state + UI
      setCurrentConsent(updated);
      setToggleConsent(updated);

      setStatusMsg(res?.message || 'Consent updated successfully.');
    } catch (err) {
      // Save failed => revert UI back to saved state
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

  // A simple toggle switch (no external libs)
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

  // --- Shared styles to match your Projects/Dashboard look ---
  const pageStyles = {
    minHeight: '100vh',
    backgroundColor: '#fafafa',
  };

  const containerStyles = {
    maxWidth: '1100px',
    margin: '0 auto',
    padding: '48px 32px',
  };

  const cardStyles = {
    backgroundColor: 'white',
    border: '1px solid #e5e5e5',
    borderRadius: '16px',
  };

  const secondaryText = { color: '#737373' };
  const headingText = { color: '#1a1a1a' };

  return (
    <div style={pageStyles}>
      <Navigation />

      <div style={containerStyles}>
        {/* Header (Dashboard-style) */}
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

          {/* ✅ Exact same back button (copied style + hover handlers) */}
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

        {/* Consent Card */}
        <div style={{ ...cardStyles, padding: '24px' }}>
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
    </div>
  );
};

export default Settings;
