import { useEffect, useState } from "react";
import { campanhasService } from "../../services/campanhas";
import type { Campanha, StatusCampanha } from "../../services/campanhas";

const statusLabel: Record<StatusCampanha, string> = {
  rascunho: "Rascunho",
  aguardando_aprovacao: "Aguardando aprovação",
  aprovada: "Aprovada",
  publicada: "Publicada",
  rejeitada: "Rejeitada",
};

const statusColor: Record<StatusCampanha, string> = {
  rascunho: "bg-gray-100 text-gray-600",
  aguardando_aprovacao: "bg-yellow-100 text-yellow-800",
  aprovada: "bg-green-100 text-green-700",
  publicada: "bg-blue-100 text-blue-700",
  rejeitada: "bg-red-100 text-red-700",
};

export default function Campanhas() {
  const [campanhas, setCampanhas] = useState<Campanha[]>([]);
  const [loading, setLoading] = useState(true);
  const [confirmAction, setConfirmAction] = useState<{ id: string; action: "aprovar" | "rejeitar" } | null>(null);

  useEffect(() => {
    campanhasService.getCampanhas().then((data) => setCampanhas(data.items)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function handleConfirm() {
    if (!confirmAction) return;
    try {
      const updated =
        confirmAction.action === "aprovar"
          ? await campanhasService.aprovarCampanha(confirmAction.id)
          : await campanhasService.rejeitarCampanha(confirmAction.id);
      setCampanhas((prev) => prev.map((c) => (c.id === updated.id ? updated : c)));
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro");
    } finally {
      setConfirmAction(null);
    }
  }

  if (loading) return <div className="p-6 text-gray-500">Carregando...</div>;

  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-gray-900 mb-4">Campanhas</h1>

      {confirmAction && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 shadow-xl max-w-sm w-full mx-4">
            <p className="text-gray-800 font-medium">
              {confirmAction.action === "aprovar" ? "Aprovar campanha?" : "Rejeitar campanha?"}
            </p>
            <p className="text-sm text-gray-500 mt-1">
              {confirmAction.action === "aprovar"
                ? "A campanha será marcada como aprovada."
                : "A campanha será rejeitada e não poderá ser publicada."}
            </p>
            <div className="flex gap-2 mt-4 justify-end">
              <button
                onClick={() => setConfirmAction(null)}
                className="px-4 py-2 text-sm border rounded hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleConfirm}
                className={`px-4 py-2 text-sm text-white rounded ${
                  confirmAction.action === "aprovar"
                    ? "bg-green-600 hover:bg-green-700"
                    : "bg-red-600 hover:bg-red-700"
                }`}
              >
                Confirmar
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="space-y-3">
        {campanhas.map((c) => (
          <div key={c.id} className="bg-white rounded-lg shadow p-4">
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-800 line-clamp-2">{c.copy}</p>
                {c.orcamento_sugerido && (
                  <p className="text-xs text-gray-500 mt-1">
                    Orçamento sugerido: R$ {c.orcamento_sugerido.toFixed(2)}
                  </p>
                )}
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusColor[c.status]}`}>
                  {statusLabel[c.status]}
                </span>
                {c.status === "aguardando_aprovacao" && (
                  <>
                    <button
                      onClick={() => setConfirmAction({ id: c.id, action: "aprovar" })}
                      className="text-xs text-green-600 hover:underline"
                    >
                      Aprovar
                    </button>
                    <button
                      onClick={() => setConfirmAction({ id: c.id, action: "rejeitar" })}
                      className="text-xs text-red-600 hover:underline"
                    >
                      Rejeitar
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
        {campanhas.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-8">Nenhuma campanha cadastrada</p>
        )}
      </div>
    </div>
  );
}
