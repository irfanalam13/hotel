"use client";

import { Boxes } from "lucide-react";

import { ComingSoon } from "@/components/shared/coming-soon";

export default function InventoryPage() {
  return (
    <ComingSoon
      title="Inventory"
      description="Stock, supplies and consumables across properties."
      icon={Boxes}
      features={["Stock levels", "Purchase orders", "Suppliers", "Low-stock alerts"]}
    />
  );
}
