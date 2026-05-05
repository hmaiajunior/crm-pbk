import { api } from "./api";

export type Classificacao = "lead" | "cliente" | "cliente_recorrente" | "inativo";

export interface ClienteListItem {
  id: string;
  telefone: string;
  nome: string | null;
  classificacao: Classificacao;
  ultima_interacao_em: string | null;
}

export interface ClienteListResponse {
  total: number;
  page: number;
  items: ClienteListItem[];
}

export interface TimelineItem {
  tipo: "mensagem" | "compra";
  timestamp: string;
  dados: Record<string, unknown>;
}

export interface ClienteDetalhe extends ClienteListItem {
  opt_in: boolean;
  primeira_interacao_em: string;
  ultima_compra_em: string | null;
  timeline: TimelineItem[];
}

export const clientesService = {
  getClientes: (params: { page?: number; segmento_id?: string; classificacao?: Classificacao }) => {
    const qs = new URLSearchParams();
    if (params.page) qs.set("page", String(params.page));
    if (params.segmento_id) qs.set("segmento_id", params.segmento_id);
    if (params.classificacao) qs.set("classificacao", params.classificacao);
    return api.get<ClienteListResponse>(`/clientes?${qs}`);
  },
  getCliente: (id: string) => api.get<ClienteDetalhe>(`/clientes/${id}`),
};
