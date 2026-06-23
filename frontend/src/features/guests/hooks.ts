"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useActiveOrg } from "@/components/layout/active-org";
import type { Guest, Paginated } from "@/types";
import { guestsApi } from "./api";

export function useGuests() {
  const { slug } = useActiveOrg();
  return useQuery({
    queryKey: ["guests", slug],
    queryFn: guestsApi.list,
    enabled: !!slug,
  });
}

export function useCreateGuest() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => guestsApi.create(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["guests", slug] });
      toast.success("Guest added");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useUpdateGuest() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      guestsApi.update(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["guests", slug] });
      toast.success("Guest updated");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useDeleteGuest() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  const key = ["guests", slug] as const;
  return useMutation({
    mutationFn: (id: string) => guestsApi.remove(id),
    onMutate: async (id: string) => {
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData<Paginated<Guest>>(key);
      if (previous) {
        qc.setQueryData<Paginated<Guest>>(key, {
          ...previous,
          count: Math.max(0, previous.count - 1),
          results: previous.results.filter((g) => g.id !== id),
        });
      }
      return { previous };
    },
    onError: (e, _id, ctx) => {
      if (ctx?.previous) qc.setQueryData(key, ctx.previous);
      toast.error(e.message);
    },
    onSuccess: () => toast.success("Guest deleted"),
    onSettled: () => qc.invalidateQueries({ queryKey: key }),
  });
}
