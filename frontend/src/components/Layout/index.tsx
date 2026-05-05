import { Link, useLocation, useNavigate } from "react-router-dom";

const navLinks = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/clientes", label: "Clientes" },
  { to: "/conversas", label: "Conversas" },
  { to: "/campanhas", label: "Campanhas" },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();

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
              className={`block px-4 py-2.5 text-sm ${
                location.pathname.startsWith(to)
                  ? "bg-gray-700 text-white"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              {label}
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
