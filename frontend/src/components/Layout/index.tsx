import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { acoesService } from "../../services/acoes";

const navLinks = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/clientes", label: "Clientes" },
  { to: "/conversas", label: "Conversas" },
  { to: "/acoes", label: "Ações" },
  { to: "/campanhas", label: "Campanhas" },
];

const PENDENTES_POLL_MS = 45_000;

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [pendentes, setPendentes] = useState(0);

  useEffect(() => {
    let active = true;
    const fetchCount = () =>
      acoesService
        .contar("sugerida")
        .then((r) => active && setPendentes(r.count))
        .catch(() => {});
    fetchCount();
    const id = setInterval(fetchCount, PENDENTES_POLL_MS);
    // Atualiza ao voltar para a aba e ao navegar entre páginas.
    const onFocus = () => fetchCount();
    window.addEventListener("focus", onFocus);
    return () => {
      active = false;
      clearInterval(id);
      window.removeEventListener("focus", onFocus);
    };
  }, [location.pathname]);

  function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("operador");
    navigate("/login");
  }

  return (
    <div className="min-h-screen flex">
      <aside className="w-56 bg-gray-900 text-gray-100 flex flex-col shrink-0">
        <div className="px-4 py-5 border-b border-gray-700">
          <p className="font-semibold text-white">CRM Playbekids</p>
        </div>
        <nav className="flex-1 py-4">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center justify-between px-4 py-2.5 text-sm ${
                location.pathname.startsWith(to)
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              <span>{label}</span>
              {to === "/acoes" && pendentes > 0 && (
                <span className="ml-2 inline-flex items-center justify-center min-w-[1.25rem] h-5 px-1.5 rounded-full bg-red-500 text-white text-xs font-semibold">
                  {pendentes > 99 ? "99+" : pendentes}
                </span>
              )}
            </Link>
          ))}
        </nav>
        <button
          onClick={logout}
          className="m-4 text-xs text-gray-500 hover:text-gray-300 text-left"
        >
          Sair
        </button>
      </aside>
      <main className="flex-1 overflow-auto bg-gray-50">{children}</main>
    </div>
  );
}
