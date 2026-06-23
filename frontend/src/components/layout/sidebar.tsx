"use client";

import { motion } from "framer-motion";
import { Hotel } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { NAV_ITEMS } from "./nav";

export function SidebarNav({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();

  return (
    <nav className="flex flex-1 flex-col gap-1">
      {NAV_ITEMS.map((item, i) => {
        const active = pathname === item.href || pathname.startsWith(item.href + "/");
        const Icon = item.icon;
        return (
          <motion.div
            key={item.href}
            initial={{ opacity: 0, x: -8 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.03 }}
          >
            <Link
              href={item.href}
              onClick={onNavigate}
              className={cn(
                "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "text-foreground"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              {active && (
                <motion.span
                  layoutId="sidebar-active"
                  className="absolute inset-0 rounded-lg bg-accent"
                  transition={{ type: "spring", stiffness: 380, damping: 30 }}
                />
              )}
              <Icon className="relative z-10 size-4" />
              <span className="relative z-10 flex-1">{item.label}</span>
              {item.soon && (
                <Badge variant="secondary" className="relative z-10 text-[10px]">
                  Soon
                </Badge>
              )}
            </Link>
          </motion.div>
        );
      })}
    </nav>
  );
}

export function Brand() {
  return (
    <Link href="/dashboard" className="flex items-center gap-2 px-3 py-1">
      <div className="flex size-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <Hotel className="size-5" />
      </div>
      <span className="text-lg font-semibold tracking-tight">HMS</span>
    </Link>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col gap-4 border-r bg-card/40 p-4 lg:flex">
      <Brand />
      <SidebarNav />
      <p className="px-3 text-xs text-muted-foreground">Hotel Management System</p>
    </aside>
  );
}
