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
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct);
  const isFullCircle = pct >= 0.999;
  const strokeLinecap = pct > 0.08 && !isFullCircle ? "round" : "butt";

  const strokeColor = `hsl(${110 + pct * 18}, ${50 + pct * 10}%, ${54 - pct * 8}%)`;

  return (
    <div style={{ display: "inline-flex", flexDirection: "column", alignItems: "center", gap: "8px" }}>
      <svg width={size} height={size} style={{ transform: "rotate(-90deg)" }}>
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke="var(--color-border)" strokeWidth={6}
        />
        <circle
          cx={size / 2} cy={size / 2} r={radius}
          fill="none" stroke={strokeColor} strokeWidth={6}
          strokeLinecap={strokeLinecap}
          strokeDasharray={isFullCircle ? undefined : circumference}
          strokeDashoffset={isFullCircle ? undefined : offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div style={{ marginTop: `-${size / 2 + 16}px`, fontSize: "var(--text-2xl)", fontWeight: 700, color: "var(--color-text)" }}>
        {Math.round(safeScore)}
      </div>
      {label && <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)", marginTop: `${size / 2 - 24}px` }}>{label}</div>}
    </div>
  );
}
