import { useCallback, useEffect, useRef, useState } from "react";
import {
  getRunChecklist,
  getRunComparison,
  getRunIssues,
  getRunStatus,
  getRunTrace,
  openRunActivity,
  queuePromptRun,
} from "../api/client";
import type {
  ActivityEvent,
  ApiIssue,
  ApiRunStatus,
  ChecklistResponse,
  ComparisonResponse,
  CrawlScope,
  PromptTarget,
  RunStatusResponse,
  TraceEntry,
} from "../api/types";
import type { AuditMode } from "../types/audit";

const TERMINAL_STATUSES = new Set<ApiRunStatus>([
  "completed",
  "partial",
  "failed",
  "cancelled",
]);

const wait = (milliseconds: number) =>
  new Promise((resolve) => window.setTimeout(resolve, milliseconds));

export function useAuditRun() {
  const [status, setStatus] = useState<ApiRunStatus | "idle">("idle");
  const [progress, setProgress] = useState(0);
  const [findings, setFindings] = useState<ApiIssue[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [runStatus, setRunStatus] = useState<RunStatusResponse | null>(null);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [trace, setTrace] = useState<TraceEntry[]>([]);
  const [checklist, setChecklist] = useState<ChecklistResponse | null>(null);
  const [checklistError, setChecklistError] = useState<string | null>(null);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [runTargets, setRunTargets] = useState<PromptTarget[]>([]);
  const [auditDefinitionId, setAuditDefinitionId] = useState<string | null>(
    null,
  );
  const [runMode, setRunMode] = useState<AuditMode | null>(null);
  const runToken = useRef(0);
  const mounted = useRef(false);
  const activitySource = useRef<EventSource | null>(null);

  const refreshChecklist = useCallback(async (runId: string, token: number) => {
    try {
      const next = await getRunChecklist(runId);
      if (!mounted.current || runToken.current !== token) return;
      setChecklist(next);
      setChecklistError(null);
    } catch (checklistFailure) {
      if (!mounted.current || runToken.current !== token) return;
      setChecklistError(
        checklistFailure instanceof Error
          ? checklistFailure.message
          : "Checklist unavailable",
      );
    }
  }, []);

  const startPromptRun = useCallback(
    async (prompt: string, mode: AuditMode, scope: CrawlScope) => {
      const token = ++runToken.current;
      activitySource.current?.close();
      activitySource.current = null;
      setStatus("queued");
      setProgress(0);
      setFindings([]);
      setComparison(null);
      setTrace([]);
      setChecklist(null);
      setChecklistError(null);
      setActivity([]);
      setRunTargets([]);
      setError(null);
      setRunMode(mode);

      try {
        const started = await queuePromptRun(prompt, mode, scope);
        if (!mounted.current || runToken.current !== token) return;
        setAuditDefinitionId(started.audit_id);
        setRunTargets(started.targets);

        const source = openRunActivity(started.run_id);
        activitySource.current = source;
        source.addEventListener("activity", (event) => {
          if (runToken.current !== token) return;
          setActivity((events) => [
            ...events,
            JSON.parse(event.data) as ActivityEvent,
          ]);
        });
        source.addEventListener("done", () => source.close());

        let current = await getRunStatus(started.run_id);
        setRunStatus(current);

        let tick = 0;
        while (!TERMINAL_STATUSES.has(current.status)) {
          if (!mounted.current || runToken.current !== token) return;
          setStatus(current.status);
          setProgress(current.progress);
          setRunStatus(current);
          if (tick % 4 === 0) void refreshChecklist(started.run_id, token);
          tick += 1;
          await wait(500);
          current = await getRunStatus(started.run_id);
        }

        if (!mounted.current || runToken.current !== token) return;
        setStatus(current.status);
        setProgress(current.progress);
        setRunStatus(current);
        const [nextFindings, nextComparison, nextTrace] = await Promise.all([
          getRunIssues(started.run_id),
          getRunComparison(started.run_id),
          getRunTrace(started.run_id),
        ]);
        setFindings(nextFindings);
        setComparison(nextComparison);
        setTrace(nextTrace);
        void refreshChecklist(started.run_id, token);
      } catch (runError) {
        if (!mounted.current || runToken.current !== token) return;
        setStatus("failed");
        setError(
          runError instanceof Error ? runError.message : "Audit run failed",
        );
      }
    },
    [refreshChecklist],
  );

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      activitySource.current?.close();
    };
  }, []);

  return {
    startPromptRun,
    status,
    progress,
    findings,
    error,
    runStatus,
    comparison,
    trace,
    checklist,
    checklistError,
    activity,
    runTargets,
    auditDefinitionId,
    runMode,
    isRunning: status === "queued" || status === "running",
  };
}
