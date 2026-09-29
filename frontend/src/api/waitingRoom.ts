import api from "./client";
import type { WaitingRoomEntry, WaitingRoomEntryCreate, WaitingRoomStatus, WaitingRoomTransition } from "@patas/shared-types";

export const waitingRoomApi = {
  list: (params: { date?: string; status?: WaitingRoomStatus; service_type_id?: number; q?: string } = {}) =>
    api.get<WaitingRoomEntry[]>("/waiting-room/", { params }),
  create: (data: WaitingRoomEntryCreate) => api.post<WaitingRoomEntry>("/waiting-room/entries", data),
  update: (id: number, data: { room?: string; message?: string }) => api.patch<WaitingRoomEntry>(`/waiting-room/entries/${id}`, data),
  transition: (id: number, data: WaitingRoomTransition) => api.post<WaitingRoomEntry>(`/waiting-room/entries/${id}/transition`, data),
};
