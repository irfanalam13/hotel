import { cn } from "@/lib/utils";

export function Avatar({
  name,
  className,
}: {
  name: string;
  className?: string;
}) {
  const initials = name
    .split(/\s+/)
    .map((p) => p[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();
  return (
    <span
      className={cn(
        "inline-flex size-8 items-center justify-center rounded-full bg-primary/10 text-xs font-medium text-primary",
        className,
      )}
    >
      {initials || "?"}
    </span>
  );
}
