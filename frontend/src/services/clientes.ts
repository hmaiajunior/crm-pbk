import { api } from "./api";
import type { TipoAcao, AgenteOrigem, StatusAcao } from "./acoes";

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

export interface ClienteInsights {
  total_mensagens: number;
  mensagens_entrada: number;
  mensagens_saida: number;
  sentimento_distribuicao: { positivo: number; neutro: number; negativo: number };
  tema_dominante: string | null;
  dias_desde_ultima_interacao: number | null;
  dias_desde_ultima_compra: number | null;
  total_compras: number;
  total_acoes_pendentes: number;
}

export interface ClienteAcaoPendente {
  id: string;
  tipo: TipoAcao;
  agente: AgenteOrigem;
  conteudo_sugerido: string;
  status: StatusAcao;
  criado_em: string;
}

export interface ClienteDetalhe extends ClienteListItem {
  opt_in: boolean;
  primeira_interacao_em: string;
  ultima_compra_em: string | null;
  timeline: TimelineItem[];
  insights: ClienteInsights;
  acoes_pendentes: ClienteAcaoPendente[];
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
