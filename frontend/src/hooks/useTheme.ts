import { useCallback, useEffect, useState } from "react";

type ThemeMode = "system" | "light" | "dark";

function getSystemTheme(): "light" | "dark" {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function applyTheme(mode: ThemeMode): void {
  const root = document.documentElement;
  if (mode === "system") {
    root.removeAttribute("data-theme");
  } else {
    root.setAttribute("data-theme", mode);
  }
}

export function useTheme() {
  const [mode, setMode] = useState<ThemeMode>(() => {
    const saved = localStorage.getItem("theme-mode");
    return (saved as ThemeMode) || "system";
  });

  const resolvedTheme = mode === "system" ? getSystemTheme() : mode;

  useEffect(() => {
    applyTheme(mode);
    localStorage.setItem("theme-mode", mode);
  }, [mode]);

  // 监听系统主题变化
  useEffect(() => {
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => {
      if (mode === "system") {
        // 强制触发重渲染
        setMode("system");
      }
    };
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [mode]);

  const toggleTheme = useCallback(() => {
    setMode((prev) => {
      const next: Record<ThemeMode, ThemeMode> = {
        system: "light",
        light: "dark",
        dark: "system",
      };
      return next[prev];
    });
  }, []);

  return { mode, resolvedTheme, toggleTheme };
}
