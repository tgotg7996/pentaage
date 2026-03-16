interface ScoreCircleProps {
  score: number;
  maxScore?: number;
  size?: number;
  label?: string;
}

export default function ScoreCircle({ score, maxScore = 100, size = 120, label }: ScoreCircleProps) {
  const safeScore = Number.isFinite(score) ? Math.max(score, 0) : 0;
  const safeMaxScore = Number.isFinite(maxScore) && maxScore > 0 ? maxScore : 100;
  const pct = Math.min(safeScore / safeMaxScore, 1);
  const strokeWidth = 8;
  const inset = strokeWidth;
  const isFullCircle = pct >= 0.999;
  const progressAngle = isFullCircle ? 360 : pct * 360;

  const strokeColor = `hsl(${110 + pct * 18}, ${50 + pct * 10}%, ${54 - pct * 8}%)`;
  const ringBackground = isFullCircle
    ? strokeColor
    : `conic-gradient(from -90deg, ${strokeColor} 0deg ${progressAngle}deg, var(--color-border) ${progressAngle}deg 360deg)`;

  return (
    <div style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
      <div
        style={{
          position: "relative",
          width: size,
          height: size,
          borderRadius: "50%",
          background: ringBackground,
          boxShadow: `0 0 0 1px color-mix(in srgb, ${strokeColor} 14%, transparent)`,
        }}
      >
        <div
          style={{
            position: "absolute",
            inset,
            borderRadius: "50%",
            background: "var(--color-surface)",
          }}
        />
        <div
          style={{
            position: "absolute",
            inset: 0,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: "var(--text-2xl)",
            fontWeight: 700,
            color: "var(--color-text)",
          }}
        >
          {Math.round(safeScore)}
        </div>
      </div>
      <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)", minHeight: "1.5em" }}>
        {label}
      </div>
    </div>
  );
}
