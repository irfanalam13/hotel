import { api } from "@/lib/api";
import type { User } from "@/types";

export const authApi = {
  me: () => api.get<User>("/api/accounts/me/", { withTenant: false }),
  register: (body: { email: string; password: string; full_name?: string }) =>
    api.post<User>("/api/accounts/auth/register/", body, { auth: false, withTenant: false }),
};
