import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import Loader from "@/components/common/Loader";

export default function ProtectedRoute() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <Loader fullScreen />;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <Outlet />;
}
