import { motion } from "framer-motion";
import { getPasswordStrength, cn } from "@/utils/validators";

const BAR_COLORS = ["bg-danger", "bg-danger", "bg-amber", "bg-signal", "bg-signal"];

export default function PasswordStrengthMeter({ password }) {
  if (!password) return null;
  const { score, label } = getPasswordStrength(password);
  const percent = (score / 5) * 100;

  return (
    <div className="flex flex-col gap-1.5" aria-live="polite">
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-hairline/60">
        <motion.div
          className={cn("h-full rounded-full", BAR_COLORS[Math.min(score, 4)])}
          initial={{ width: 0 }}
          animate={{ width: `${percent}%` }}
          transition={{ duration: 0.3, ease: "easeOut" }}
        />
      </div>
      <span className="text-xs text-ink-muted">{label}</span>
    </div>
  );
}
