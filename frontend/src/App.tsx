import { useCallback, useMemo, useState } from "react";
import { DDSButton, DDSModal, DDSModalBody, DDSModalHeader } from "@dds/react";
import "./App.css";
import { ChatPanel } from "./components/chat/ChatPanel";
import { CommandRail } from "./components/audit/CommandRail";
import { ScopeEditor } from "./components/audit/ScopeEditor";
import { ComparisonFilters } from "./components/results/ComparisonFilters";
import { CoverageBanner } from "./components/results/CoverageBanner";
import { ResultsStage } from "./components/results/ResultsStage";
import { RightRail } from "./components/results/RightRail";
import { SchedulePanel } from "./components/schedules/SchedulePanel";
import { TopBar } from "./components/shell/TopBar";
import {
  badgeColors,
  demoPrompt,
  profileDetails,
  statusLabels,
} from "./data/demoAudit";
import { useAuditRun } from "./hooks/useAuditRun";
import { useTheme } from "./hooks/useTheme";
import { groupIssues, sortBySeverity } from "./utils/findings";
import type { CrawlScope } from "./api/types";
import type { AuditMode, Finding, IssueStatus, Severity } from "./types/audit";

const demoMode = import.meta.env.VITE_DEMO_MODE === "true";

function App() {
  const [prompt, setPrompt] = useState(() =>
    demoMode ? demoPrompt("r3") : "",
  );
  const [mode, setMode] = useState<AuditMode>("r3");
  const [activeTab, setActiveTab] = useState("findings");
  const [activePage, setActivePage] = useState("ALL");
  const [severityFilter, setSeverityFilter] = useState<Severity | "all">("all");
  const [comparisonStatus, setComparisonStatus] = useState<IssueStatus | "all">(
    "all",
  );
  const [activeFindingId, setActiveFindingId] = useState("");
  const [copied, setCopied] = useState(false);
  const [scheduleModalOpen, setScheduleModalOpen] = useState(false);
  const [scanOptionsOpen, setScanOptionsOpen] = useState(false);
  const [scope, setScope] = useState<CrawlScope>({
    include_paths: [],
    exclude_paths: [],
    page_limit: 5,
    max_depth: 0,
  });
  const {
    themeMode,
    setThemeMode,
    resolvedTheme,
    themeMenuOpen,
    setThemeMenuOpen,
    themeOptions,
    themeIconNames,
  } = useTheme();
  const {
    startPromptRun,
    activity,
    runTargets,
    progress,
    findings: apiFindings,
    error: auditError,
    runStatus,
    comparison,
    trace,
    checklist,
    checklistError,
    auditDefinitionId,
    isRunning,
    runMode,
  } = useAuditRun();

  const activeProfile = profileDetails[mode];
  const resultsProfile = profileDetails[runMode ?? (demoMode ? "r3" : mode)];
  const findings = useMemo(
    () => sortBySeverity(groupIssues(apiFindings)),
    [apiFindings],
  );
  const comparisonGroups = useMemo(
    () =>
      Object.fromEntries(
        Object.entries(comparison?.statuses ?? {}).map(
          ([status, items]): [string, Finding[]] => [
            status,
            groupIssues(items),
          ],
        ),
      ),
    [comparison],
  );
  const filteredFindings = useMemo(
    () =>
      findings.filter((finding) => {
        const matchesPage =
          activePage === "ALL" ||
          (finding.pages ?? [finding.page]).includes(activePage);
        const matchesSeverity =
          severityFilter === "all" || finding.severity === severityFilter;
        const matchesStatus =
          comparisonStatus === "all" || finding.status === comparisonStatus;
        return matchesPage && matchesSeverity && matchesStatus;
      }),
    [activePage, comparisonStatus, findings, severityFilter],
  );

  const activeFinding: Finding | null =
    filteredFindings.find((finding) => finding.id === activeFindingId) ??
    filteredFindings[0] ??
    null;

  const counts = {
    critical: findings.filter((finding) => finding.severity === "critical")
      .length,
    high: findings.filter((finding) => finding.severity === "high").length,
    medium: findings.filter((finding) => finding.severity === "medium").length,
    resolved: comparisonGroups.resolved?.length ?? 0,
  };

  const handleModeChange = (nextMode: AuditMode) => {
    setMode(nextMode);
    if (demoMode) setPrompt(demoPrompt(nextMode));
  };

  const runAudit = useCallback(() => {
    setCopied(false);
    void startPromptRun(prompt, mode, scope);
  }, [mode, prompt, scope, startPromptRun]);

  const copyProof = (text: string) => {
    void navigator.clipboard?.writeText(text);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className={`app-shell dds--${resolvedTheme}-mode`}>
      <TopBar
        activeProfile={activeProfile}
        themeMode={themeMode}
        themeMenuOpen={themeMenuOpen}
        setThemeMode={setThemeMode}
        setThemeMenuOpen={setThemeMenuOpen}
        themeOptions={themeOptions}
        themeIconNames={themeIconNames}
        resolvedTheme={resolvedTheme}
      />
      <main className="workspace">
        <aside className="scan-pane" aria-label="Scan controls">
          <CommandRail
            prompt={prompt}
            setPrompt={setPrompt}
            mode={mode}
            activeProfile={activeProfile}
            handleModeChange={handleModeChange}
            isRunning={isRunning}
            runAudit={runAudit}
          />
          <div className="workflow-support">
            <DDSButton
              size="sm"
              kind="outline"
              block
              onClick={() => setScanOptionsOpen(true)}
            >
              Scan options
            </DDSButton>
            <DDSButton
              size="sm"
              kind="outline"
              block
              onClick={() => setScheduleModalOpen(true)}
            >
              Open schedules
            </DDSButton>
          </div>
        </aside>
        <section className="results-pane">
          <CoverageBanner status={runStatus} />
          <ResultsStage
            resultsProfile={resultsProfile}
            activeFinding={activeFinding}
            activePage={activePage}
            activeTab={activeTab}
            copied={copied}
            counts={counts}
            comparison={comparison}
            comparisonGroups={comparisonGroups}
            trace={trace}
            filteredFindings={filteredFindings}
            findings={findings}
            isRunning={isRunning}
            runError={auditError}
            pageTargets={runTargets}
            partial={runStatus?.status === "partial"}
            progress={progress}
            severityFilter={severityFilter}
            setActiveFindingId={setActiveFindingId}
            setActivePage={setActivePage}
            setActiveTab={setActiveTab}
            setSeverityFilter={(value) =>
              setSeverityFilter(value as Severity | "all")
            }
            copyProof={copyProof}
            badgeColors={badgeColors}
            statusLabels={statusLabels}
          />
        </section>
        <RightRail
          activity={activity}
          checklist={checklist}
          checklistError={checklistError}
          isRunning={isRunning}
        />
      </main>
      <DDSModal
        open={scanOptionsOpen}
        onOpenChange={setScanOptionsOpen}
        aria-labelledby="scan-options-title"
        lightDismiss
      >
        <DDSModalHeader>
          <h2 id="scan-options-title" className="dds__heading--4 dds__m--none">
            Scan options
          </h2>
        </DDSModalHeader>
        <DDSModalBody>
          <ChatPanel />
          <ScopeEditor scope={scope} onChange={setScope} />
          <ComparisonFilters
            status={comparisonStatus}
            severity={severityFilter}
            onStatusChange={setComparisonStatus}
            onSeverityChange={setSeverityFilter}
          />
        </DDSModalBody>
      </DDSModal>
      <DDSModal
        open={scheduleModalOpen}
        onOpenChange={setScheduleModalOpen}
        aria-labelledby="schedule-modal-title"
        lightDismiss
      >
        <DDSModalHeader>
          <h2
            id="schedule-modal-title"
            className="dds__heading--4 dds__m--none"
          >
            Recurring audit schedules
          </h2>
        </DDSModalHeader>
        <DDSModalBody>
          <SchedulePanel auditDefinitionId={auditDefinitionId ?? undefined} />
        </DDSModalBody>
      </DDSModal>
    </div>
  );
}

export default App;
