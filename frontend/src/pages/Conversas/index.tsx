import { useEffect, useState } from "react";
import { api } from "../../services/api";

interface Conversa {
  id: string;
  cliente_id: string;
  cliente_nome: string | null;
  cliente_telefone: string;
  status: "ativa" | "em_handoff" | "encerrada";
  operador_nome: string | null;
}

export default function Conversas() {
  const [conversas, setConversas] = useState<Conversa[]>([]);
  const [loading, setLoading] = useState(true);
  const [confirmId, setConfirmId] = useState<string | null>(null);

  useEffect(() => {
    api.get<Conversa[]>("/conversas").then(setConversas).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function assumir(id: string) {
    try {
      await api.post(`/conversas/${id}/handoff`);
      setConversas((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: "em_handoff" } : c))
      );
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao assumir conversa");
    } finally {
      setConfirmId(null);
    }
  }

  async function liberar(id: string) {
    try {
      await api.delete(`/conversas/${id}/handoff`);
      setConversas((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: "ativa", operador_nome: null } : c))
      );
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao liberar conversa");
    }
  }

  if (loading) return <div className="p-6 text-gray-500">Carregando...</div>;

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-gray-900 mb-4">Conversas</h1>

      {confirmId && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full mx-4">
            <p className="text-gray-800 font-medium">Assumir esta conversa?</p>
            <p className="text-sm text-gray-500 mt-1">Você será o responsável pelo atendimento.</p>
            <div className="flex gap-2 mt-4 justify-end">
              <button
                onClick={() => setConfirmId(null)}
                className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={() => assumir(confirmId)}
                className="px-4 py-2 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Cliente</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Status</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Operador</th>
              <th className="px-4 py-3 text-left font-medium text-gray-600">Ação</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {conversas.map((c) => (
              <tr key={c.id}>
                <td className="px-4 py-3">{c.cliente_nome ?? c.cliente_telefone}</td>
                <td className="px-4 py-3">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs ${
                      c.status === "em_handoff"
                        ? "bg-orange-100 text-orange-700"
                        : "bg-blue-100 text-blue-700"
                    }`}
                  >
                    {c.status === "em_handoff" ? "Em atendimento" : "Ativa"}
                  </span>
                </td>
                <td className="px-4 py-3 text-gray-500">{c.operador_nome ?? "—"}</td>
                <td className="px-4 py-3">
                  {c.status === "ativa" ? (
                    <button
                      onClick={() => setConfirmId(c.id)}
                      className="text-sm text-blue-600 hover:underline"
                    >
                      Assumir
                    </button>
                  ) : (
                    <button
                      onClick={() => liberar(c.id)}
                      className="text-sm text-gray-500 hover:underline"
                    >
                      Liberar
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {conversas.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                  Nenhuma conversa ativa
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
