import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { clientesService } from "../../services/clientes";
import type { ClienteListItem, Classificacao } from "../../services/clientes";
import SegmentoFiltro from "../../components/SegmentoFiltro";

const classificacaoBadge: Record<Classificacao, string> = {
  lead: "bg-yellow-100 text-yellow-800",
  cliente: "bg-blue-100 text-blue-800",
  cliente_recorrente: "bg-green-100 text-green-800",
  inativo: "bg-gray-100 text-gray-600",
};

export default function Clientes() {
  const [clientes, setClientes] = useState<ClienteListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [segmentoId, setSegmentoId] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    clientesService
      .getClientes({ page, segmento_id: segmentoId || undefined })
      .then((data) => {
        setClientes(data.items);
        setTotal(data.total);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [page, segmentoId]);

  function handleSegmentoChange(id: string) {
    setSegmentoId(id);
    setPage(1);
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-semibold text-gray-900">Clientes ({total})</h1>
        <SegmentoFiltro value={segmentoId} onChange={handleSegmentoChange} />
      </div>

      {loading ? (
        <p className="text-gray-500 text-sm">Carregando...</p>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full text-sm">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Nome</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Telefone</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Classificação</th>
                <th className="px-4 py-3 text-left font-medium text-gray-600">Última interação</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {clientes.map((c) => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <Link to={`/clientes/${c.id}`} className="text-blue-600 hover:underline">
                      {c.nome ?? c.telefone}
                    </Link>
                  </td>
                  <td className="px-4 py-3 text-gray-600">{c.telefone}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${classificacaoBadge[c.classificacao]}`}>
                      {c.classificacao.replace("_", " ")}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">
                    {c.ultima_interacao_em
                      ? new Date(c.ultima_interacao_em).toLocaleDateString("pt-BR")
                      : "—"}
                  </td>
                </tr>
              ))}
              {clientes.length === 0 && (
                <tr>
                  <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                    Nenhum cliente encontrado
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      <div className="flex items-center gap-2 mt-4 text-sm">
        <button
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1}
          className="px-3 py-1 border rounded disabled:opacity-40"
        >
          Anterior
        </button>
        <span className="text-gray-600">Página {page}</span>
        <button
          onClick={() => setPage((p) => p + 1)}
          disabled={clientes.length < 20}
          className="px-3 py-1 border rounded disabled:opacity-40"
        >
          Próxima
        </button>
      </div>
    </div>
  );
}
