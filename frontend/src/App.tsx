import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ThemeProvider } from './context/ThemeContext';
import { Layout } from './components/layout/Layout';

// Lazy load page components for code splitting
const Landing = lazy(() => import('./pages/Landing').then(m => ({ default: m.Landing })));
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })));
const Practice = lazy(() => import('./pages/Practice').then(m => ({ default: m.Practice })));
const Feedback = lazy(() => import('./pages/Feedback').then(m => ({ default: m.Feedback })));
const Roleplay = lazy(() => import('./pages/Roleplay').then(m => ({ default: m.Roleplay })));
const Progress = lazy(() => import('./pages/Progress').then(m => ({ default: m.Progress })));
const History = lazy(() => import('./pages/History').then(m => ({ default: m.History })));
const PracticeSessionDetail = lazy(() => import('./pages/PracticeSessionDetail').then(m => ({ default: m.PracticeSessionDetail })));
const RoleplaySessionDetail = lazy(() => import('./pages/RoleplaySessionDetail').then(m => ({ default: m.RoleplaySessionDetail })));
const Settings = lazy(() => import('./pages/Settings'));

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="h-screen w-screen flex items-center justify-center bg-background text-textSecondary font-serif">Loading Eloq...</div>;
  if (!user) return <Navigate to="/" replace />;
  return <Suspense fallback={<div className="h-screen w-screen flex items-center justify-center bg-background text-textSecondary font-serif">Loading...</div>}>{children}</Suspense>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="h-screen w-screen flex items-center justify-center bg-background text-textSecondary font-serif">Loading Eloq...</div>;
  if (user) return <Navigate to="/app/practice" replace />;
  return <Suspense fallback={<div className="h-screen w-screen flex items-center justify-center bg-background text-textSecondary font-serif">Loading...</div>}>{children}</Suspense>;
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            {/* Public routes */}
            <Route path="/" element={
              <PublicRoute>
                <Landing />
              </PublicRoute>
            } />
            <Route path="/login" element={
              <PublicRoute>
                <Login />
              </PublicRoute>
            } />
            
            {/* Protected routes */}
            <Route
              path="/app"
              element={
                <RequireAuth>
                  <Layout />
                </RequireAuth>
              }
            >
              <Route index element={<Navigate to="/app/practice" replace />} />
              <Route path="practice" element={<Practice />} />
              <Route path="feedback/:id" element={<Feedback />} />
              <Route path="roleplay" element={<Roleplay />} />
              <Route path="progress" element={<Progress />} />
              <Route path="history" element={<History />} />
              <Route path="history/practice/:sessionId" element={<PracticeSessionDetail />} />
              <Route path="history/roleplay/:sessionId" element={<RoleplaySessionDetail />} />
              <Route path="settings" element={<Settings />} />
            </Route>
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}
