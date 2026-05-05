import { Link } from "react-router-dom";
import MetricasPanel from "../../components/MetricasPanel";

export default function Dashboard() {
  return (
    <div className="p-6">
      <h1 className="text-xl font-semibold text-gray-900 mb-6">Dashboard</h1>
      <MetricasPanel />
      <div className="mt-6 flex gap-3">
        <Link
          to="/clientes"
          className="text-sm text-blue-600 hover:underline"
        >
          Ver clientes →
        </Link>
        <Link
          to="/conversas"
          className="text-sm text-blue-600 hover:underline"
        >
          Ver conversas →
        </Link>
        <Link
          to="/campanhas"
          className="text-sm text-blue-600 hover:underline"
        >
          Ver campanhas →
        </Link>
      </div>
    </div>
  );
}
