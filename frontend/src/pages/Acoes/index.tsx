import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { acoesService } from "../../services/acoes";
import type { AcaoItem } from "../../services/acoes";

function tipoAcaoLabel(t: string) {
  if (t === "convite_vip") return "Convite VIP";
  if (t === "oferta") return "Oferta";
  if (t === "follow_up") return "Follow-up";
  if (t === "boas_vindas") return "Boas-vindas";
  if (t === "recuperacao_checkout") return "Recuperar checkout";
  if (t === "reengajamento") return "Reengajamento";
  return t;
}

export default function Acoes() {
  const [acoes, setAcoes] = useState<AcaoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    acoesService
      .listAcoes("sugerida")
      .then((r) => setAcoes(r.items))
      .catch((e) => setError(e instanceof Error ? e.message : "Erro ao carregar ações"))
      .finally(() => setLoading(false));
  }, []);

  async function handle(id: string, action: "aprovar" | "rejeitar") {
    setBusy(id);
    setError("");
    try {
      if (action === "aprovar") await acoesService.aprovar(id);
      else await acoesService.rejeitar(id);
      setAcoes((prev) => prev.filter((a) => a.id !== id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao processar ação");
    } finally {
      setBusy(null);
    }
  }

  if (loading) return <div className="p-6 text-gray-500">Carregando...</div>;

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-gray-900 mb-4">Ações sugeridas</h1>
      {error && <p className="text-sm text-red-600 mb-3">{error}</p>}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Cliente</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Tipo</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Conteúdo</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Criado em</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {acoes.map((a) => (
              <tr key={a.id}>
                <td className="px-4 py-3">
                  <Link
                    to={`/clientes/${a.cliente.id}`}
                    className="text-blue-600 hover:underline"
                  >
                    {a.cliente.nome ?? a.cliente.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
                    {tipoAcaoLabel(a.tipo)}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-700 max-w-md truncate">{a.conteudo_sugerido}</td>
                <td className="px-4 py-3 text-gray-500">
                  {new Date(a.criado_em).toLocaleString("pt-BR")}
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
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
                </td>
              </tr>
            ))}
            {acoes.length === 0 && (
              <tr>
                <td colSpan={5} className="px-4 py-8 text-center text-gray-400">
                  Nenhuma ação pendente
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
