import { riskTheme } from "../utils/format";

// Semicircular gauge showing a 0-100 risk score.
export default function RiskGauge({ score = 0, category = "Low Risk" }) {
  const theme = riskTheme(category);
  const clamped = Math.max(0, Math.min(100, score));

  // Arc geometry: 180deg sweep, radius 90, center (110, 110)
  const r = 90;
  const cx = 110;
  const cy = 110;
  const circumference = Math.PI * r; // half circle length
  const dash = (clamped / 100) * circumference;

  return (
    <div className="flex flex-col items-center">
      <svg width="220" height="130" viewBox="0 0 220 130">
        {/* Track */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke="#252f45"
          strokeWidth="16"
          strokeLinecap="round"
        />
        {/* Value arc */}
        <path
          d={`M ${cx - r} ${cy} A ${r} ${r} 0 0 1 ${cx + r} ${cy}`}
          fill="none"
          stroke={theme.ring}
          strokeWidth="16"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
          style={{ transition: "stroke-dasharray 0.8s ease" }}
        />
      </svg>
      <div className="-mt-8 text-center">
        <p className={`text-4xl font-extrabold ${theme.text}`}>{clamped.toFixed(1)}</p>
        <p className="text-xs text-slate-500">Risk Score / 100</p>
        <span
          className={`mt-2 inline-block rounded-full border px-3 py-1 text-xs font-semibold ${theme.bg} ${theme.text} ${theme.border}`}
        >
          {category}
        </span>
      </div>
    </div>
  );
}
