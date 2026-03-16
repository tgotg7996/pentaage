interface LoadingSpinnerProps {
  size?: number;
  text?: string;
}

export default function LoadingSpinner({ size = 20, text }: LoadingSpinnerProps) {
  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "8px" }}>
      <svg width={size} height={size} viewBox="0 0 24 24" style={{ animation: "spin 1s linear infinite" }}>
        <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="3" opacity="0.25" />
        <path d="M12 2 A10 10 0 0 1 22 12" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      {text && <span>{text}</span>}
    </span>
  );
}
