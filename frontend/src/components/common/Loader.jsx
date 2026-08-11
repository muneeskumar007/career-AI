import { Loader2 } from "lucide-react";
import { cn } from "@/utils/validators";

export default function Loader({ fullScreen = false }) {
  return (
    <div
      className={cn(
        "flex items-center justify-center text-ink-muted",
        fullScreen ? "min-h-screen w-full bg-ink" : "p-6"
      )}
      role="status"
      aria-live="polite"
    >
      <Loader2 className="h-6 w-6 animate-spin" aria-hidden="true" />
      <span className="sr-only">Loading…</span>
    </div>
  );
}
