import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { LogOut, User as UserIcon, ChevronDown, FileText } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import ThemeToggle from "@/components/common/ThemeToggle";

export default function Navbar() {
  const { user, logout } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef(null);
  const triggerRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false);
      }
    }
    function handleKeyDown(event) {
      if (event.key === "Escape" && menuOpen) {
        setMenuOpen(false);
        triggerRef.current?.focus();
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [menuOpen]);

  const initials = (user?.name ?? "?")
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="sticky top-0 z-20 border-b border-hairline bg-ink/80 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <span className="font-display text-lg font-semibold text-ink-text">CareerAI</span>

        <nav className="hidden items-center gap-6 sm:flex">
          <Link to="/resume" className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
            <FileText className="h-4 w-4" /> Resumes
          </Link>
        </nav>

        <div className="flex items-center gap-3">
          <ThemeToggle />

          <div className="relative" ref={menuRef}>
            <button
              type="button"
              ref={triggerRef}
              onClick={() => setMenuOpen((v) => !v)}
              aria-haspopup="menu"
              aria-expanded={menuOpen}
              className="flex items-center gap-2 rounded-full border border-hairline py-1 pl-1 pr-3 text-sm text-ink-text transition-colors hover:border-signal"
            >
              <span className="flex h-7 w-7 items-center justify-center rounded-full bg-signal-dim font-mono-data text-xs font-medium text-signal">
                {initials}
              </span>
              <span className="hidden sm:inline">{user?.name}</span>
              <ChevronDown className="h-3.5 w-3.5 text-ink-muted" />
            </button>

            {menuOpen && (
              <div
                role="menu"
                className="glass-panel absolute right-0 mt-2 w-48 overflow-hidden rounded-xl py-1 shadow-xl"
              >
                <div className="border-b border-hairline px-3 py-2">
                  <p className="truncate text-sm font-medium text-ink-text">{user?.name}</p>
                  <p className="truncate text-xs text-ink-muted">{user?.email}</p>
                </div>
                <button
                  type="button"
                  role="menuitem"
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-ink-text hover:bg-hairline/30"
                  onClick={() => setMenuOpen(false)}
                >
                  <UserIcon className="h-4 w-4" /> Profile
                </button>
                <button
                  type="button"
                  role="menuitem"
                  className="flex w-full items-center gap-2 px-3 py-2 text-sm text-danger hover:bg-hairline/30"
                  onClick={() => {
                    setMenuOpen(false);
                    logout();
                  }}
                >
                  <LogOut className="h-4 w-4" /> Log out
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
