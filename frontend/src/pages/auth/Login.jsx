import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { Mail, Lock, AlertCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import Input from "@/components/common/Input";
import Button from "@/components/common/Button";
import { getApiErrorMessage } from "@/utils/validators";

export default function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [formError, setFormError] = useState(null);

  const {
    register: registerField,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();

  const onSubmit = async (data) => {
    setFormError(null);
    try {
      await login(data);
      const redirectTo = location.state?.from ?? "/dashboard";
      navigate(redirectTo, { replace: true });
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Couldn't log you in. Check your email and password."));
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="font-display text-2xl font-semibold text-ink-text">Welcome back</h2>
        <p className="text-sm text-ink-muted">Log in to pick up your interview prep.</p>
      </div>

      {formError && (
        <motion.div
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          role="alert"
          className="flex items-start gap-2 rounded-xl border border-danger/30 bg-danger/10 px-3.5 py-2.5 text-sm text-danger"
        >
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
          <span>{formError}</span>
        </motion.div>
      )}

      <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          icon={<Mail className="h-4 w-4" />}
          error={errors.email?.message}
          {...registerField("email", {
            required: "Enter your email",
            pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Enter a valid email" },
          })}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          icon={<Lock className="h-4 w-4" />}
          error={errors.password?.message}
          {...registerField("password", { required: "Enter your password" })}
        />

        <div className="flex justify-end">
          <Link to="/forgot-password" className="text-sm text-signal hover:underline">
            Forgot password?
          </Link>
        </div>

        <Button type="submit" fullWidth isLoading={isSubmitting}>
          Log in
        </Button>
      </form>

      <p className="text-center text-sm text-ink-muted">
        New to CareerAI?{" "}
        <Link to="/register" className="font-medium text-signal hover:underline">
          Create an account
        </Link>
      </p>
    </div>
  );
}
