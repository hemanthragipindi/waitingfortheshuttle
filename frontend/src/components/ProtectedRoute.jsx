import { Navigate, useLocation } from "react-router-dom";
import { Loading } from "./ui.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function ProtectedRoute({ requiredRole, children }) {
  const { user, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <Loading label="Checking your sign-in session" />;
  }

  if (!user) {
    const loginPath = requiredRole === "ADMIN" ? "/admin/login" : "/login";
    return <Navigate to={loginPath} state={{ from: location.pathname }} replace />;
  }

  if (requiredRole && user.role !== requiredRole) {
    return <Navigate to="/unauthorized" replace />;
  }

  return children;
}
