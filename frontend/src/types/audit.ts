export type Severity = "critical" | "high" | "medium" | "low";
export type IssueStatus = "new" | "unresolved" | "resolved" | "not_rechecked";
export type AuditMode = "sprint_launch" | "r2" | "r3";
export type ThemeMode = "light" | "dark" | "system";
export type ResolvedTheme = "light" | "dark";

export type Finding = {
  id: string;
  severity: Severity;
  status: IssueStatus;
  rule: string;
  category: string;
  page: string;
  locale: string;
  snippet: string;
  problem: string;
  correction: string;
  proof: string;
  locator: string;
  evaluator: string;
  captureUrl?: string | null;
  reasoning?: string | null;
  issueKey?: string | null;
  pages?: string[];
  members?: Finding[];
};

export type PageTarget = {
  label: string;
  locale: string;
  url: string;
  displayUrl?: string;
};

export type ProfileDetails = {
  label: string;
  description: string;
  helper: string;
};
