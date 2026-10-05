import { NavLink, useLocation, useNavigate } from "react-router-dom";

import { useAuth } from "../auth/AuthContext";
import type { ReactNode } from "react";

export function AppLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const isAccountPage = ["/login", "/register"].includes(location.pathname);

  function handleLogout() {
    logout();
    navigate("/login");
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink className="brand" to="/dashboard" aria-label="CloudPilot home">
          <span className="brand-mark" aria-hidden="true">C</span>
          <span>CloudPilot</span>
        </NavLink>
        {!isAccountPage && (
          <nav className="main-nav" aria-label="Main navigation">
            <NavLink
              to="/dashboard"
              className={({ isActive }) => `nav-link${isActive ? " active" : ""}`}
            >
              Overview
            </NavLink>
            <span className="nav-link nav-link-muted" aria-disabled="true">Resources</span>
            <span className="nav-link nav-link-muted" aria-disabled="true">Recommendations</span>
          </nav>
        )}
        <div className="topbar-actions">
          {isAuthenticated ? (
            <button className="text-button" type="button" onClick={handleLogout}>
              Sign out
            </button>
          ) : (
            <NavLink className="text-button" to="/login">Sign in</NavLink>
          )}
        </div>
      </header>
      <main className="main-content">{children}</main>
      <footer className="footer">
        <span>CloudPilot</span>
        <span>FinOps workspace</span>
      </footer>
    </div>
  );
}