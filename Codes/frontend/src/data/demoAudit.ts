import type {
  AuditMode,
  IssueStatus,
  ProfileDetails,
  Severity,
} from "../types/audit";

const demoPageUrls = [
  "https://www.dell.com/en-ca/shop/laptop-computers/spd/dell16laptopdc16251",
  "https://www.dell.com/en-us/shop/laptop-computers/spd/dell16laptopdc16251",
  "https://www.dell.com/fr-ca/shop/laptop-computers/spd/dell16laptopdc16251",
];

export function demoPrompt(mode: AuditMode): string {
  return `Audit these pages against ${profileDetails[mode].label} checkpoints: ${demoPageUrls.join(", ")}. Show exact rule and HTML evidence.`;
}

export const statusLabels: Record<IssueStatus, string> = {
  new: "New",
  unresolved: "Unresolved",
  resolved: "Not reported",
  not_rechecked: "Not rechecked",
};

export const profileDetails: Record<AuditMode, ProfileDetails> = {
  sprint_launch: {
    label: "Sprint / Launch",
    description: "launch readiness PDP audit",
    helper:
      "Checks launch-critical content, localization, and presentation readiness.",
  },
  r2: {
    label: "R2",
    description: "pre-release PDP audit",
    helper:
      "Checks the R2 checkpoint set before the page moves toward release.",
  },
  r3: {
    label: "R3",
    description: "locale-aware PDP audit",
    helper:
      "Checks the R3 checkpoint set with locale and cross-page comparisons.",
  },
};

export const badgeColors: Record<
  Severity,
  "error" | "warning" | "informative" | "success"
> = {
  critical: "error",
  high: "error",
  medium: "warning",
  low: "informative",
};
