import type { AuditMode, Finding } from "../types/audit";

export type CrawlScope = {
  include_paths: string[];
  exclude_paths: string[];
  page_limit: number;
  max_depth: number;
};

export type ChatResponse = {
  type: "clarification" | "confirmation" | "accepted" | "query";
  message: string;
  audit_id?: string | null;
  run_id?: string | null;
  command?: { action: string; clarification?: string | null } | null;
};

export type Schedule = {
  id: string;
  audit_definition_id: string;
  enabled: boolean;
  frequency: "daily" | "weekly";
  local_time: string;
  timezone: string;
  recipients: string[];
  next_run_at_utc: string;
  last_run_id?: string | null;
};

export type DeliveryAttempt = {
  id: string;
  schedule_id: string;
  run_id: string;
  recipients: string[];
  status: "queued" | "sent" | "failed";
  error_code?: string | null;
};

export type CrossPageValue = {
  locale: string;
  url: string;
  value: string | null;
};

export type CrossPageField = {
  field: string;
  label: string;
  category: "invariant" | "market_sensitive";
  status: "consistent" | "actionable" | "expected";
  values: CrossPageValue[];
};

export type ComparisonResponse = {
  run_id: string;
  previous_run_id?: string | null;
  statuses: Record<string, ApiIssue[]>;
  cross_page?: CrossPageField[];
};

export type TraceEntry = {
  rule: string;
  zone: string;
  outcome: string;
  evaluator: string;
  detail: string;
  reasoning?: string | null;
  locales?: string[];
  evidence?: string[];
};

export type ChecklistStatus =
  | "pending"
  | "pass"
  | "issues"
  | "error"
  | "not_evaluated"
  | "not_applicable";

export type ChecklistCounts = {
  total: number;
  checked: number;
  issues: number;
  not_evaluated: number;
  pending: number;
  not_applicable: number;
};

export type ChecklistCheckpoint = {
  id: string;
  label: string;
  status: ChecklistStatus;
  issues: number;
  pages: number;
};

export type ChecklistGroup = {
  title: string;
  counts: ChecklistCounts;
  checkpoints: ChecklistCheckpoint[];
};

export type ChecklistResponse = {
  run_id: string;
  rule_version: string;
  mode: string;
  run_status: ApiRunStatus;
  counts: ChecklistCounts;
  groups: ChecklistGroup[];
};

export type ApiRunStatus =
  | "queued"
  | "running"
  | "partial"
  | "completed"
  | "failed"
  | "cancelled";

export type PromptTarget = {
  url: string;
  locale: string;
};

export type PromptParseResponse = {
  targets: PromptTarget[];
  problems: string[];
};

export type PromptRunResponse = {
  audit_id: string;
  run_id: string;
  mode: AuditMode;
  targets: PromptTarget[];
};

export type ActivityEvent = {
  stage: string;
  message: string;
  page: string | null;
  at: string;
};

export type RunStatusResponse = {
  run_id: string;
  audit_definition_id: string;
  status: ApiRunStatus;
  progress: number;
  total_pages: number;
  completed_pages: number;
  failed_pages: number;
  warnings: string[];
  coverage: {
    scanned: number;
    skipped: number;
    inaccessible: number;
    duplicate: number;
    timeout: number;
  };
  started_at?: string | null;
  completed_at?: string | null;
  pages: Array<{
    url: string;
    locale: string;
    status: string;
    reason?: string | null;
  }>;
};

export type ApiIssue = Finding & {
  run_id: string;
  confidence: number;
  review_required: boolean;
  capture_url?: string | null;
  issue_key?: string | null;
};
