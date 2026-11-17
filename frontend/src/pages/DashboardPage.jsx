import { Overview } from "./StudentPages.jsx";
import { Dashboard as AdminDashboard } from "./AdminPages.jsx";

export default function DashboardPage({ isAdmin = false }) {
  return isAdmin ? <AdminDashboard /> : <Overview />;
}
