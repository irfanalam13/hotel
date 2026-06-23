import type { BadgeProps } from "@/components/ui/badge";
import type { RoomStatus } from "@/types";

export const ROOM_STATUS: Record<
  RoomStatus,
  { label: string; variant: BadgeProps["variant"] }
> = {
  vacant_clean: { label: "Clean", variant: "success" },
  vacant_dirty: { label: "Dirty", variant: "warning" },
  occupied: { label: "Occupied", variant: "info" },
  out_of_order: { label: "Out of order", variant: "danger" },
};

export const ROOM_STATUS_OPTIONS = Object.entries(ROOM_STATUS).map(([value, meta]) => ({
  value: value as RoomStatus,
  label: meta.label,
}));
