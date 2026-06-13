import { createTheme } from '@mui/material/styles';

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary:   { main: '#6366f1', light: '#818cf8', dark: '#4f46e5' },
    secondary: { main: '#e2b96f', light: '#f0d08a', dark: '#c99a50' },
    background: { default: '#0f0f1a', paper: '#1a1a2e' },
    success:   { main: '#22c55e' },
    warning:   { main: '#f59e0b' },
    error:     { main: '#ef4444' },
    info:      { main: '#3b82f6' },
    text:      { primary: '#f1f5f9', secondary: '#94a3b8' },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h4: { fontWeight: 700 },
    h5: { fontWeight: 600 },
    h6: { fontWeight: 600 },
  },
  shape: { borderRadius: 10 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: { backgroundImage: 'none', border: '1px solid rgba(255,255,255,0.06)' },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 600 },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: { fontWeight: 600, fontSize: '0.75rem' },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: { background: '#13131f', borderRight: '1px solid rgba(255,255,255,0.06)' },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: { background: '#13131f', boxShadow: 'none', borderBottom: '1px solid rgba(255,255,255,0.06)' },
      },
    },
  },
});

// Status chip colors
export const STATUS_COLORS: Record<string, 'default' | 'warning' | 'success' | 'error' | 'info' | 'secondary'> = {
  DRAFT:            'default',
  PENDING_APPROVAL: 'warning',
  APPROVED:         'success',
  REJECTED:         'error',
  DISPUTED:         'info',
  PUBLISHED:        'secondary',
};

export const ROLE_COLORS: Record<string, string> = {
  ADMIN:     '#ef4444',
  USER:      '#6366f1',
  APPROVER:  '#f59e0b',
  PUBLISHER: '#22c55e',
};
