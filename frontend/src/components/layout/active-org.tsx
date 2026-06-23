"use client";

import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { useOrganizations } from "@/features/organizations/hooks";
import { auth } from "@/lib/auth";
import type { Organization } from "@/types";

interface ActiveOrgContext {
  orgs: Organization[];
  activeOrg: Organization | null;
  slug: string | null;
  setSlug: (slug: string) => void;
  isLoading: boolean;
}

const Ctx = createContext<ActiveOrgContext | null>(null);

export function ActiveOrgProvider({ children }: { children: React.ReactNode }) {
  const qc = useQueryClient();
  const { data, isLoading } = useOrganizations();
  const orgs = useMemo(() => data?.results ?? [], [data]);
  const [slug, setSlugState] = useState<string | null>(() => auth.getOrgSlug());

  const setSlug = useCallback(
    (next: string) => {
      auth.setOrgSlug(next);
      setSlugState(next);
      // Tenant changed — drop all tenant-scoped caches.
      qc.invalidateQueries();
    },
    [qc],
  );

  // Default to the first organization the user belongs to.
  useEffect(() => {
    if (!slug && orgs.length > 0) {
      setSlug(orgs[0].slug);
    }
  }, [slug, orgs, setSlug]);

  const activeOrg = orgs.find((o) => o.slug === slug) ?? null;

  return (
    <Ctx.Provider value={{ orgs, activeOrg, slug, setSlug, isLoading }}>
      {children}
    </Ctx.Provider>
  );
}

export function useActiveOrg() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("useActiveOrg must be used within ActiveOrgProvider");
  return ctx;
}
