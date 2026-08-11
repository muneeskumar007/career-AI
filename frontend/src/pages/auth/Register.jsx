import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import { Mail, Lock, User as UserIcon, AlertCircle } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import Input from "@/components/common/Input";
import Button from "@/components/common/Button";
import PasswordStrengthMeter from "@/components/common/PasswordStrengthMeter";
import { PASSWORD_REGEX, PASSWORD_HINT, getApiErrorMessage } from "@/utils/validators";

export default function Register() {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [formError, setFormError] = useState(null);

  const {
    register: registerField,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm();

  const password = watch("password", "");

  const onSubmit = async (data) => {
    setFormError(null);
    try {
      await registerUser({ name: data.name, email: data.email, password: data.password });
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setFormError(getApiErrorMessage(error, "Couldn't create your account. Please try again."));
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="font-display text-2xl font-semibold text-ink-text">Create your account</h2>
        <p className="text-sm text-ink-muted">Start with a free resume scan, no card needed.</p>
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
          label="Full name"
          autoComplete="name"
          icon={<UserIcon className="h-4 w-4" />}
          error={errors.name?.message}
          {...registerField("name", {
            required: "Enter your name",
            minLength: { value: 2, message: "Name is too short" },
          })}
        />
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
        <div className="flex flex-col gap-1.5">
          <Input
            label="Password"
            type="password"
            autoComplete="new-password"
            icon={<Lock className="h-4 w-4" />}
            error={errors.password?.message}
            {...registerField("password", {
              required: "Choose a password",
              pattern: { value: PASSWORD_REGEX, message: PASSWORD_HINT },
            })}
          />
          <PasswordStrengthMeter password={password} />
        </div>
        <Input
          label="Confirm password"
          type="password"
          autoComplete="new-password"
          icon={<Lock className="h-4 w-4" />}
          error={errors.confirmPassword?.message}
          {...registerField("confirmPassword", {
            required: "Confirm your password",
            validate: (value) => value === password || "Passwords don't match",
          })}
        />

        <Button type="submit" fullWidth isLoading={isSubmitting}>
          Create account
        </Button>
      </form>

      <p className="text-center text-sm text-ink-muted">
        Already have an account?{" "}
        <Link to="/login" className="font-medium text-signal hover:underline">
          Log in
        </Link>
      </p>
    </div>
  );
}
