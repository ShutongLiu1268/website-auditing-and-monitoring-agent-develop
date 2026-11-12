import type { AuditMode } from "../types/audit";
import type {
  ApiIssue,
  ChatResponse,
  ChecklistResponse,
  ComparisonResponse,
  CrawlScope,
  DeliveryAttempt,
  PromptParseResponse,
  PromptRunResponse,
  RunStatusResponse,
  Schedule,
  TraceEntry,
} from "./types";

type ApiError = {
  error?: { message?: string };
  detail?: string;
};

export class ApiRequestError extends Error {
  readonly status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as ApiError;
    throw new ApiRequestError(
      body.error?.message ??
        body.detail ??
        `API request failed (${response.status})`,
      response.status,
    );
  }
  return (await response.json()) as T;
}

export function parsePrompt(prompt: string): Promise<PromptParseResponse> {
  return request<PromptParseResponse>("/api/prompt/parse", {
    method: "POST",
    body: JSON.stringify({ prompt }),
  });
}

export function queuePromptRun(
  prompt: string,
  mode: AuditMode,
  scope: CrawlScope,
): Promise<PromptRunResponse> {
  return request<PromptRunResponse>("/api/prompt/runs", {
    method: "POST",
    body: JSON.stringify({ prompt, mode, scope }),
  });
}

export function openRunActivity(runId: string): EventSource {
  return new EventSource(`${API_BASE_URL}/api/runs/${runId}/events`);
}

export function getRunStatus(runId: string): Promise<RunStatusResponse> {
  return request<RunStatusResponse>(`/api/runs/${runId}/status`);
}

function toApiIssue(issue: ApiIssue): ApiIssue {
  const capture = issue.captureUrl ?? issue.capture_url ?? null;
  return {
    ...issue,
    captureUrl: capture ? new URL(capture, API_BASE_URL).href : null,
    issueKey: issue.issue_key ?? issue.id,
  };
}

export async function getRunIssues(runId: string): Promise<ApiIssue[]> {
  const issues = await request<ApiIssue[]>(`/api/runs/${runId}/issues`);
  return issues.map(toApiIssue);
}

export async function getRunComparison(
  runId: string,
): Promise<ComparisonResponse> {
  const comparison = await request<ComparisonResponse>(
    `/api/runs/${runId}/comparison`,
  );
  return {
    ...comparison,
    statuses: Object.fromEntries(
      Object.entries(comparison.statuses).map(
        ([status, items]): [string, ApiIssue[]] => [
          status,
          items.map(toApiIssue),
        ],
      ),
    ),
  };
}

export function getRunTrace(runId: string): Promise<TraceEntry[]> {
  return request<TraceEntry[]>(`/api/runs/${runId}/trace`);
}

export function getRunChecklist(runId: string): Promise<ChecklistResponse> {
  return request<ChecklistResponse>(`/api/runs/${runId}/checklist`);
}

export function sendChat(message: string): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function listSchedules(): Promise<Schedule[]> {
  return request<Schedule[]>("/api/schedules");
}

export function createSchedule(
  input: Omit<Schedule, "id" | "next_run_at_utc" | "last_run_id">,
): Promise<Schedule> {
  return request<Schedule>("/api/schedules", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateSchedule(
  id: string,
  input: Partial<Schedule>,
): Promise<Schedule> {
  return request<Schedule>(`/api/schedules/${id}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export function deleteSchedule(id: string): Promise<void> {
  return request<void>(`/api/schedules/${id}`, { method: "DELETE" });
}

export function retryDelivery(id: string): Promise<DeliveryAttempt> {
  return request<DeliveryAttempt>(`/api/deliveries/${id}/retry`, {
    method: "POST",
  });
}

export function listDeliveries(scheduleId: string): Promise<DeliveryAttempt[]> {
  return request<DeliveryAttempt[]>(`/api/schedules/${scheduleId}/deliveries`);
}

export function runScheduleNow(scheduleId: string): Promise<DeliveryAttempt> {
  return request<DeliveryAttempt>(`/api/schedules/${scheduleId}/run-now`, {
    method: "POST",
  });
}
