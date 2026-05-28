import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { clientesService } from "../../services/clientes";
import type {
  ClienteDetalhe,
  ClienteAcaoPendente,
  ClienteInsights,
  TimelineItem,
} from "../../services/clientes";
import { acoesService } from "../../services/acoes";

function sentimentoColor(s: unknown) {
  if (s === "positivo") return "text-green-600";
  if (s === "negativo") return "text-red-600";
  return "text-gray-500";
}

function tipoAcaoLabel(t: string) {
  if (t === "convite_vip") return "Convite VIP";
  if (t === "oferta") return "Oferta";
  if (t === "follow_up") return "Follow-up";
  return t;
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

function InsightCell({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <p className="text-xs text-gray-500">{label}</p>
      <p className="text-sm font-medium text-gray-800">{value ?? "—"}</p>
    </div>
  );
}

function InsightsPanel({ data }: { data: ClienteInsights }) {
  const sd = data.sentimento_distribuicao;
  const sentimentoSummary = `+${sd.positivo} / =${sd.neutro} / -${sd.negativo}`;
  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-base font-medium text-gray-800 mb-3">Insights</h2>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <InsightCell label="Mensagens (total)" value={data.total_mensagens} />
        <InsightCell label="Entrada / Saída" value={`${data.mensagens_entrada} / ${data.mensagens_saida}`} />
        <InsightCell label="Sentimento (+/=/-)" value={sentimentoSummary} />
        <InsightCell label="Tema dominante" value={data.tema_dominante} />
        <InsightCell label="Dias desde última interação" value={data.dias_desde_ultima_interacao} />
        <InsightCell label="Dias desde última compra" value={data.dias_desde_ultima_compra} />
        <InsightCell label="Total de compras" value={data.total_compras} />
        <InsightCell label="Ações pendentes" value={data.total_acoes_pendentes} />
      </div>
    </div>
  );
}

function AcoesPanel({
  acoes,
  onResolved,
}: {
  acoes: ClienteAcaoPendente[];
  onResolved: (id: string) => void;
}) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handle(id: string, action: "aprovar" | "rejeitar") {
    setBusy(id);
    setError("");
    try {
      if (action === "aprovar") await acoesService.aprovar(id);
      else await acoesService.rejeitar(id);
      onResolved(id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao processar ação");
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 mb-6">
      <h2 className="text-base font-medium text-gray-800 mb-3">Ações sugeridas</h2>
      {error && <p className="text-sm text-red-600 mb-2">{error}</p>}
      {acoes.length === 0 ? (
        <p className="text-sm text-gray-400">Nenhuma ação sugerida no momento</p>
      ) : (
        <ul className="divide-y divide-gray-100">
          {acoes.map((a) => (
            <li key={a.id} className="py-3 flex gap-3 items-start">
              <div className="flex-1 min-w-0">
                <div className="flex gap-2 items-center mb-1">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                    {tipoAcaoLabel(a.tipo)}
                  </span>
                  <span className="text-xs text-gray-400">
                    {new Date(a.criado_em).toLocaleString("pt-BR")}
                  </span>
                </div>
                <p className="text-sm text-gray-800">{a.conteudo_sugerido}</p>
              </div>
              <div className="flex gap-2 shrink-0">
                <button
                  onClick={() => handle(a.id, "aprovar")}
                  disabled={busy === a.id}
                  className="text-sm px-3 py-1 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                >
                  Aprovar
                </button>
                <button
                  onClick={() => handle(a.id, "rejeitar")}
                  disabled={busy === a.id}
                  className="text-sm px-3 py-1 border rounded hover:bg-gray-50 disabled:opacity-50"
                >
                  Rejeitar
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
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

  function handleAcaoResolved(acaoId: string) {
    setCliente((prev) => {
      if (!prev) return prev;
      const filtered = prev.acoes_pendentes.filter((a) => a.id !== acaoId);
      return {
        ...prev,
        acoes_pendentes: filtered,
        insights: { ...prev.insights, total_acoes_pendentes: filtered.length },
      };
    });
  }

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

      <InsightsPanel data={cliente.insights} />

      <AcoesPanel acoes={cliente.acoes_pendentes} onResolved={handleAcaoResolved} />

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
