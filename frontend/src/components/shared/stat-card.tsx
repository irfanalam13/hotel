"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function StatCard({
  label,
  value,
  icon: Icon,
  hint,
  loading,
  index = 0,
}: {
  label: string;
  value: React.ReactNode;
  icon: LucideIcon;
  hint?: string;
  loading?: boolean;
  index?: number;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, delay: index * 0.05 }}
    >
      <Card className="p-5 transition-shadow hover:shadow-md">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-muted-foreground">{label}</span>
          <Icon className="size-4 text-muted-foreground" />
        </div>
        <div className={cn("mt-3 text-3xl font-semibold tracking-tight")}>
          {loading ? <Skeleton className="h-8 w-20" /> : value}
        </div>
        {hint && !loading && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </Card>
    </motion.div>
  );
}
