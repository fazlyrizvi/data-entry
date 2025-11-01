import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { Navigation } from './components/Navigation'
import { LoginForm } from './components/auth/LoginForm'
import { SignupForm } from './components/auth/SignupForm'
import { WorkflowDashboard } from './components/dashboard/WorkflowDashboard'
import { FileUploadInterface } from './components/files/FileUploadInterface'
import { DataValidationInterface } from './components/validation/DataValidationInterface'
import { AnalyticsDashboard } from './components/analytics/AnalyticsDashboard'
import { NLCommandInterface } from './components/commands/NLCommandInterface'
import { AccessControlInterface } from './components/access/AccessControlInterface'
import { AIAnalysisInterface } from './components/ai/AIAnalysisInterface'
import { WorkflowBuilderInterface } from './components/workflows/WorkflowBuilderInterface'
import { DataFeedsInterface } from './components/feeds/DataFeedsInterface'

// Import new data automation components
import { DataEntryTemplateInterface } from './components/data-entry/DataEntryTemplateInterface'
import { OCRDocumentInterface } from './components/ocr/OCRDocumentInterface'
import { QualityControlDashboard } from './components/quality/QualityControlDashboard'
import { BatchProcessingInterface } from './components/batch/BatchProcessingInterface'
import { DataExportInterface } from './components/export/DataExportInterface'

// Import new comprehensive features
import DocumentProcessingInterface from './components/DocumentProcessingInterface'
import ValidationDashboard from './components/validation/ValidationDashboard'
import TemplateSelector from './components/templates/TemplateSelector'
import MedicalRecordsForm from './components/templates/MedicalRecordsForm'
import BatchUpload from './components/batch/BatchUpload'

// Role-based route protection
const ProtectedRoute: React.FC<{ 
  children: React.ReactNode
  allowedRoles: string[]
}> = ({ children, allowedRoles }) => {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-neutral-600">Loading...</p>
        </div>
      </div>
    )
  }
  
  if (!user) {
    return <Navigate to="/login" replace />
  }
  
  if (!allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}

// Public route wrapper - redirects authenticated users
const PublicRoute: React.FC<{ 
  children: React.ReactNode
}> = ({ children }) => {
  const { user, loading } = useAuth()
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500 mx-auto mb-4"></div>
          <p className="text-neutral-600">Loading...</p>
        </div>
      </div>
    )
  }
  
  if (user) {
    return <Navigate to="/" replace />
  }
  
  return <>{children}</>
}

const HomePage: React.FC = () => {
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
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DataFeedsInterface />
      </main>
    </div>
  )
}

// New Comprehensive Data Automation Pages
const DocumentProcessingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DocumentProcessingInterface />
      </main>
    </div>
  )
}

const DataValidationPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <ValidationDashboard />
      </main>
    </div>
  )
}

const TemplatesPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <TemplateSelector />
      </main>
    </div>
  )
}

const MedicalRecordsPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <MedicalRecordsForm />
      </main>
    </div>
  )
}

const BatchUploadPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <BatchUpload />
      </main>
    </div>
  )
}

// New Data Automation Pages
const DataEntryTemplatePage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DataEntryTemplateInterface />
      </main>
    </div>
  )
}

const OCRDocumentPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <OCRDocumentInterface />
      </main>
    </div>
  )
}

const QualityControlPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <QualityControlDashboard />
      </main>
    </div>
  )
}

const BatchProcessingPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <BatchProcessingInterface />
      </main>
    </div>
  )
}

const DataExportPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-neutral-50 via-neutral-100 to-primary-50">
      <Navigation />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DataExportInterface />
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
            {/* Auth Routes - Public */}
            <Route 
              path="/login" 
              element={
                <PublicRoute>
                  <LoginForm />
                </PublicRoute>
              } 
            />
            <Route 
              path="/signup" 
              element={
                <PublicRoute>
                  <SignupForm />
                </PublicRoute>
              } 
            />
            {/* Protected Routes */}
            <Route 
              path="/" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator', 'viewer']}>
                  <HomePage />
                </ProtectedRoute>
              } 
            />
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
                <ProtectedRoute allowedRoles={['admin', 'manager']}>
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
                <ProtectedRoute allowedRoles={['admin', 'manager']}>
                  <DataFeedsPage />
                </ProtectedRoute>
              } 
            />
            {/* New Data Automation Routes */}
            <Route 
              path="/data-entry" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <DataEntryTemplatePage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/ocr" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <OCRDocumentPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/quality-control" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager']}>
                  <QualityControlPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/batch-processing" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <BatchProcessingPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/data-export" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <DataExportPage />
                </ProtectedRoute>
              } 
            />
            {/* Enhanced New Data Automation Routes */}
            <Route 
              path="/document-processing" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <DocumentProcessingPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/data-validation" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <DataValidationPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/templates" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <TemplatesPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/medical-records" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <MedicalRecordsPage />
                </ProtectedRoute>
              } 
            />
            <Route 
              path="/batch-upload" 
              element={
                <ProtectedRoute allowedRoles={['admin', 'manager', 'operator']}>
                  <BatchUploadPage />
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