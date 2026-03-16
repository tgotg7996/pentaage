interface ErrorCardProps {
  title?: string;
  message: string;
}

export default function ErrorCard({ title = "出错了", message }: ErrorCardProps) {
  return (
    <div className="card" style={{
      borderColor: "var(--color-error)",
      background: "var(--color-surface)",
      display: "flex", gap: "12px", alignItems: "flex-start",
    }}>
      <span style={{ fontSize: "1.5rem" }}>⚠️</span>
      <div>
        <div style={{ fontWeight: 600, color: "var(--color-error)", marginBottom: "4px" }}>{title}</div>
        <div style={{ color: "var(--color-text-secondary)", fontSize: "var(--text-sm)" }}>{message}</div>
      </div>
    </div>
  );
}
