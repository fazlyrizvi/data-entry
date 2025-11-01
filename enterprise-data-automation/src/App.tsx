import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { Navigation } from './components/Navigation'
import { WorkflowDashboard } from './components/dashboard/WorkflowDashboard'
import { FileUploadInterface } from './components/files/FileUploadInterface'
import { DataValidationInterface } from './components/validation/DataValidationInterface'
import { AnalyticsDashboard } from './components/analytics/AnalyticsDashboard'
import { NLCommandInterface } from './components/commands/NLCommandInterface'
import { AccessControlInterface } from './components/access/AccessControlInterface'
import { AIAnalysisInterface } from './components/ai/AIAnalysisInterface'
import { WorkflowBuilderInterface } from './components/workflows/WorkflowBuilderInterface'
import { DataFeedsInterface } from './components/feeds/DataFeedsInterface'

// Role-based route protection
const ProtectedRoute: React.FC<{ 
  children: React.ReactNode
  allowedRoles: string[]
}> = ({ children, allowedRoles }) => {
  const { user } = useAuth()
  
  if (!user) {
    return <Navigate to="/" replace />
  }
  
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}

const HomePage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <WorkflowDashboard />
      </main>
    </div>
  )
}

const FilesPage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <FileUploadInterface />
      </main>
    </div>
  )
}

const ValidationPage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DataValidationInterface />
      </main>
    </div>
  )
}

const AnalyticsPage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AnalyticsDashboard />
      </main>
    </div>
  )
}

const CommandsPage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <NLCommandInterface />
      </main>
    </div>
  )
}

const AccessPage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AccessControlInterface />
      </main>
    </div>
  )
}

const AIAnalysisPage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AIAnalysisInterface />
      </main>
    </div>
  )
}

const WorkflowBuilderPage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <WorkflowBuilderInterface />
      </main>
    </div>
  )
}

const DataFeedsPage: React.FC = () => {
  const { user } = useAuth()
  
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DataFeedsInterface />
      </main>
    </div>
  )
}

const App: React.FC = () => {
  return (
    <AuthProvider>
      <Router>
        <div className="App">
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route 
              path="/files" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <FilesPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/validation" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <ValidationPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/analytics" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager']}>
                  <AnalyticsPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/commands" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator', 'viewer']}>
                  <CommandsPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/access" 
              element={
                <ProtectedRoute allowedRoles={['admin']}>
                  <AccessPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/ai-analysis" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'analyst']}>
                  <AIAnalysisPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/workflows" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <WorkflowBuilderPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/data-feeds" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'analyst']}>
                  <DataFeedsPage />
                </ProtectedRoute>
              } 
            />
          </Routes>
          <Toaster 
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: 'rgba(255, 255, 255, 0.9)',
                backdropFilter: 'blur(20px)',
                border: '1px solid rgba(255, 255, 255, 0.3)',
                borderRadius: '12px',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.08)',
              },
              success: {
                iconTheme: {
                  primary: '#10B981',
                  secondary: '#ffffff',
                },
              },
              error: {
                iconTheme: {
                  primary: '#EF4444',
                  secondary: '#ffffff',
                },
              },
            }}
          />
        </div>
      </Router>
    </AuthProvider>
  )
}

export default App