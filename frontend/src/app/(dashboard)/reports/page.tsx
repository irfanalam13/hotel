"use client";

import { BarChart3 } from "lucide-react";

import { ComingSoon } from "@/components/shared/coming-soon";

export default function ReportsPage() {
  return (
    <ComingSoon
      title="Reports"
      description="Occupancy, revenue and operational analytics."
      icon={BarChart3}
      features={["Occupancy & ADR", "RevPAR", "Revenue breakdowns", "Exportable reports"]}
    />
  );
}
