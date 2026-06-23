import {
  BarChart3,
  BedDouble,
  Boxes,
  Building2,
  CalendarCheck,
  LayoutDashboard,
  Receipt,
  Settings,
  Sparkles,
  Users,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
  /** No backend yet — rendered as a placeholder page. */
  soon?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Reservations", href: "/reservations", icon: CalendarCheck },
  { label: "Properties", href: "/properties", icon: Building2 },
  { label: "Rooms", href: "/rooms", icon: BedDouble },
  { label: "Guests", href: "/guests", icon: Users },
  { label: "Billing", href: "/billing", icon: Receipt, soon: true },
  { label: "Housekeeping", href: "/housekeeping", icon: Sparkles, soon: true },
  { label: "Inventory", href: "/inventory", icon: Boxes, soon: true },
  { label: "Reports", href: "/reports", icon: BarChart3, soon: true },
  { label: "Settings", href: "/settings", icon: Settings },
];
