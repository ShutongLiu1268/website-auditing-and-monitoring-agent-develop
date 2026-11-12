import { DDSButton, DDSIcon } from "@dds/react";
import type { ThemeMode } from "../../types/audit";

type ThemeMenuProps = Readonly<{
  themeMode: ThemeMode;
  themeMenuOpen: boolean;
  setThemeMode: (mode: ThemeMode) => void;
  setThemeMenuOpen: (open: boolean) => void;
  themeOptions: ReadonlyArray<{ value: ThemeMode; label: string }>;
  themeIconNames: Readonly<
    Record<ThemeMode, "brightness" | "moon" | "device-laptop">
  >;
  resolvedTheme: "light" | "dark";
}>;

export function ThemeMenu({
  themeMode,
  themeMenuOpen,
  setThemeMode,
  setThemeMenuOpen,
  themeOptions,
  themeIconNames,
  resolvedTheme,
}: ThemeMenuProps) {
  return (
    <div className="theme-menu">
      <DDSButton
        className="theme-trigger"
        type="button"
        size="sm"
        iconOnly
        kind="minimal"
        color="neutral"
        aria-label={`Theme mode: ${themeMode}`}
        aria-expanded={themeMenuOpen}
        aria-haspopup="menu"
        title={`Theme mode: ${themeMode}`}
        onClick={() => setThemeMenuOpen(!themeMenuOpen)}
      >
        <DDSIcon name={themeIconNames[themeMode]} size="sm" />
        <span className="theme-caret" aria-hidden="true">
          ▾
        </span>
        <span className="sr-only">Theme</span>
      </DDSButton>
      {themeMenuOpen && (
        <div
          className="theme-menu-panel"
          role="menu"
          aria-label="Theme options"
        >
          {themeOptions.map((option) => (
            <DDSButton
              key={option.value}
              size="sm"
              kind={themeMode === option.value ? "filled" : "minimal"}
              color={themeMode === option.value ? "brand" : "neutral"}
              aria-checked={themeMode === option.value}
              role="menuitemradio"
              onClick={() => {
                setThemeMode(option.value);
                setThemeMenuOpen(false);
              }}
            >
              {option.label}
              {option.value === "system" && ` (${resolvedTheme})`}
            </DDSButton>
          ))}
        </div>
      )}
    </div>
  );
}
