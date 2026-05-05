import { api } from "./api";

export interface Segmento {
  id: string;
  nome: string;
  descricao: string;
  total_clientes: number;
}

export const segmentosService = {
  getSegmentos: () => api.get<Segmento[]>("/segmentos"),
};
