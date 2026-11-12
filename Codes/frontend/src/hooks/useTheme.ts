import { useEffect, useState } from "react";
import type { ResolvedTheme, ThemeMode } from "../types/audit";

const themeOptions: Array<{ value: ThemeMode; label: string }> = [
  { value: "light", label: "Light" },
  { value: "dark", label: "Dark" },
  { value: "system", label: "System" },
];

const themeIconNames: Record<
  ThemeMode,
  "brightness" | "moon" | "device-laptop"
> = {
  light: "brightness",
  dark: "moon",
  system: "device-laptop",
};

function getInitialThemeMode(): ThemeMode {
  const stored = window.localStorage.getItem("pdp-audit-theme");
  return stored === "light" || stored === "dark" || stored === "system"
    ? stored
    : "system";
}

function getResolvedTheme(mode: ThemeMode): ResolvedTheme {
  if (mode !== "system") return mode;
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function useTheme() {
  const [themeMode, setThemeMode] = useState<ThemeMode>(getInitialThemeMode);
  const [resolvedTheme, setResolvedTheme] = useState<ResolvedTheme>(() =>
    getResolvedTheme(getInitialThemeMode()),
  );
  const [themeMenuOpen, setThemeMenuOpen] = useState(false);

  useEffect(() => {
    const syncTheme = () => {
      const nextTheme = getResolvedTheme(themeMode);
      const root = document.documentElement;
      root.classList.remove("dds--light-mode", "dds--dark-mode");
      root.classList.add(`dds--${nextTheme}-mode`);
      root.style.colorScheme = nextTheme;
      setResolvedTheme(nextTheme);
    };

    window.localStorage.setItem("pdp-audit-theme", themeMode);
    syncTheme();

    if (themeMode !== "system") return undefined;
    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");
    mediaQuery.addEventListener("change", syncTheme);
    return () => mediaQuery.removeEventListener("change", syncTheme);
  }, [themeMode]);

  return {
    themeMode,
    setThemeMode,
    resolvedTheme,
    themeMenuOpen,
    setThemeMenuOpen,
    themeOptions,
    themeIconNames,
  };
}
