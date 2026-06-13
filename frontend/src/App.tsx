import React, { useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Provider } from 'react-redux';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import { store } from './store';
import { fetchMe } from './store';
import { theme } from './theme';
import { useAuth, useAppDispatch } from './hooks/useAuth';
import { tokenStorage } from './services/api';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { ArticlesPage } from './pages/ArticlesPage';
import { UserManagementPage } from './pages/admin/UserManagementPage';
import { AuditLogsPage } from './pages/admin/AuditLogsPage';

// ─── Route guards ──────────────────────────────────────────────────────────────
const RequireAuth: React.FC<{ children: React.ReactNode; roles?: string[] }> = ({ children, roles }) => {
  const { user, hasRole } = useAuth();
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (!user && tokenStorage.getAccess()) {
      dispatch(fetchMe());
    }
  }, []);

  if (!user && !tokenStorage.getAccess()) {
    return <Navigate to="/login" replace />;
  }
  if (roles && user && !roles.some((r) => hasRole(r as any))) {
    return <Navigate to="/dashboard" replace />;
  }
  return <AppLayout>{children}</AppLayout>;
};

// ─── Lazy placeholder pages ────────────────────────────────────────────────────
const Placeholder: React.FC<{ title: string }> = ({ title }) => (
  <div style={{ padding: 32 }}>
    <h2 style={{ color: '#94a3b8' }}>{title}</h2>
    <p style={{ color: '#64748b' }}>This page is under construction.</p>
  </div>
);

// ─── App Bootstrap ────────────────────────────────────────────────────────────
const AppRoutes: React.FC = () => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    if (tokenStorage.getAccess()) dispatch(fetchMe());
  }, []);

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />

      {/* Dashboard */}
      <Route path="/dashboard" element={<RequireAuth><DashboardPage /></RequireAuth>} />

      {/* Articles */}
      <Route path="/articles" element={<RequireAuth><ArticlesPage /></RequireAuth>} />
      <Route path="/articles/mine" element={<RequireAuth roles={['USER']}><ArticlesPage /></RequireAuth>} />
      <Route path="/articles/new" element={<RequireAuth roles={['USER']}><Placeholder title="Generate / New Article" /></RequireAuth>} />
      <Route path="/articles/:id" element={<RequireAuth><Placeholder title="Article Detail" /></RequireAuth>} />

      {/* User flows */}
      <Route path="/articles/generate" element={<RequireAuth roles={['USER']}><Placeholder title="KBG Article Generator" /></RequireAuth>} />
      <Route path="/source-sync" element={<RequireAuth roles={['USER']}><Placeholder title="Source & Sync" /></RequireAuth>} />
      <Route path="/pipeline" element={<RequireAuth roles={['USER']}><Placeholder title="Pipeline Review" /></RequireAuth>} />

      {/* Approver */}
      <Route path="/approver/pending" element={<RequireAuth roles={['APPROVER', 'ADMIN']}><ArticlesPage /></RequireAuth>} />
      <Route path="/approver/approved" element={<RequireAuth roles={['APPROVER', 'ADMIN']}><ArticlesPage /></RequireAuth>} />
      <Route path="/approver/rejected" element={<RequireAuth roles={['APPROVER', 'ADMIN']}><ArticlesPage /></RequireAuth>} />

      {/* Publisher */}
      <Route path="/publisher/queue" element={<RequireAuth roles={['PUBLISHER', 'ADMIN']}><ArticlesPage /></RequireAuth>} />
      <Route path="/publisher/published" element={<RequireAuth roles={['PUBLISHER', 'ADMIN']}><ArticlesPage /></RequireAuth>} />

      {/* Admin */}
      <Route path="/admin/users" element={<RequireAuth roles={['ADMIN']}><UserManagementPage /></RequireAuth>} />
      <Route path="/admin/audit" element={<RequireAuth roles={['ADMIN']}><AuditLogsPage /></RequireAuth>} />
      <Route path="/admin/stats" element={<RequireAuth roles={['ADMIN']}><Placeholder title="Platform Statistics" /></RequireAuth>} />
      <Route path="/notifications" element={<RequireAuth><Placeholder title="Notifications" /></RequireAuth>} />

      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

const App: React.FC = () => (
  <Provider store={store}>
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
      <ToastContainer
        position="bottom-right"
        theme="dark"
        toastStyle={{ background: '#1a1a2e', border: '1px solid rgba(255,255,255,0.1)' }}
      />
    </ThemeProvider>
  </Provider>
);

export default App;
