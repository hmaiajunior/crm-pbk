import { useEffect, useState } from "react";
import { metricasService } from "../../services/metricas";
import type { MetricasDashboard } from "../../services/metricas";

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-2xl font-semibold text-gray-900 mt-1">{value}</p>
    </div>
  );
}

export default function MetricasPanel() {
  const [metricas, setMetricas] = useState<MetricasDashboard | null>(null);

  useEffect(() => {
    metricasService.getDashboard().then(setMetricas).catch(() => {});
  }, []);

  if (!metricas) return <div className="text-sm text-gray-400">Carregando métricas...</div>;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      <MetricCard label="Total de clientes" value={metricas.clientes_total} />
      <MetricCard label="Novos (7 dias)" value={metricas.clientes_novos_7d} />
      <MetricCard label="Clientes ativos" value={metricas.clientes_ativos} />
      <MetricCard label="Clientes inativos" value={metricas.clientes_inativos} />
      <MetricCard label="Atendimentos hoje" value={metricas.atendimentos_hoje} />
      <MetricCard label="Ações pendentes" value={metricas.acoes_pendentes} />
      <MetricCard label="Campanhas pendentes" value={metricas.campanhas_pendentes} />
    </div>
  );
}
