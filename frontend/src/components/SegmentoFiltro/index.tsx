import { useEffect, useState } from "react";
import { segmentosService } from "../../services/segmentos";
import type { Segmento } from "../../services/segmentos";

interface Props {
  value: string;
  onChange: (segmentoId: string) => void;
}

export default function SegmentoFiltro({ value, onChange }: Props) {
  const [segmentos, setSegmentos] = useState<Segmento[]>([]);

  useEffect(() => {
    segmentosService.getSegmentos().then(setSegmentos).catch(() => {});
  }, []);

  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
    >
      <option value="">Todos os segmentos</option>
      {segmentos.map((s) => (
        <option key={s.id} value={s.id}>
          {s.nome} ({s.total_clientes})
        </option>
      ))}
    </select>
  );
}
