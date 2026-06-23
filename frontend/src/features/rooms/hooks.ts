"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { useActiveOrg } from "@/components/layout/active-org";
import { roomsApi } from "./api";

export function useRoomTypes() {
  const { slug } = useActiveOrg();
  return useQuery({
    queryKey: ["room-types", slug],
    queryFn: roomsApi.listTypes,
    enabled: !!slug,
  });
}

export function useRooms() {
  const { slug } = useActiveOrg();
  return useQuery({
    queryKey: ["rooms", slug],
    queryFn: roomsApi.list,
    enabled: !!slug,
  });
}

export function useCreateRoomType() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => roomsApi.createType(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["room-types", slug] });
      toast.success("Room type created");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useDeleteRoomType() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: (id: string) => roomsApi.deleteType(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["room-types", slug] });
      toast.success("Room type deleted");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useCreateRoom() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: (body: Record<string, unknown>) => roomsApi.create(body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rooms", slug] });
      toast.success("Room created");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useDeleteRoom() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: (id: string) => roomsApi.remove(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rooms", slug] });
      toast.success("Room deleted");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useSetRoomStatus() {
  const qc = useQueryClient();
  const { slug } = useActiveOrg();
  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      roomsApi.setStatus(id, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["rooms", slug] });
      toast.success("Room status updated");
    },
    onError: (e) => toast.error(e.message),
  });
}
