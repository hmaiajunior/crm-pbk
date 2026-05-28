import { api } from "./api";

export type TipoAcao = "convite_vip" | "oferta" | "follow_up";
export type AgenteOrigem = "growth_agent" | "ads_agent";
export type StatusAcao = "sugerida" | "aprovada" | "executada" | "rejeitada";

export interface AcaoItem {
  id: string;
  tipo: TipoAcao;
  agente: AgenteOrigem;
  cliente: { id: string; nome: string | null };
  conteudo_sugerido: string;
  status: StatusAcao;
  criado_em: string;
}

export interface AcoesListResponse {
  items: AcaoItem[];
}

export const acoesService = {
  listAcoes: (status: StatusAcao = "sugerida") =>
    api.get<AcoesListResponse>(`/acoes?status=${status}`),
  aprovar: (id: string) => api.post<{ status: StatusAcao; executada_em: string | null }>(`/acoes/${id}/aprovar`),
  rejeitar: (id: string) => api.post<{ status: StatusAcao }>(`/acoes/${id}/rejeitar`),
};
