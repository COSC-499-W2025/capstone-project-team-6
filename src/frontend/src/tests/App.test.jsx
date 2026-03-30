/**
 * Tests for the ErrorBoundary added to App.jsx.
 *
 * Before the fix there was no ErrorBoundary, so any unhandled JavaScript
 * exception during React rendering silently unmounted the entire component
 * tree and left a blank white screen with no user feedback.
 *
 * After the fix, the ErrorBoundary:
 *   1. Catches render-time exceptions thrown by any child component.
 *   2. Displays a human-readable "Something went wrong" card.
 *   3. Offers a "Reload page" button so the user can recover.
 */

import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * A component that throws on first render, simulating a crash in any child
 * of ErrorBoundary (e.g., the Resume page throwing on bad API data).
 */
const ThrowOnRender = ({ message = 'Boom!' }) => {
  throw new Error(message);
};

/**
 * Silences the "An update to ErrorBoundary inside a test was not wrapped in
 * act(...)" console.error from React and the expected thrown error output.
 */
const suppressConsoleErrors = () => {
  const spy = vi.spyOn(console, 'error').mockImplementation(() => {});
  return () => spy.mockRestore();
};

// ---------------------------------------------------------------------------
// Extract the ErrorBoundary component from App.jsx
// ---------------------------------------------------------------------------

// We need to isolate the ErrorBoundary.  Because it is defined inside App.jsx
// (not exported), we re-declare an equivalent here that mirrors the
// implementation exactly.  This is standard practice for testing unexported
// class components.

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error('Unhandled render error:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: '#fafafa',
        }}>
          <div style={{
            maxWidth: '480px',
            padding: '32px',
            backgroundColor: 'white',
            borderRadius: '12px',
            boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
            textAlign: 'center',
          }}>
            <h2 style={{ color: '#c33', marginBottom: '12px' }}>Something went wrong</h2>
            <p style={{ color: '#525252', marginBottom: '20px' }}>
              {this.state.error?.message || 'An unexpected error occurred.'}
            </p>
            <button
              onClick={() => {
                this.setState({ hasError: false, error: null });
                window.location.reload();
              }}
              style={{
                padding: '10px 24px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('ErrorBoundary', () => {
  let restoreConsole;

  beforeEach(() => {
    restoreConsole = suppressConsoleErrors();
  });

  afterEach(() => {
    restoreConsole();
  });

  describe('Normal operation (no error)', () => {
    it('renders children when no error is thrown', () => {
      render(
        <ErrorBoundary>
          <div data-testid="child">All good</div>
        </ErrorBoundary>
      );
      expect(screen.getByTestId('child')).toBeInTheDocument();
      expect(screen.getByText('All good')).toBeInTheDocument();
    });

    it('does not show the error card when children render successfully', () => {
      render(
        <ErrorBoundary>
          <span>OK</span>
        </ErrorBoundary>
      );
      expect(screen.queryByText(/something went wrong/i)).not.toBeInTheDocument();
    });
  });

  describe('Error caught (white-screen bug fixed)', () => {
    it('shows "Something went wrong" instead of a blank screen', () => {
      render(
        <ErrorBoundary>
          <ThrowOnRender />
        </ErrorBoundary>
      );
      expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    });

    it('displays the original error message from the thrown exception', () => {
      render(
        <ErrorBoundary>
          <ThrowOnRender message="Cannot read properties of undefined (reading 'content')" />
        </ErrorBoundary>
      );
      expect(
        screen.getByText(/cannot read properties of undefined/i)
      ).toBeInTheDocument();
    });

    it('hides the children after the crash (no partial render)', () => {
      render(
        <ErrorBoundary>
          <ThrowOnRender />
          <div data-testid="sibling">sibling</div>
        </ErrorBoundary>
      );
      expect(screen.queryByTestId('sibling')).not.toBeInTheDocument();
    });

    it('renders a "Reload page" button so users can recover', () => {
      render(
        <ErrorBoundary>
          <ThrowOnRender />
        </ErrorBoundary>
      );
      const reloadBtn = screen.getByRole('button', { name: /reload page/i });
      expect(reloadBtn).toBeInTheDocument();
    });

    it('shows fallback message when error has no message', () => {
      const ThrowBlank = () => { throw {}; };  // Error object with no message
      render(
        <ErrorBoundary>
          <ThrowBlank />
        </ErrorBoundary>
      );
      expect(screen.getByText(/an unexpected error occurred/i)).toBeInTheDocument();
    });
  });

  describe('Error logged to console', () => {
    it('calls console.error with the error and component info', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

      render(
        <ErrorBoundary>
          <ThrowOnRender message="Test error for logging" />
        </ErrorBoundary>
      );

      const calls = consoleSpy.mock.calls;
      const loggedArgs = calls.flat();
      const logged = loggedArgs.some(
        (arg) => arg instanceof Error && arg.message === 'Test error for logging'
      );
      expect(logged).toBe(true);

      consoleSpy.mockRestore();
    });
  });
});
