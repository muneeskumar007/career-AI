import { useState } from "react";
import { Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { Mail, CheckCircle2 } from "lucide-react";
import * as authService from "@/services/authService";
import Input from "@/components/common/Input";
import Button from "@/components/common/Button";
import { getApiErrorMessage } from "@/utils/validators";

export default function ForgotPassword() {
  const [sent, setSent] = useState(false);
  const [formError, setFormError] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();

  const onSubmit = async (data) => {
    setFormError(null);
    try {
      await authService.forgotPassword(data.email);
      setSent(true);
    } catch (error) {
      setFormError(getApiErrorMessage(error));
    }
  };

  if (sent) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center gap-4 text-center"
      >
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-signal-dim text-signal">
          <CheckCircle2 className="h-6 w-6" />
        </span>
        <h2 className="font-display text-xl font-semibold text-ink-text">Check your inbox</h2>
        <p className="max-w-xs text-sm text-ink-muted">
          If an account exists for that email, a reset link is on its way. It expires in 30 minutes.
        </p>
        <Link to="/login" className="text-sm font-medium text-signal hover:underline">
          Back to log in
        </Link>
      </motion.div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="font-display text-2xl font-semibold text-ink-text">Reset your password</h2>
        <p className="text-sm text-ink-muted">We'll email you a link to get back in.</p>
      </div>

      {formError && (
        <p role="alert" className="rounded-xl border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
          {formError}
        </p>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          icon={<Mail className="h-4 w-4" />}
          error={errors.email?.message}
          {...register("email", {
            required: "Enter your email",
            pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter a valid email" },
          })}
        />
        <Button type="submit" fullWidth isLoading={isSubmitting}>
          Send reset link
        </Button>
      </form>

      <p className="text-center text-sm text-ink-muted">
        <Link to="/login" className="font-medium text-signal hover:underline">
          Back to log in
        </Link>
      </p>
    </div>
  );
}
