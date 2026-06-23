import { api } from "@/lib/api";
import type { Paginated, Room, RoomType } from "@/types";

export const roomsApi = {
  listTypes: () => api.get<Paginated<RoomType>>("/api/rooms/room-types/?page_size=100"),
  createType: (body: Record<string, unknown>) =>
    api.post<RoomType>("/api/rooms/room-types/", body),
  deleteType: (id: string) => api.delete<void>(`/api/rooms/room-types/${id}/`),

  list: () => api.get<Paginated<Room>>("/api/rooms/rooms/?page_size=200"),
  create: (body: Record<string, unknown>) => api.post<Room>("/api/rooms/rooms/", body),
  remove: (id: string) => api.delete<void>(`/api/rooms/rooms/${id}/`),
  setStatus: (id: string, status: string) =>
    api.patch<Room>(`/api/rooms/rooms/${id}/status/`, { status }),
};
