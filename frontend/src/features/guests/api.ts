import { api } from "@/lib/api";
import type { Guest, Paginated } from "@/types";

export const guestsApi = {
  list: () => api.get<Paginated<Guest>>("/api/guests/?page_size=100"),
  create: (body: Record<string, unknown>) => api.post<Guest>("/api/guests/", body),
  update: (id: string, body: Record<string, unknown>) =>
    api.patch<Guest>(`/api/guests/${id}/`, body),
  remove: (id: string) => api.delete<void>(`/api/guests/${id}/`),
};
