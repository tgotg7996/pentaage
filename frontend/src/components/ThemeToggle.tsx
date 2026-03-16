import type { CSSProperties } from "react";

interface ThemeToggleProps {
  mode: "system" | "light" | "dark";
  onToggle: () => void;
}

const iconMap = {
  light: "☀️",
  dark: "🌙",
  system: "💻",
};

const labelMap = {
  light: "浅色模式",
  dark: "深色模式",
  system: "跟随系统",
};

const buttonStyle: CSSProperties = {
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  width: 40,
  height: 40,
  borderRadius: "var(--radius-full)",
  border: "1px solid var(--color-border)",
  background: "var(--color-surface)",
  fontSize: "1.2rem",
  cursor: "pointer",
  transition: "all var(--transition-fast)",
};

export default function ThemeToggle({ mode, onToggle }: ThemeToggleProps) {
  return (
    <button
      type="button"
      onClick={onToggle}
      style={buttonStyle}
      title={labelMap[mode]}
      aria-label={labelMap[mode]}
    >
      {iconMap[mode]}
    </button>
  );
}
