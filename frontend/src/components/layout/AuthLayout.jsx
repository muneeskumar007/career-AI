import { Navigate, Outlet } from "react-router-dom";
import { motion } from "framer-motion";
import { useAuth } from "@/hooks/useAuth";
import SignalBars from "@/components/common/SignalBars";
import ThemeToggle from "@/components/common/ThemeToggle";
import Loader from "@/components/common/Loader";

export default function AuthLayout() {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) return <Loader fullScreen />;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  return (
    <div className="relative flex min-h-screen w-full flex-col bg-ink md:flex-row">
      {/* Brand panel — hidden below md, shown as a compact header instead */}
      <div className="relative hidden overflow-hidden bg-gradient-to-br from-[#0a0f1e] via-[#0c1526] to-[#0a1f1c] px-12 py-10 md:flex md:w-[44%] md:flex-col md:justify-between lg:w-[40%]">
        <div
          className="pointer-events-none absolute -top-32 -left-20 h-96 w-96 rounded-full opacity-20 blur-[100px]"
          style={{ background: "radial-gradient(circle, #2fe2c4, transparent 70%)" }}
        />
        <div
          className="pointer-events-none absolute bottom-0 right-0 h-72 w-72 rounded-full opacity-20 blur-[100px]"
          style={{ background: "radial-gradient(circle, #f5b942, transparent 70%)" }}
        />

        <motion.div
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="relative z-10 flex items-center gap-2"
        >
          <span className="font-display text-lg font-semibold tracking-tight text-white">CareerAI</span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="relative z-10 flex flex-col gap-6"
        >
          <h1 className="font-display text-4xl font-semibold leading-[1.1] text-white lg:text-[2.75rem]">
            Arrive already
            <br />
            calibrated.
          </h1>
          <p className="max-w-sm text-[15px] leading-relaxed text-white/60">
            CareerAI scores your resume against any job description, rehearses the interview with
            you, and shows you exactly what to fix before it counts.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="relative z-10 flex flex-col gap-2"
        >
          <SignalBars />
          <span className="font-mono-data text-[11px] uppercase tracking-widest text-white/35">
            Reading pacing · clarity · confidence
          </span>
        </motion.div>
      </div>

      {/* Compact mobile header, shown only below md */}
      <div className="flex items-center justify-between px-6 pt-6 md:hidden">
        <span className="font-display text-lg font-semibold text-ink-text">CareerAI</span>
        <ThemeToggle />
      </div>

      {/* Form panel */}
      <div className="relative flex flex-1 flex-col items-center justify-center px-6 py-12">
        <div className="absolute right-6 top-6 hidden md:block">
          <ThemeToggle />
        </div>
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="w-full max-w-sm"
        >
          <Outlet />
        </motion.div>
      </div>
    </div>
  );
}
