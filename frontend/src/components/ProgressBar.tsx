interface ProgressBarProps {
  value: number;
  max?: number;
  showLabel?: boolean;
  color?: string;
}

export default function ProgressBar({ value, max = 1, showLabel = true, color }: ProgressBarProps) {
  const pct = Math.min(value / max, 1) * 100;
  const barColor = color || "var(--color-primary)";

  return (
    <div style={{ display: "flex", alignItems: "center", gap: "8px", width: "100%" }}>
      <div style={{
        flex: 1, height: 8, borderRadius: "var(--radius-full)",
        background: "var(--color-border)", overflow: "hidden",
      }}>
        <div style={{
          height: "100%", borderRadius: "var(--radius-full)",
          background: barColor, width: `${pct}%`,
          transition: "width 0.5s ease",
        }} />
      </div>
      {showLabel && (
        <span style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)", minWidth: "40px", textAlign: "right" }}>
          {pct.toFixed(0)}%
        </span>
      )}
    </div>
  );
}
