import { api } from "./api";

export interface MetricasDashboard {
  clientes_total: number;
  clientes_novos_7d: number;
  clientes_ativos: number;
  clientes_inativos: number;
  atendimentos_hoje: number;
  acoes_pendentes: number;
  campanhas_pendentes: number;
}

export const metricasService = {
  getDashboard: () => api.get<MetricasDashboard>("/metricas/dashboard"),
};
