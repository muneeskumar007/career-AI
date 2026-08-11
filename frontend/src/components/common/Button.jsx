import { forwardRef } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/utils/validators";

const VARIANT_CLASSES = {
  primary:
    "bg-signal text-ink font-semibold hover:brightness-110 active:brightness-95 disabled:hover:brightness-100",
  secondary:
    "bg-transparent border border-hairline text-ink-text hover:border-signal hover:text-signal",
  ghost: "bg-transparent text-ink-muted hover:text-ink-text",
};

const Button = forwardRef(
  ({ variant = "primary", isLoading = false, fullWidth = false, disabled, className, children, ...rest }, ref) => {
    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm transition-all duration-150",
          "disabled:cursor-not-allowed disabled:opacity-50",
          fullWidth && "w-full",
          VARIANT_CLASSES[variant],
          className
        )}
        {...rest}
      >
        {isLoading && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}
        {children}
      </button>
    );
  }
);
Button.displayName = "Button";

export default Button;
