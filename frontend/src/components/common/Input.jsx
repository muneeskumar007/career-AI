import { forwardRef, useId, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "@/utils/validators";

const Input = forwardRef(({ label, error, icon, type = "text", id, className, ...rest }, ref) => {
  const generatedId = useId();
  const inputId = id ?? generatedId;
  const isPassword = type === "password";
  const [revealed, setRevealed] = useState(false);
  const errorId = error ? `${inputId}-error` : undefined;

  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-ink-text">
        {label}
      </label>
      <div className="relative">
        {icon && (
          <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted">
            {icon}
          </span>
        )}
        <input
          ref={ref}
          id={inputId}
          type={isPassword && revealed ? "text" : type}
          aria-invalid={!!error}
          aria-describedby={errorId}
          className={cn(
            "w-full rounded-xl border bg-surface/60 py-2.5 text-sm text-ink-text placeholder:text-ink-muted",
            "outline-none transition-colors focus:border-signal",
            icon ? "pl-10" : "pl-3.5",
            isPassword ? "pr-10" : "pr-3.5",
            error ? "border-danger" : "border-hairline",
            className
          )}
          {...rest}
        />
        {isPassword && (
          <button
            type="button"
            onClick={() => setRevealed((v) => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-text"
            aria-label={revealed ? "Hide password" : "Show password"}
            tabIndex={-1}
          >
            {revealed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
      {error && (
        <p id={errorId} role="alert" className="text-xs text-danger">
          {error}
        </p>
      )}
    </div>
  );
});
Input.displayName = "Input";

export default Input;
