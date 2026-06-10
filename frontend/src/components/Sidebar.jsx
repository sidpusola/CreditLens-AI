import { NavLink } from "react-router-dom";

const NAV = [
  { to: "/", label: "Dashboard", icon: "M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" },
  { to: "/assess", label: "New Assessment", icon: "M12 4v16m8-8H4" },
  { to: "/report", label: "Risk Report", icon: "M9 17v-6h6v6m2 4H7a2 2 0 01-2-2V5a2 2 0 012-2h7l5 5v11a2 2 0 01-2 2z" },
  { to: "/model", label: "Model Insights", icon: "M11 3.05V11h7.95A8 8 0 1011 3.05zM13 3v6h6a8 8 0 00-6-6z" },
];

export default function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-ink-700 bg-ink-800/60 p-5 md:flex">
      <div className="mb-8 flex items-center gap-2.5 px-1">
        <div className="grid h-9 w-9 place-items-center rounded-xl bg-accent text-lg font-extrabold text-white">
          C
        </div>
        <div>
          <p className="text-sm font-bold leading-tight text-white">CreditLens AI</p>
          <p className="text-[11px] text-slate-400">Risk Intelligence</p>
        </div>
      </div>

      <nav className="flex flex-col gap-1">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/"}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${
                isActive
                  ? "bg-accent/15 text-accent-soft"
                  : "text-slate-400 hover:bg-ink-700 hover:text-slate-200"
              }`
            }
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8">
              <path strokeLinecap="round" strokeLinejoin="round" d={item.icon} />
            </svg>
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-auto rounded-xl border border-ink-700 bg-ink-900/50 p-3 text-[11px] text-slate-500">
        Production model: <span className="font-semibold text-slate-300">XGBoost</span>
        <br />ROC-AUC 0.7773
      </div>
    </aside>
  );
}
