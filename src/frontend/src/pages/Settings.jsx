import Navigation from '../components/Navigation';

const Settings = () => {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#fafafa',
    }}>
      <Navigation />

      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        padding: '48px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: 'calc(100vh - 100px)',
      }}>
        <div style={{
          textAlign: 'center',
        }}>
          <h1 style={{
            fontSize: '48px',
            fontWeight: '600',
            color: '#1a1a1a',
            margin: '0 0 16px 0',
            letterSpacing: '-0.5px'
          }}>
            Settings
          </h1>
          <p style={{
            fontSize: '18px',
            color: '#737373',
            margin: 0
          }}>
            This is the Settings page
          </p>
        </div>
      </div>
    </div>
  );
};

export default Settings;
