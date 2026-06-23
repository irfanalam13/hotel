"use client";

import { Receipt } from "lucide-react";

import { ComingSoon } from "@/components/shared/coming-soon";

export default function BillingPage() {
  return (
    <ComingSoon
      title="Billing"
      description="Folios, invoices, payments and night audit."
      icon={Receipt}
      features={["Guest folios", "Invoices & receipts", "Payments & refunds", "Tax & service charges"]}
    />
  );
}
