"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useActiveOrg } from "@/components/layout/active-org";
import type { Paginated, Property } from "@/types";
import { propertiesApi } from "./api";

export function usePropertiesKey() {
  const { slug } = useActiveOrg();
  return ["properties", slug] as const;
}

export function useProperties() {
  const { slug } = useActiveOrg();
  return useQuery({
    queryKey: ["properties", slug],
    queryFn: propertiesApi.list,
    enabled: !!slug,
  });
}

export function useCreateProperty() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => propertiesApi.create(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["properties", slug] });
      toast.success("Property created");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useUpdateProperty() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: Record<string, unknown> }) =>
      propertiesApi.update(id, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["properties", slug] });
      toast.success("Property updated");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useDeleteProperty() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  const key = ["properties", slug] as const;
  return useMutation({
    mutationFn: (id: string) => propertiesApi.remove(id),
    // Optimistic removal.
    onMutate: async (id: string) => {
      await qc.cancelQueries({ queryKey: key });
      const previous = qc.getQueryData<Paginated<Property>>(key);
      if (previous) {
        qc.setQueryData<Paginated<Property>>(key, {
          ...previous,
          count: Math.max(0, previous.count - 1),
          results: previous.results.filter((p) => p.id !== id),
        });
      }
      return { previous };
    },
    onError: (e, _id, ctx) => {
      if (ctx?.previous) qc.setQueryData(key, ctx.previous);
      toast.error(e.message);
    },
    onSuccess: () => toast.success("Property deleted"),
    onSettled: () => qc.invalidateQueries({ queryKey: key }),
  });
}
