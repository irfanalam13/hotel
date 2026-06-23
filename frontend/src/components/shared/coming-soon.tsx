"use client";

import { motion } from "framer-motion";
import type { LucideIcon } from "lucide-react";

import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

export function ComingSoon({
  title,
  description,
  icon: Icon,
  features,
}: {
  title: string;
  description: string;
  icon: LucideIcon;
  features: string[];
}) {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} />
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
        <Card className="flex flex-col items-center gap-4 p-12 text-center">
          <div className="flex size-14 items-center justify-center rounded-2xl bg-primary/10">
            <Icon className="size-7 text-primary" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center justify-center gap-2">
              <h2 className="text-xl font-semibold">{title}</h2>
              <Badge variant="secondary">Coming soon</Badge>
            </div>
            <p className="mx-auto max-w-md text-sm text-muted-foreground">{description}</p>
          </div>
          <ul className="mt-2 grid gap-2 text-sm text-muted-foreground sm:grid-cols-2">
            {features.map((f) => (
              <li key={f} className="flex items-center gap-2">
                <span className="size-1.5 rounded-full bg-primary/50" />
                {f}
              </li>
            ))}
          </ul>
        </Card>
      </motion.div>
    </div>
  );
}
