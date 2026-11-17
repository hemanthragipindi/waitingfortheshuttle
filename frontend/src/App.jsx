import { Navigate, Route, Routes } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import { AuthProvider } from "./context/AuthContext.jsx";
import AppLayout from "./layouts/AppLayout.jsx";
import * as AdminPages from "./pages/AdminPages.jsx";
import DashboardPage from "./pages/DashboardPage.jsx";
import HomePage from "./pages/HomePage.jsx";
import LoginPage from "./pages/LoginPage.jsx";
import RegisterPage from "./pages/RegisterPage.jsx";
import * as StudentPages from "./pages/StudentPages.jsx";
import UnauthorizedPage from "./pages/UnauthorizedPage.jsx";

function Secure({ role, children }) {
  return <ProtectedRoute requiredRole={role}>{children}</ProtectedRoute>;
}

export default function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route element={<AppLayout />}>
          <Route index element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/admin/login" element={<LoginPage isAdmin />} />
          <Route path="/unauthorized" element={<UnauthorizedPage />} />

          <Route path="/student/dashboard" element={<Secure role="STUDENT"><DashboardPage /></Secure>} />
          <Route path="/student/stops" element={<Secure role="STUDENT"><StudentPages.Stops /></Secure>} />
          <Route path="/student/stops/:stopId" element={<Secure role="STUDENT"><StudentPages.StopDetails /></Secure>} />
          <Route path="/student/routes" element={<Secure role="STUDENT"><StudentPages.Routes /></Secure>} />
          <Route path="/student/routes/:routeId" element={<Secure role="STUDENT"><StudentPages.RouteDetails /></Secure>} />
          <Route path="/student/shuttles" element={<Secure role="STUDENT"><StudentPages.Shuttles /></Secure>} />
          <Route path="/student/shuttles/:shuttleId" element={<Secure role="STUDENT"><StudentPages.ShuttleDetails /></Secure>} />
          <Route path="/student/announcements" element={<Secure role="STUDENT"><StudentPages.Announcements /></Secure>} />
          <Route path="/student/feedback" element={<Secure role="STUDENT"><StudentPages.Feedback /></Secure>} />
          <Route path="/student/my-feedback" element={<Secure role="STUDENT"><StudentPages.MyFeedback /></Secure>} />
          <Route path="/student/profile" element={<Secure role="STUDENT"><StudentPages.Profile /></Secure>} />

          <Route path="/admin" element={<Secure role="ADMIN"><AdminPages.Dashboard /></Secure>} />
          <Route path="/admin/stops" element={<Secure role="ADMIN"><AdminPages.Stops /></Secure>} />
          <Route path="/admin/routes" element={<Secure role="ADMIN"><AdminPages.Routes /></Secure>} />
          <Route path="/admin/shuttles" element={<Secure role="ADMIN"><AdminPages.Shuttles /></Secure>} />
          <Route path="/admin/status" element={<Secure role="ADMIN"><AdminPages.Status /></Secure>} />
          <Route path="/admin/announcements" element={<Secure role="ADMIN"><AdminPages.Announcements /></Secure>} />
          <Route path="/admin/feedback" element={<Secure role="ADMIN"><AdminPages.Feedback /></Secure>} />
          <Route path="/admin/profile" element={<Secure role="ADMIN"><AdminPages.Profile /></Secure>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </AuthProvider>
  );
}
