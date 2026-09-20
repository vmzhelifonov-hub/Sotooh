import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./providers/AuthProvider";
import { ToastProvider } from "./providers/ToastProvider";
import { Toasts } from "./components/ui/Toasts";
import LandingPage from "./pages/LandingPage";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import OnboardingPage from "./pages/OnboardingPage";
import DashboardPage from "./pages/DashboardPage";
import CustomersPage from "./pages/CustomersPage";
import ProductsPage from "./pages/ProductsPage";
import QuotesPage from "./pages/QuotesPage";
import QuoteDetailPage from "./pages/QuoteDetailPage";
import SettingsPage from "./pages/SettingsPage";
import PublicQuotePage from "./pages/PublicQuotePage";
import { Spinner } from "./components/ui/DataDisplay";

function Protected({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  const location = useLocation();
  if (isLoading) return <Spinner />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/q/:token" element={<PublicQuotePage />} />

        <Route
          path="/onboarding"
          element={
            <Protected>
              <OnboardingPage />
            </Protected>
          }
        />
        <Route
          path="/app/*"
          element={
            <Protected>
              <AppLayout />
            </Protected>
          }
        />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toasts />
    </>
  );
}

import { Routes as LayoutRoutes } from "./appRoutes";

function AppLayout() {
  return <LayoutRoutes />;
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </ToastProvider>
  );
}

export { DashboardPage, CustomersPage, ProductsPage, QuotesPage, QuoteDetailPage, SettingsPage, OnboardingPage };
