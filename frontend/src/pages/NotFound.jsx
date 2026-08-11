import { Link } from "react-router-dom";
import Button from "@/components/common/Button";

export default function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-4 bg-ink px-6 text-center">
      <span className="font-mono-data text-sm text-signal">404</span>
      <h1 className="font-display text-2xl font-semibold text-ink-text">Page not found</h1>
      <p className="max-w-xs text-sm text-ink-muted">
        The page you're looking for doesn't exist or has moved.
      </p>
      <Link to="/dashboard">
        <Button variant="secondary">Back to dashboard</Button>
      </Link>
    </div>
  );
}
