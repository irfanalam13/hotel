import { api } from "@/lib/api";
import type { AvailabilityRow, Paginated, Reservation } from "@/types";

export const reservationsApi = {
  list: (status?: string) =>
    api.get<Paginated<Reservation>>(
      `/api/reservations/?page_size=100${status ? `&status=${status}` : ""}`,
    ),
  availability: (params: { property: string; check_in: string; check_out: string }) =>
    api.get<AvailabilityRow[]>(
      `/api/reservations/availability/?property=${params.property}&check_in=${params.check_in}&check_out=${params.check_out}`,
    ),
  create: (body: Record<string, unknown>) => api.post<Reservation>("/api/reservations/", body),
  cancel: (id: string, reason = "") =>
    api.post<Reservation>(`/api/reservations/${id}/cancel/`, { reason }),
  checkIn: (id: string) => api.post<Reservation>(`/api/reservations/${id}/check-in/`),
  checkOut: (id: string) => api.post<Reservation>(`/api/reservations/${id}/check-out/`),
};
