"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { organizationsApi } from "./api";

export function useOrganizations() {
  return useQuery({
    queryKey: ["organizations"],
    queryFn: organizationsApi.list,
  });
}

export function useMembers(enabled = true) {
  return useQuery({
    queryKey: ["members"],
    queryFn: organizationsApi.members,
    enabled,
  });
}

export function useCreateOrganization() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: organizationsApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["organizations"] });
      toast.success("Organization created");
    },
    onError: (e) => toast.error(e.message),
  });
}

export function useInviteMember() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: organizationsApi.invite,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["members"] });
      toast.success("Member invited");
    },
    onError: (e) => toast.error(e.message),
  });
}
