"use client";

import { Sparkles } from "lucide-react";

import { ComingSoon } from "@/components/shared/coming-soon";

export default function HousekeepingPage() {
  return (
    <ComingSoon
      title="Housekeeping"
      description="Room cleaning workflows and staff assignments."
      icon={Sparkles}
      features={["Cleaning queues", "Staff assignments", "Inspection checklists", "Turn-down service"]}
    />
  );
}
