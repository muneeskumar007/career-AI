import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useForm } from "react-hook-form";
import { Lock, AlertCircle, AlertTriangle } from "lucide-react";
import * as authService from "@/services/authService";
import Input from "@/components/common/Input";
import Button from "@/components/common/Button";
import PasswordStrengthMeter from "@/components/common/PasswordStrengthMeter";
import { PASSWORD_REGEX, PASSWORD_HINT, getApiErrorMessage } from "@/utils/validators";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();
  const [formError, setFormError] = useState(null);

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm();

  const password = watch("password", "");

  const onSubmit = async (data) => {
    if (!token) return;
    setFormError(null);
    try {
      await authService.resetPassword(token, data.password);
      navigate("/login", { replace: true, state: { resetSuccess: true } });
    } catch (error) {
      setFormError(getApiErrorMessage(error, "That reset link is invalid or has expired."));
    }
  };

  if (!token) {
    return (
      <div className="flex flex-col items-center gap-4 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-danger/10 text-danger">
          <AlertTriangle className="h-6 w-6" />
        </span>
        <h2 className="font-display text-xl font-semibold text-ink-text">Link missing or broken</h2>
        <p className="max-w-xs text-sm text-ink-muted">
          Open the reset-password link from your email again, or request a new one.
        </p>
        <Link to="/forgot-password" className="text-sm font-medium text-signal hover:underline">
          Request a new link
        </Link>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="font-display text-2xl font-semibold text-ink-text">Choose a new password</h2>
        <p className="text-sm text-ink-muted">Make it one you haven't used before.</p>
      </div>

      {formError && (
        <p role="alert" className="flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{formError}</span>
        </p>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Input
            label="New password"
            type="password"
            autoComplete="new-password"
            icon={<Lock className="h-4 w-4" />}
            error={errors.password?.message}
            {...register("password", {
              required: "Choose a password",
              pattern: { value: PASSWORD_REGEX, message: PASSWORD_HINT },
            })}
          />
          <PasswordStrengthMeter password={password} />
        </div>
        <Input
          label="Confirm new password"
          type="password"
          autoComplete="new-password"
          icon={<Lock className="h-4 w-4" />}
          error={errors.confirmPassword?.message}
          {...register("confirmPassword", {
            required: "Confirm your password",
            validate: (value) => value === password || "Passwords don't match",
          })}
        />
        <Button type="submit" fullWidth isLoading={isSubmitting}>
          Reset password
        </Button>
      </form>
    </div>
  );
}
