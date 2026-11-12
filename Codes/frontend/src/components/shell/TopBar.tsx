import { DDSBadge } from "@dds/react";
import type { ProfileDetails, ThemeMode } from "../../types/audit";
import { ThemeMenu } from "../theme/ThemeMenu";

type TopBarProps = Readonly<{
  activeProfile: ProfileDetails;
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

export function TopBar({
  activeProfile,
  themeMode,
  themeMenuOpen,
  setThemeMode,
  setThemeMenuOpen,
  themeOptions,
  themeIconNames,
  resolvedTheme,
}: TopBarProps) {
  return (
    <header className="topbar">
      <div className="brand-lockup">
        <div className="brand-mark" aria-hidden="true">
          D
        </div>
        <div>
          <p className="eyebrow">NPL QUALITY ENGINEERING</p>
          <p className="brand-name">PDP Audit Copilot</p>
        </div>
      </div>
      <div className="topbar-meta">
        <DDSBadge
          color="success"
          size="sm"
          title="Bundled PDP checkpoint guide is loaded and ready"
        >
          Rules ready
        </DDSBadge>
        <span
          className="framework-version"
          title={`${activeProfile.label} is the selected PDP review checkpoint profile`}
        >
          Profile: {activeProfile.label} · v0.1.0
        </span>
        <ThemeMenu
          themeMode={themeMode}
          themeMenuOpen={themeMenuOpen}
          setThemeMode={setThemeMode}
          setThemeMenuOpen={setThemeMenuOpen}
          themeOptions={themeOptions}
          themeIconNames={themeIconNames}
          resolvedTheme={resolvedTheme}
        />
      </div>
    </header>
  );
}
