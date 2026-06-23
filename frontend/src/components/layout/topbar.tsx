"use client";

import { Check, ChevronsUpDown, LogOut, Menu, Search } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Avatar } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { useMe } from "@/features/auth/hooks";
import { logout } from "@/lib/api";
import { useActiveOrg } from "./active-org";
import { Brand, SidebarNav } from "./sidebar";

export function Topbar({ onOpenCommand }: { onOpenCommand: () => void }) {
  const router = useRouter();
  const { orgs, activeOrg, setSlug } = useActiveOrg();
  const { data: me } = useMe();
  const [mobileOpen, setMobileOpen] = useState(false);

  const onLogout = () => {
    logout();
    router.replace("/login");
  };

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b bg-background/80 px-4 backdrop-blur">
      {/* Mobile nav */}
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="lg:hidden">
            <Menu className="size-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="gap-4">
          <Brand />
          <SidebarNav onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Org switcher */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="outline" size="sm" className="gap-2">
            {activeOrg?.name ?? "Select organization"}
            <ChevronsUpDown className="size-3.5 opacity-50" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" className="w-56">
          <DropdownMenuLabel>Organizations</DropdownMenuLabel>
          {orgs.map((org) => (
            <DropdownMenuItem key={org.id} onClick={() => setSlug(org.slug)}>
              <span className="flex-1 truncate">{org.name}</span>
              {org.slug === activeOrg?.slug && <Check className="size-4" />}
            </DropdownMenuItem>
          ))}
          {orgs.length === 0 && (
            <DropdownMenuItem disabled>No organizations</DropdownMenuItem>
          )}
        </DropdownMenuContent>
      </DropdownMenu>

      <div className="flex-1" />

      {/* Command palette trigger */}
      <Button
        variant="outline"
        size="sm"
        className="gap-2 text-muted-foreground"
        onClick={onOpenCommand}
      >
        <Search className="size-3.5" />
        <span className="hidden sm:inline">Search…</span>
        <kbd className="hidden rounded border bg-muted px-1.5 text-[10px] sm:inline">⌘K</kbd>
      </Button>

      {/* User menu */}
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button className="rounded-full outline-none focus-visible:ring-2 focus-visible:ring-ring">
            <Avatar name={me?.full_name || me?.email || "?"} />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end" className="w-56">
          <DropdownMenuLabel className="truncate normal-case text-foreground">
            {me?.full_name || me?.email}
          </DropdownMenuLabel>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={() => router.push("/settings")}>Settings</DropdownMenuItem>
          <DropdownMenuItem onClick={onLogout}>
            <LogOut className="size-4" /> Sign out
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  );
}
