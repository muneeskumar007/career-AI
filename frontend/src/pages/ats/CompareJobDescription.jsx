import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { useForm } from "react-hook-form";
import { ArrowLeft, Target } from "lucide-react";
import * as atsService from "@/services/atsService";
import Card from "@/components/common/Card";
import Button from "@/components/common/Button";
import Input from "@/components/common/Input";
import { getApiErrorMessage } from "@/utils/validators";

export default function CompareJobDescription() {
  const { resumeId } = useParams();
  const navigate = useNavigate();
  const [error, setError] = useState(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();

  const onSubmit = async (data) => {
    setError(null);
    try {
      const jd = await atsService.createJobDescription({
        title: data.title || undefined,
        company: data.company || undefined,
        rawText: data.rawText,
      });
      await atsService.compareATS(resumeId, jd.id);
      navigate(`/resume/${resumeId}/ats/${jd.id}`);
    } catch (err) {
      setError(getApiErrorMessage(err, "Couldn't run the comparison. Please try again."));
    }
  };

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-6">
      <Link to={`/resume/${resumeId}`} className="flex items-center gap-1.5 text-sm text-ink-muted hover:text-signal">
        <ArrowLeft className="h-4 w-4" /> Back to resume
      </Link>

      <div>
        <h1 className="font-display text-2xl font-semibold text-ink-text">Compare against a job description</h1>
        <p className="mt-1 text-sm text-ink-muted">Paste the full job posting for the most accurate match.</p>
      </div>

      <Card>
        <form onSubmit={handleSubmit(onSubmit)} noValidate className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Input label="Job title (optional)" {...register("title")} />
            <Input label="Company (optional)" {...register("company")} />
          </div>

          <div className="flex flex-col gap-1.5">
            <label htmlFor="rawText" className="text-sm font-medium text-ink-text">
              Job description
            </label>
            <textarea
              id="rawText"
              rows={12}
              placeholder="Paste the full job description here…"
              aria-invalid={!!errors.rawText}
              className={`w-full resize-y rounded-xl border bg-surface/60 p-3.5 text-sm text-ink-text placeholder:text-ink-muted outline-none transition-colors focus:border-signal ${
                errors.rawText ? "border-danger" : "border-hairline"
              }`}
              {...register("rawText", {
                required: "Paste the job description",
                minLength: { value: 20, message: "That looks too short to be a real job description" },
              })}
            />
            {errors.rawText && <p className="text-xs text-danger">{errors.rawText.message}</p>}
          </div>

          {error && <p className="text-sm text-danger">{error}</p>}

          <Button type="submit" isLoading={isSubmitting}>
            <Target className="h-4 w-4" /> {isSubmitting ? "Comparing…" : "Compare"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
