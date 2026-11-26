import {
  Bell,
  BusFront,
  ChevronDown,
  ClipboardList,
  LayoutDashboard,
  LogOut,
  MapPin,
  Menu,
  MessageSquareText,
  Route as RouteIcon,
  Settings,
  ShieldCheck,
  UserRound,
  X,
} from "lucide-react";
import { useState } from "react";
import { Link, NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const studentLinks = [
  { to: "/student/dashboard", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/student/stops", label: "Campus stops", icon: MapPin },
  { to: "/student/routes", label: "Shuttle routes", icon: RouteIcon },
  { to: "/student/shuttles", label: "Shuttle information", icon: BusFront },
  { to: "/student/announcements", label: "Announcements", icon: Bell },
  { to: "/student/feedback", label: "Send feedback", icon: MessageSquareText },
  { to: "/student/my-feedback", label: "My feedback", icon: ClipboardList },
  { to: "/student/profile", label: "My profile", icon: UserRound },
];

const adminLinks = [
  { to: "/admin", label: "Overview", icon: LayoutDashboard, end: true },
  { to: "/admin/stops", label: "Stops", icon: MapPin },
  { to: "/admin/routes", label: "Routes", icon: RouteIcon },
  { to: "/admin/shuttles", label: "Shuttles", icon: BusFront },
  { to: "/admin/status", label: "Service status", icon: Settings },
  { to: "/admin/announcements", label: "Announcements", icon: Bell },
  { to: "/admin/feedback", label: "Feedback", icon: MessageSquareText },
  { to: "/admin/profile", label: "Administrator profile", icon: ShieldCheck },
];

export default function AppLayout() {
  const { user, logout, authError } = useAuth();
  const [logoutError, setLogoutError] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const isAdmin = user?.role === "ADMIN";
  const links = isAdmin ? adminLinks : studentLinks;
  const dashboardPath = isAdmin ? "/admin" : "/student/dashboard";

  async function handleLogout() {
    setLogoutError("");
    try {
      await logout();
      setMenuOpen(false);
      navigate("/", { replace: true });
    } catch {
      setLogoutError("Sign out could not reach the server. Please try again.");
    }
  }

  const publicNav = !user && (
    <div className="public-nav">
      <Link to="/student/stops">Campus stops</Link>
      <Link to="/student/routes">Routes</Link>
      <Link to="/student/shuttles">Shuttles</Link>
      <Link to="/student/announcements">Announcements</Link>
      <Link to="/login">Student sign in</Link>
      <Link to="/admin/login">Admin</Link>
      <Link className="button button--primary public-nav__cta" to="/register">Create account</Link>
    </div>
  );

  return (
    <div className="app-shell">
      <header className="topbar">
        <Link className="brand" to="/" aria-label="Waiting for the Shuttle home">
          <span className="brand__icon"><BusFront size={20} aria-hidden="true" /></span>
          <span className="brand__name">Waiting for the Shuttle</span>
        </Link>
        {user ? (
          <>
            <button
              type="button"
              className="mobile-menu-button"
              aria-expanded={menuOpen}
              aria-controls="portal-navigation"
              onClick={() => setMenuOpen((open) => !open)}
            >
              {menuOpen ? <X size={20} /> : <Menu size={20} />}
              <span>{menuOpen ? "Close menu" : "Menu"}</span>
            </button>
            <div className="topbar__account">
              <span className="topbar__account-name">{user.full_name}</span>
              <span className="topbar__avatar">{user.full_name?.trim().charAt(0).toUpperCase() || "U"}</span>
              <button type="button" className="icon-button" aria-label="Sign out" onClick={handleLogout}>
                <LogOut size={17} />
              </button>
            </div>
          </>
        ) : publicNav}
      </header>

      {user ? (
        <div className="portal">
          <aside className={`sidebar ${menuOpen ? "sidebar--open" : ""}`} id="portal-navigation">
            <div className="sidebar__workspace">
              <span className={`sidebar__role-icon ${isAdmin ? "sidebar__role-icon--admin" : ""}`}>
                {isAdmin ? <ShieldCheck size={17} /> : <BusFront size={17} />}
              </span>
              <span><strong>{isAdmin ? "Transport team" : "Campus transit"}</strong><small>{isAdmin ? "Administration" : "Student portal"}</small></span>
              <ChevronDown size={15} aria-hidden="true" />
            </div>
            <p className="sidebar__section-label">WORKSPACE</p>
            <nav className="sidebar__nav" aria-label={isAdmin ? "Administrator navigation" : "Student navigation"}>
              {links.map(({ to, label, icon: Icon, end }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={({ isActive }) => `sidebar__link${isActive ? " is-active" : ""}`}
                  onClick={() => setMenuOpen(false)}
                >
                  <Icon size={17} aria-hidden="true" />
                  <span>{label}</span>
                </NavLink>
              ))}
            </nav>
            <div className="sidebar__note">
              <span className="sidebar__note-icon"><MessageSquareText size={16} /></span>
              <p>Have an issue with service?<Link to={isAdmin ? "/admin/feedback" : "/student/feedback"} onClick={() => setMenuOpen(false)}>{isAdmin ? "Review feedback" : "Send feedback"}</Link></p>
            </div>
            <div className="sidebar__bottom">
              <span className="sidebar__university">LOVELY PROFESSIONAL UNIVERSITY</span>
              <button type="button" className="sidebar__signout" onClick={handleLogout}><LogOut size={16} /> Sign out</button>
            </div>
          </aside>
          <main className="portal-main">
            <div className="portal-breadcrumb">
              <Link to={dashboardPath}>{isAdmin ? "Admin" : "Student portal"}</Link>
              <span>/</span>
              <span>{links.find((item) => item.to === location.pathname)?.label || "Page"}</span>
            </div>
            {(authError || logoutError) && <div className="global-alert" role="alert">{authError || logoutError}</div>}
            <Outlet />
            <footer className="portal-footer">
              <span>Waiting for the Shuttle · Campus shuttle information</span>
              <span>Service updates are manually reported. No live tracking is provided.</span>
            </footer>
          </main>
        </div>
      ) : (
        <>
          {logoutError && <div className="global-alert" role="alert">{logoutError}</div>}
          <Outlet />
          <footer className="public-footer">
            <span>Waiting for the Shuttle · Campus shuttle information</span>
            <span>Campus shuttle information for Lovely Professional University</span>
          </footer>
        </>
      )}
    </div>
  );
}
