import api from "./client";
import type { ServiceType, ServiceTypeCreate, ServiceTypeUpdate } from "@patas/shared-types";

export const serviceTypesApi = {
  list: () => api.get<ServiceType[]>("/service-types/"),
  create: (data: ServiceTypeCreate) => api.post<ServiceType>("/service-types/", data),
  update: (id: number, data: ServiceTypeUpdate) => api.patch<ServiceType>(`/service-types/${id}`, data),
};
