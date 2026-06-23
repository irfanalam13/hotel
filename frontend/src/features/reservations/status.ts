import type { BadgeProps } from "@/components/ui/badge";
import type { ReservationStatus } from "@/types";

export const RESERVATION_STATUS: Record<
  ReservationStatus,
  { label: string; variant: BadgeProps["variant"] }
> = {
  inquiry: { label: "Inquiry", variant: "secondary" },
  booked: { label: "Booked", variant: "info" },
  checked_in: { label: "Checked in", variant: "success" },
  checked_out: { label: "Checked out", variant: "secondary" },
  cancelled: { label: "Cancelled", variant: "danger" },
  no_show: { label: "No-show", variant: "warning" },
};
