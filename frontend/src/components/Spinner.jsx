import { cn } from "../utils/cn.js";

const SIZES = { sm: "h-4 w-4 border-2", md: "h-6 w-6 border-2", lg: "h-10 w-10 border-4" };

export default function Spinner({ size = "md", label = "Loading", className }) {
  return (
    <span
      role="status"
      aria-label={label}
      className={cn(
        "inline-block animate-spin rounded-full border-current border-t-transparent text-emerald-600",
        SIZES[size],
        className,
      )}
    />
  );
}
