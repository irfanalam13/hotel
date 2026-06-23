import { api } from "@/lib/api";
import type { Membership, Organization, Paginated } from "@/types";

export const organizationsApi = {
  list: () =>
    api.get<Paginated<Organization>>("/api/organizations/", { withTenant: false }),
  create: (body: { name: string; plan?: string }) =>
    api.post<Organization>("/api/organizations/", body, { withTenant: false }),
  members: () => api.get<Membership[]>("/api/organizations/members/"),
  invite: (body: { email: string; role_code: string; full_name?: string }) =>
    api.post<Membership>("/api/organizations/members/invite/", body),
};
