import { useState } from "react";
import { useHealthCheck } from "../hooks/useHealthCheck";

export default function HealthIndicator() {
  const { health, error } = useHealthCheck();
  const [showDetail, setShowDetail] = useState(false);

  let color = "var(--color-text-secondary)"; // 灰 — 未知
  let label = "检查中...";

  if (error) {
    color = "var(--color-error)";
    label = "无法连接";
  } else if (health) {
    const allHealthy = Object.values(health.components).every((v) => v === "healthy");
    if (allHealthy) {
      color = "var(--color-success)";
      label = "服务正常";
    } else {
      color = "var(--color-warning)";
      label = "部分异常";
    }
  }

  return (
    <div style={{ position: "relative" }}>
      <button
        type="button"
        onClick={() => setShowDetail((v) => !v)}
        style={{
          display: "flex", alignItems: "center", gap: "6px",
          background: "none", border: "none", cursor: "pointer", padding: "4px 8px",
          fontSize: "var(--text-sm)", color: "var(--color-text-secondary)",
        }}
        title={label}
      >
        <span style={{
          width: 8, height: 8, borderRadius: "50%", background: color,
          display: "inline-block", boxShadow: `0 0 6px ${color}`,
        }} />
      </button>
      {showDetail && health && (
        <div className="card" style={{
          position: "absolute", right: 0, top: "100%", marginTop: "8px",
          padding: "12px 16px", minWidth: "180px", zIndex: 100,
          fontSize: "var(--text-sm)",
        }}>
          {Object.entries(health.components).map(([key, val]) => (
            <div key={key} style={{ display: "flex", justifyContent: "space-between", padding: "2px 0" }}>
              <span>{key}</span>
              <span style={{ color: val === "healthy" ? "var(--color-success)" : "var(--color-error)" }}>
                {val === "healthy" ? "✓" : "✗"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
