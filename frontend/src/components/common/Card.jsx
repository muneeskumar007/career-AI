import { cn } from "@/utils/validators";

export default function Card({ className, children, ...rest }) {
  return (
    <div className={cn("glass-panel rounded-[1.25rem] p-6 sm:p-8", className)} {...rest}>
      {children}
    </div>
  );
}
