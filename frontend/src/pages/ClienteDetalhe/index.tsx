import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { clientesService } from "../../services/clientes";
import type { ClienteDetalhe, TimelineItem } from "../../services/clientes";

function sentimentoColor(s: unknown) {
  if (s === "positivo") return "text-green-600";
  if (s === "negativo") return "text-red-600";
  return "text-gray-500";
}

function TimelineEntry({ item }: { item: TimelineItem }) {
  const ts = new Date(item.timestamp).toLocaleString("pt-BR");
  if (item.tipo === "compra") {
    return (
      <div className="flex gap-3 py-3 border-b last:border-0">
        <div className="w-2 h-2 mt-2 rounded-full bg-green-500 shrink-0" />
        <div>
          <p className="text-sm font-medium text-gray-700">Compra realizada</p>
          <p className="text-xs text-gray-400">{ts}</p>
        </div>
      </div>
    );
  }
  const d = item.dados as { conteudo?: string; direcao?: string; sentimento?: string; tema?: string };
  return (
    <div className="flex gap-3 py-3 border-b last:border-0">
      <div className={`w-2 h-2 mt-2 rounded-full shrink-0 ${d.direcao === "entrada" ? "bg-blue-400" : "bg-gray-300"}`} />
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-800 truncate">{d.conteudo}</p>
        <div className="flex gap-2 mt-0.5">
          <span className="text-xs text-gray-400">{ts}</span>
          {d.sentimento && (
            <span className={`text-xs ${sentimentoColor(d.sentimento)}`}>{d.sentimento}</span>
          )}
          {d.tema && <span className="text-xs text-gray-400">{d.tema}</span>}
        </div>
      </div>
    </div>
  );
}

export default function ClienteDetalhePage() {
  const { id } = useParams<{ id: string }>();
  const [cliente, setCliente] = useState<ClienteDetalhe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;
    clientesService
      .getCliente(id)
      .then(setCliente)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="p-6 text-gray-500">Carregando...</div>;
  if (error) return <div className="p-6 text-red-600">{error}</div>;
  if (!cliente) return null;

  return (
    <div className="p-6 max-w-3xl">
      <Link to="/clientes" className="text-sm text-blue-600 hover:underline mb-4 block">
        ← Voltar para clientes
      </Link>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h1 className="text-xl font-semibold text-gray-900">
          {cliente.nome ?? cliente.telefone}
        </h1>
        <p className="text-sm text-gray-500">{cliente.telefone}</p>
        <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
          <div>
            <span className="text-gray-500">Classificação: </span>
            <span className="font-medium">{cliente.classificacao}</span>
          </div>
          <div>
            <span className="text-gray-500">Opt-in: </span>
            <span>{cliente.opt_in ? "Sim" : "Não"}</span>
          </div>
          <div>
            <span className="text-gray-500">Primeira interação: </span>
            <span>{new Date(cliente.primeira_interacao_em).toLocaleDateString("pt-BR")}</span>
          </div>
          {cliente.ultima_compra_em && (
            <div>
              <span className="text-gray-500">Última compra: </span>
              <span>{new Date(cliente.ultima_compra_em).toLocaleDateString("pt-BR")}</span>
            </div>
          )}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-base font-medium text-gray-800 mb-3">Timeline</h2>
        {cliente.timeline.length === 0 ? (
          <p className="text-sm text-gray-400">Nenhuma interação registrada</p>
        ) : (
          cliente.timeline.map((item, i) => <TimelineEntry key={i} item={item} />)
        )}
      </div>
    </div>
  );
}
