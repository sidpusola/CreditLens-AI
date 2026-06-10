import { Outlet, NavLink } from "react-router-dom";
import Sidebar from "./Sidebar";

const MOBILE_NAV = [
  { to: "/", label: "Home" },
  { to: "/assess", label: "Assess" },
  { to: "/report", label: "Report" },
  { to: "/model", label: "Model" },
];

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-ink-900">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Mobile top nav */}
        <header className="flex items-center justify-between border-b border-ink-700 px-4 py-3 md:hidden">
          <span className="font-bold text-white">CreditLens AI</span>
          <nav className="flex gap-1">
            {MOBILE_NAV.map((n) => (
              <NavLink
                key={n.to}
                to={n.to}
                end={n.to === "/"}
                className={({ isActive }) =>
                  `rounded-lg px-2.5 py-1 text-xs font-medium ${
                    isActive ? "bg-accent/20 text-accent-soft" : "text-slate-400"
                  }`
                }
              >
                {n.label}
              </NavLink>
            ))}
          </nav>
        </header>

        <main className="flex-1 overflow-y-auto p-5 md:p-8">
          <div className="mx-auto max-w-6xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
