"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useActiveOrg } from "@/components/layout/active-org";
import { ApiError } from "@/lib/api";
import { reservationsApi } from "./api";

export function useReservations(status?: string) {
  const { slug } = useActiveOrg();
  return useQuery({
    queryKey: ["reservations", slug, status ?? "all"],
    queryFn: () => reservationsApi.list(status),
    enabled: !!slug,
  });
}

export function useAvailability(
  params: { property: string; check_in: string; check_out: string } | null,
) {
  const { slug } = useActiveOrg();
  return useQuery({
    queryKey: ["availability", slug, params],
    queryFn: () => reservationsApi.availability(params!),
    enabled: !!slug && !!params && !!params.property && params.check_out > params.check_in,
  });
}

export function useCreateReservation() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => reservationsApi.create(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["reservations", slug] });
      qc.invalidateQueries({ queryKey: ["availability", slug] });
      toast.success("Reservation created");
    },
    onError: (e) =>
      toast.error((e as ApiError).status === 409 ? "No availability for those dates." : e.message),
  });
}

type Action = "cancel" | "checkIn" | "checkOut";

export function useReservationAction() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: ({ id, action }: { id: string; action: Action }) => {
      if (action === "cancel") return reservationsApi.cancel(id);
      if (action === "checkIn") return reservationsApi.checkIn(id);
      return reservationsApi.checkOut(id);
    },
    onSuccess: (_data, { action }) => {
      qc.invalidateQueries({ queryKey: ["reservations", slug] });
      qc.invalidateQueries({ queryKey: ["rooms", slug] });
      toast.success(
        action === "cancel"
          ? "Reservation cancelled"
          : action === "checkIn"
            ? "Guest checked in"
            : "Guest checked out",
      );
    },
    onError: (e) => toast.error(e.message),
  });
}
