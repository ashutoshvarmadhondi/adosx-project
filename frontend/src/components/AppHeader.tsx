import { LogOut, ShieldCheck, User } from "lucide-react";

import type { AuthUser } from "../types/api";

type AppHeaderProps = {
  user?: AuthUser | null;
  onLogout?: () => void;
  isLoggingOut?: boolean;
};

export default function AppHeader({
  user,
  onLogout,
  isLoggingOut = false,
}: AppHeaderProps) {
  return (
    <header className="app-header">
      <div className="app-header-content">
        <div className="header-brand">
          <div className="header-brand-icon">
            <ShieldCheck size={22} />
          </div>

          <div>
            <strong>ReconGuard</strong>
            <span>Reconciliation Intelligence</span>
          </div>
        </div>

        {user && onLogout ? (
          <div className="header-user-area">
            <div className="header-user">
              <div className="header-user-icon">
                <User size={17} />
              </div>

              <div>
                <strong>{user.username}</strong>
                <span>{user.organization_name}</span>
              </div>
            </div>

            <button
              type="button"
              className="header-logout-button"
              onClick={onLogout}
              disabled={isLoggingOut}
            >
              <LogOut size={17} />
              {isLoggingOut ? "Logging out..." : "Logout"}
            </button>
          </div>
        ) : (
          <span className="header-security-label">
            Tenant-secured workspace
          </span>
        )}
      </div>
    </header>
  );
}