interface ScoreCircleProps {
  score: number;
  maxScore?: number;
  size?: number;
  label?: string;
}

export default function ScoreCircle({ score, maxScore = 100, size = 120, label }: ScoreCircleProps) {
  const pct = Math.min(score / maxScore, 1);
  const radius = (size - 12) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct);

  // 颜色随分值变化
  const hue = pct * 120; // 0=红 → 60=黄 → 120=绿
  const strokeColor = `hsl(${hue}, 60%, 45%)`;

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
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease" }}
        />
      </svg>
      <div style={{ marginTop: `-${size / 2 + 16}px`, fontSize: "var(--text-2xl)", fontWeight: 700, color: "var(--color-text)" }}>
        {Math.round(score)}
      </div>
      {label && <div style={{ fontSize: "var(--text-sm)", color: "var(--color-text-secondary)", marginTop: `${size / 2 - 24}px` }}>{label}</div>}
    </div>
  );
}
