import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { consentAPI } from '../../services/api';

const ConsentPage = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleConsent = async (hasConsented) => {
    setLoading(true);
    setError('');

    try {
      await consentAPI.saveConsent(hasConsented);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to save consent');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#f5f5f5',
      padding: '20px'
    }}>
      <div style={{ marginBottom: '32px', textAlign: 'center' }}>
        <h1 style={{
          fontSize: '36px',
          fontWeight: 'bold',
          margin: '0 0 8px 0',
          color: '#1a1a1a'
        }}>
          Project Consent Form
        </h1>
        <p style={{
          fontSize: '16px',
          color: '#666',
          margin: 0
        }}>
          Mining Digital Work Artifacts
        </p>
      </div>

      <div style={{
        backgroundColor: 'white',
        padding: '48px',
        borderRadius: '12px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        width: '100%',
        maxWidth: '800px',
        maxHeight: '80vh',
        overflow: 'auto'
      }}>
        <div style={{
          fontFamily: 'monospace',
          fontSize: '13px',
          lineHeight: '1.6',
          color: '#1a1a1a',
          whiteSpace: 'pre-wrap',
          marginBottom: '32px'
        }}>
          <div style={{ borderBottom: '2px solid #e0e0e0', paddingBottom: '16px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0 }}>
              1. PURPOSE OF THE APPLICATION
            </h2>
          </div>
          <p style={{ margin: '0 0 24px 0' }}>
            This application analyzes a zipped project folder that you provide
            in order to generate summaries, metrics, and résumé-ready highlights.
          </p>
          <p style={{ margin: '0 0 24px 0' }}>
            The application offers TWO types of analysis:<br />
            <strong>A) LOCAL ANALYSIS (Default):</strong> All processing happens on your device.<br />
            <strong>B) AI-ENHANCED ANALYSIS (Optional):</strong> Uses Google Gemini API for
            advanced insights. Requires separate consent (see below).
          </p>

          <div style={{ borderBottom: '2px solid #e0e0e0', paddingBottom: '16px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0 }}>
              2. SCOPE OF DATA ACCESS
            </h2>
          </div>
          <p style={{ margin: '0 0 16px 0' }}>
            When you upload a ZIP file, the app will only access the contents
            within that ZIP. It will not scan or access any other files or
            directories on your device.
          </p>
          <p style={{ margin: '0 0 24px 0' }}>
            The application may extract and process the following:
          </p>
          <ul style={{ margin: '0 0 24px 20px', padding: 0 }}>
            <li>File metadata (names, sizes, timestamps, types)</li>
            <li>Readable text (e.g., README files, notes, documentation, comments)</li>
            <li>Programming code (for classification and metrics)</li>
            <li>Image metadata (for creative project context)</li>
          </ul>

          <div style={{ borderBottom: '2px solid #e0e0e0', paddingBottom: '16px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0 }}>
              3. LOCAL ANALYSIS (DEFAULT MODE)
            </h2>
          </div>
          <p style={{ margin: '0 0 16px 0' }}>
            The standard 'analyze' command performs all computations locally:
          </p>
          <p style={{ margin: '0 0 16px 0' }}>
            <strong>Features of Local Processing:</strong>
          </p>
          <ul style={{ margin: '0 0 16px 20px', padding: 0 }}>
            <li>No internet connection required.</li>
            <li>All analysis (OOP metrics, complexity, git history, etc.) runs
              entirely on your device using Python AST parsers and static
              analysis tools.</li>
            <li>No data transmission to external servers.</li>
          </ul>
          <p style={{ margin: '0 0 16px 0' }}>
            <strong>Privacy Considerations:</strong>
          </p>
          <ul style={{ margin: '0 0 24px 20px', padding: 0 }}>
            <li>Your data never leaves your device during local analysis.</li>
            <li>No external APIs or cloud-based services are contacted.</li>
            <li>All logs and results remain local.</li>
          </ul>

          <div style={{ borderBottom: '2px solid #e0e0e0', paddingBottom: '16px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0 }}>
              4. DATA STORAGE
            </h2>
          </div>
          <p style={{ margin: '0 0 24px 0' }}>
            Stored locally on your device:
          </p>
          <ul style={{ margin: '0 0 24px 20px', padding: 0 }}>
            <li>SQLite database containing project metadata, metrics, summaries,
              and your consent record.</li>
            <li>Extracted text snippets used for analysis only.</li>
            <li>Timestamped consent log.</li>
          </ul>

          <div style={{ borderBottom: '2px solid #e0e0e0', paddingBottom: '16px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0 }}>
              5. DATA DELETION
            </h2>
          </div>
          <p style={{ margin: '0 0 16px 0' }}>
            You may delete stored data at any time from your account settings.
          </p>
          <p style={{ margin: '0 0 24px 0' }}>
            This action removes:
          </p>
          <ul style={{ margin: '0 0 24px 20px', padding: 0 }}>
            <li>All local databases, caches, summaries, and consent records.</li>
            <li>Any temporary extracted files or logs generated during processing.</li>
          </ul>

          <div style={{ borderBottom: '2px solid #e0e0e0', paddingBottom: '16px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0 }}>
              6. VOLUNTARY PARTICIPATION
            </h2>
          </div>
          <p style={{ margin: '0 0 24px 0' }}>
            Your participation and data submission are voluntary. You may withdraw
            consent at any time through your account settings.
            After withdrawal, the application will cease all data analysis and
            delete existing data if requested.
          </p>

          <div style={{ borderBottom: '2px solid #e0e0e0', paddingBottom: '16px', marginBottom: '24px' }}>
            <h2 style={{ fontSize: '16px', fontWeight: 'bold', margin: 0 }}>
              7. CONSENT DECISION
            </h2>
          </div>
          <div style={{
            backgroundColor: '#f0f9ff',
            border: '2px solid #2563EB',
            borderRadius: '8px',
            padding: '20px',
            margin: '0 0 24px 0'
          }}>
            <p style={{ margin: 0, fontWeight: 'bold' }}>
              I consent to the app analyzing my uploaded ZIP files locally.<br />
              I understand that this consent covers LOCAL analysis only.<br />
              AI-enhanced analysis (Google Gemini) requires separate consent.
            </p>
          </div>
        </div>

        {error && (
          <div style={{
            padding: '12px',
            marginBottom: '24px',
            backgroundColor: '#FEE2E2',
            border: '1px solid #EF4444',
            borderRadius: '8px',
            color: '#DC2626',
            fontSize: '14px'
          }}>
            {error}
          </div>
        )}

        <div style={{
          display: 'flex',
          gap: '16px',
          justifyContent: 'center'
        }}>
          <button
            onClick={() => handleConsent(false)}
            disabled={loading}
            style={{
              padding: '14px 32px',
              fontSize: '16px',
              fontWeight: '600',
              color: '#1a1a1a',
              backgroundColor: 'white',
              border: '2px solid #e0e0e0',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s'
            }}
            onMouseEnter={(e) => !loading && (e.target.style.borderColor = '#1a1a1a')}
            onMouseLeave={(e) => !loading && (e.target.style.borderColor = '#e0e0e0')}
          >
            I Do Not Consent
          </button>

          <button
            onClick={() => handleConsent(true)}
            disabled={loading}
            style={{
              padding: '14px 32px',
              fontSize: '16px',
              fontWeight: '600',
              color: 'white',
              backgroundColor: loading ? '#94A3B8' : '#1a1a1a',
              border: 'none',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'background-color 0.2s'
            }}
            onMouseEnter={(e) => !loading && (e.target.style.backgroundColor = '#333')}
            onMouseLeave={(e) => !loading && (e.target.style.backgroundColor = '#1a1a1a')}
          >
            {loading ? 'Processing...' : 'I Consent'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConsentPage;
