import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { Suspense, lazy } from "react";
import { AuthProvider } from "@/context/AuthContext";
import { ThemeProvider } from "@/context/ThemeContext";
import ProtectedRoute from "@/components/layout/ProtectedRoute";
import AuthLayout from "@/components/layout/AuthLayout";
import DashboardLayout from "@/layouts/DashboardLayout";
import Loader from "@/components/common/Loader";
import Login from "@/pages/auth/Login";
import Register from "@/pages/auth/Register";
import ForgotPassword from "@/pages/auth/ForgotPassword";
import ResetPassword from "@/pages/auth/ResetPassword";
import Dashboard from "@/pages/Dashboard";
import ResumeList from "@/pages/resume/ResumeList";
import UploadResume from "@/pages/resume/UploadResume";
import ResumeDetail from "@/pages/resume/ResumeDetail";
import NotFound from "@/pages/NotFound";

// Lazy-loaded: these are secondary-flow pages (not the first thing anyone
// hits after logging in) and recharts in particular is by far the heaviest
// dependency in the app. Keeping them out of the main bundle means the
// login/dashboard/resume-list flow every user hits stays fast.
const ResumeImprovement = lazy(() => import("@/pages/resume/ResumeImprovement"));
const CompareJobDescription = lazy(() => import("@/pages/ats/CompareJobDescription"));
const ATSResults = lazy(() => import("@/pages/ats/ATSResults"));
const StartInterview = lazy(() => import("@/pages/interview/StartInterview"));
const InterviewSession = lazy(() => import("@/pages/interview/InterviewSession"));
const PerformanceReport = lazy(() => import("@/pages/report/PerformanceReport"));

function Lazy({ children }) {
  return <Suspense fallback={<Loader fullScreen />}>{children}</Suspense>;
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route element={<AuthLayout />}>
              <Route path="/login" element={<Login />} />
              <Route path="/register" element={<Register />} />
              <Route path="/forgot-password" element={<ForgotPassword />} />
              <Route path="/reset-password" element={<ResetPassword />} />
            </Route>

            <Route element={<ProtectedRoute />}>
              <Route element={<DashboardLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/resume" element={<ResumeList />} />
                <Route path="/resume/upload" element={<UploadResume />} />
                <Route path="/resume/:resumeId" element={<ResumeDetail />} />
                <Route path="/resume/:resumeId/improve" element={<Lazy><ResumeImprovement /></Lazy>} />
                <Route path="/resume/:resumeId/compare" element={<Lazy><CompareJobDescription /></Lazy>} />
                <Route path="/resume/:resumeId/ats/:jobDescriptionId" element={<Lazy><ATSResults /></Lazy>} />
                <Route path="/interview/start/:resumeId" element={<Lazy><StartInterview /></Lazy>} />
                <Route path="/interview/:interviewId" element={<Lazy><InterviewSession /></Lazy>} />
                <Route path="/report" element={<Lazy><PerformanceReport /></Lazy>} />
              </Route>
            </Route>

            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </ThemeProvider>
  );
}
