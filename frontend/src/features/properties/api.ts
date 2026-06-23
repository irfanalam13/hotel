import { api } from "@/lib/api";
import type { Paginated, Property } from "@/types";

export const propertiesApi = {
  list: () => api.get<Paginated<Property>>("/api/properties/?page_size=100"),
  create: (body: Record<string, unknown>) => api.post<Property>("/api/properties/", body),
  update: (id: string, body: Record<string, unknown>) =>
    api.patch<Property>(`/api/properties/${id}/`, body),
  remove: (id: string) => api.delete<void>(`/api/properties/${id}/`),
};
