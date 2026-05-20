import { api } from "./api";

export type StatusCampanha =
  | "rascunho"
  | "aguardando_aprovacao"
  | "aprovada"
  | "publicada"
  | "rejeitada";

export interface Campanha {
  id: string;
  copy: string;
  publico_alvo: Record<string, unknown>;
  orcamento_sugerido: number | null;
  status: StatusCampanha;
  aprovada_por: string | null;
  criado_em: string;
  atualizado_em: string;
}

export interface GerarCampanhaInput {
  segmento_id?: string;
}

export interface CampanhaListResponse {
  total: number;
  items: Campanha[];
}

export const campanhasService = {
  getCampanhas: () => api.get<CampanhaListResponse>("/campanhas"),
  gerarCampanha: (input: GerarCampanhaInput) =>
    api.post<Campanha>("/campanhas/gerar", input),
  editarCampanha: (id: string, data: Partial<Pick<Campanha, "copy" | "orcamento_sugerido">>) =>
    api.patch<Campanha>(`/campanhas/${id}`, data),
  aprovarCampanha: (id: string) =>
    api.post<Campanha>(`/campanhas/${id}/aprovar`),
  rejeitarCampanha: (id: string) =>
    api.post<Campanha>(`/campanhas/${id}/rejeitar`),
};
