"use client";

import { useQuery } from "@tanstack/react-query";

import { auth } from "@/lib/auth";
import { authApi } from "./api";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: authApi.me,
    enabled: auth.isAuthenticated(),
    staleTime: 5 * 60_000,
  });
}
