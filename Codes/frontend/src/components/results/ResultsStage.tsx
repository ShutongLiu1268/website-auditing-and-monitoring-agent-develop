import { useState } from "react";
import {
  DDSBadge,
  DDSButton,
  DDSCard,
  DDSDrawer,
  DDSDrawerBody,
  DDSDrawerFooter,
  DDSMessageBar,
  DDSProgressBar,
  DDSSelect,
  DDSTab,
  DDSTabPanel,
  DDSTabs,
  DDSTabsBody,
  DDSTabsHeader,
} from "@dds/react";
import type {
  ComparisonResponse,
  CrossPageField,
  CrossPageValue,
  PromptTarget,
  TraceEntry,
} from "../../api/types";
import type { Finding, ProfileDetails, Severity } from "../../types/audit";

type Counts = Readonly<{
  critical: number;
  high: number;
  medium: number;
  resolved: number;
}>;

type ResultsStageProps = Readonly<{
  resultsProfile: ProfileDetails;
  activeFinding: Finding | null;
  activePage: string;
  activeTab: string;
  copied: boolean;
  counts: Counts;
  comparison: ComparisonResponse | null;
  comparisonGroups: Readonly<Record<string, Finding[]>>;
  trace: TraceEntry[];
  filteredFindings: ReadonlyArray<Finding>;
  findings: ReadonlyArray<Finding>;
  isRunning: boolean;
  runError: string | null;
  pageTargets: ReadonlyArray<PromptTarget>;
  partial: boolean;
  progress: number;
  severityFilter: string;
  setActiveFindingId: (id: string) => void;
  setActivePage: (page: string) => void;
  setActiveTab: (tab: string) => void;
  setSeverityFilter: (severity: string) => void;
  copyProof: (text: string) => void;
  badgeColors: Readonly<
    Record<Severity, "error" | "warning" | "informative" | "success">
  >;
  statusLabels: Readonly<Record<string, string>>;
}>;

const crossPageStatusLabel: Record<CrossPageField["status"], string> = {
  consistent: "Consistent",
  actionable: "Actionable",
  expected: "Expected",
};

const crossPageStatusColor: Record<
  CrossPageField["status"],
  "success" | "error" | "informative"
> = {
  consistent: "success",
  actionable: "error",
  expected: "informative",
};

const crossPageCategoryLabel: Record<CrossPageField["category"], string> = {
  invariant: "Invariant",
  market_sensitive: "Market-sensitive",
};

const transitionLabel: Record<string, string> = {
  new: "New",
  unresolved: "Unresolved",
  resolved: "Not reported",
  not_rechecked: "Not rechecked",
  changed_page: "Changed page",
};

function normalizeFact(value: string | null) {
  return value === null
    ? null
    : value.trim().toLowerCase().split(/\s+/).join(" ");
}

function majorityFact(values: CrossPageValue[]) {
  const counts = new Map<string | null, number>();
  for (const value of values) {
    const key = normalizeFact(value.value);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  let majority: string | null = null;
  let best = 0;
  for (const [key, count] of counts) {
    if (count > best) {
      majority = key;
      best = count;
    }
  }
  return majority;
}

function factMarker(
  field: CrossPageField,
  value: CrossPageValue,
  majority: string | null,
) {
  if (field.status === "consistent") return "match";
  if (field.status === "expected") return "market";
  return normalizeFact(value.value) === majority ? "match" : "diff";
}

function traceOutcomeRank(outcome: string) {
  if (outcome === "issue" || outcome === "error") return 0;
  if (outcome === "pass") return 1;
  return 2;
}

export function ResultsStage({
  resultsProfile,
  activeFinding,
  activePage,
  activeTab,
  copied,
  counts,
  comparison,
  comparisonGroups,
  trace,
  filteredFindings,
  findings,
  isRunning,
  runError,
  pageTargets,
  partial,
  progress,
  severityFilter,
  setActiveFindingId,
  setActivePage,
  setActiveTab,
  setSeverityFilter,
  copyProof,
  badgeColors,
  statusLabels,
}: ResultsStageProps) {
  const [captureOpen, setCaptureOpen] = useState(false);
  const [capturePage, setCapturePage] = useState<string | null>(null);
  const crossPageFields = comparison?.cross_page ?? [];
  const crossPageLocales =
    crossPageFields[0]?.values.map((value) => value.locale) ?? [];
  const crossPageColumns = `minmax(180px, 1.2fr) repeat(${crossPageLocales.length}, minmax(0, 1fr))`;
  const issueCount = `${findings.length} ${findings.length === 1 ? "issue" : "issues"}`;
  const pageCount = `${pageTargets.length} ${pageTargets.length === 1 ? "page" : "pages"} in scope`;
  let runStatusLabel = "Partial audit";
  if (isRunning) {
    runStatusLabel = "Agent is working";
  } else if (progress === 100 && !partial) {
    runStatusLabel = "Audit complete";
  }

  const applicableTrace = trace.filter(
    (entry) => entry.outcome !== "not_applicable",
  );
  const orderedTrace = [...applicableTrace].sort(
    (left, right) =>
      traceOutcomeRank(left.outcome) - traceOutcomeRank(right.outcome),
  );

  const captures =
    activeFinding?.members ?? (activeFinding ? [activeFinding] : []);
  const selectedCapture =
    captures.find((capture) => capture.page === capturePage) ??
    captures.find((capture) => capture.page === activePage) ??
    captures[0] ??
    null;

  return (
    <section className="results-stage" aria-label="Audit results">
      <div className="results-header">
        <div>
          <h2>{resultsProfile.label} review</h2>
        </div>
        <div className="run-status">
          <span
            className={`status-indicator ${isRunning ? "is-running" : ""}`}
          />
          <div>
            <strong>{runStatusLabel}</strong>
            <span>
              {isRunning
                ? `Rendering and applying ${resultsProfile.label} checkpoints`
                : `${issueCount} · ${pageCount} · ${resultsProfile.label}`}
            </span>
          </div>
        </div>
      </div>

      {runError && (
        <DDSMessageBar
          color="error"
          dismissible={false}
          className="run-message"
        >
          <strong>Audit API error.</strong> {runError}
        </DDSMessageBar>
      )}

      {isRunning && (
        <DDSMessageBar
          color="informative"
          dismissible={false}
          className="run-message"
        >
          <span>
            <strong>Agent is evaluating page evidence.</strong> Applying{" "}
            {resultsProfile.label} checkpoints one at a time keeps every finding
            traceable.
          </span>
        </DDSMessageBar>
      )}

      <div className="progress-strip">
        <div className="progress-copy">
          <span>Run progress</span>
          <strong>{progress}%</strong>
        </div>
        <DDSProgressBar
          value={progress}
          max={100}
          aria-label={`Audit progress ${progress}%`}
          size="sm"
        />
        <div className="progress-stages">
          <span className={progress >= 20 ? "done" : ""}>Render</span>
          <span className={progress >= 50 ? "done" : ""}>Extract</span>
          <span className={progress >= 76 ? "done" : ""}>Evaluate</span>
          <span className={progress === 100 ? "done" : ""}>Compare</span>
        </div>
      </div>

      <div className="metric-grid">
        <DDSCard className="metric-card metric-critical">
          <span className="metric-label">Critical</span>
          <strong>{counts.critical}</strong>
          <small>Needs immediate review</small>
        </DDSCard>
        <DDSCard className="metric-card metric-high">
          <span className="metric-label">High</span>
          <strong>{counts.high}</strong>
          <small>Across 2 locales</small>
        </DDSCard>
        <DDSCard className="metric-card metric-medium">
          <span className="metric-label">Medium</span>
          <strong>{counts.medium}</strong>
          <small>Language and specs</small>
        </DDSCard>
        <DDSCard className="metric-card metric-resolved">
          <span className="metric-label">Not reported</span>
          <strong>{counts.resolved}</strong>
          <small>Absent from this run</small>
        </DDSCard>
      </div>

      <DDSTabs
        activeTab={activeTab}
        onActiveTabChange={setActiveTab}
        className="results-tabs"
      >
        <DDSTabsHeader>
          <DDSTab id="findings">
            Findings <span className="tab-count">{findings.length}</span>
          </DDSTab>
          <DDSTab id="comparison">Cross-page comparison</DDSTab>
          <DDSTab id="trace">Rule trace</DDSTab>
        </DDSTabsHeader>
        <DDSTabsBody>
          <DDSTabPanel tab="findings">
            <div className="findings-toolbar">
              <div>
                <h3>Actionable findings</h3>
                <p>Sorted by severity, then source position.</p>
              </div>
              <div className="filter-row">
                <DDSSelect
                  value={activePage}
                  onChange={(event) => setActivePage(event.target.value)}
                  size="sm"
                  aria-label="Filter by page"
                >
                  <option value="ALL">All pages</option>
                  {pageTargets.map((target) => (
                    <option
                      key={target.url}
                      value={target.locale.toUpperCase()}
                    >
                      {target.locale.toUpperCase()}
                    </option>
                  ))}
                </DDSSelect>
                <DDSSelect
                  value={severityFilter}
                  onChange={(event) => setSeverityFilter(event.target.value)}
                  size="sm"
                  className="severity-select"
                  aria-label="Filter by severity"
                >
                  <option value="all">All severity</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                </DDSSelect>
              </div>
            </div>
            <div className="findings-layout">
              <div className="finding-list" aria-label="Findings list">
                {filteredFindings.map((finding) => (
                  <DDSButton
                    type="button"
                    size="sm"
                    block
                    kind="minimal"
                    color="neutral"
                    key={finding.id}
                    className={`finding-row ${activeFinding?.id === finding.id ? "selected" : ""}`}
                    onClick={() => setActiveFindingId(finding.id)}
                    aria-pressed={activeFinding?.id === finding.id}
                  >
                    <span
                      className={`severity-rail severity-${finding.severity}`}
                    />
                    <span className="finding-main">
                      <span className="finding-topline">
                        <DDSBadge
                          color={badgeColors[finding.severity]}
                          size="sm"
                        >
                          {finding.severity}
                        </DDSBadge>
                        <span className="finding-page">{finding.page}</span>
                        <span className="finding-status">
                          {statusLabels[finding.status]}
                        </span>
                      </span>
                      <strong>{finding.problem}</strong>
                      <span className="finding-snippet">
                        “{finding.snippet}”
                      </span>
                      <small>
                        {finding.rule} · {finding.category}
                      </small>
                    </span>
                    <span className="finding-arrow" aria-hidden="true">
                      →
                    </span>
                  </DDSButton>
                ))}
                {filteredFindings.length === 0 && (
                  <div className="empty-filter">
                    No findings match these filters.
                  </div>
                )}
              </div>

              {activeFinding && selectedCapture ? (
                <DDSCard className="evidence-card">
                  <div className="evidence-heading">
                    <div>
                      <p className="section-label">FINDING EVIDENCE</p>
                      <h3>
                        {activeFinding.category} <span>·</span>{" "}
                        {activeFinding.page}
                      </h3>
                    </div>
                    <DDSBadge
                      color={badgeColors[activeFinding.severity]}
                      size="sm"
                    >
                      {activeFinding.severity}
                    </DDSBadge>
                  </div>
                  {captures.length > 1 ? (
                    <div className="capture-switch">
                      {captures.map((capture) => (
                        <DDSButton
                          key={capture.page}
                          size="sm"
                          kind={
                            capture.page === selectedCapture.page
                              ? "outline"
                              : "minimal"
                          }
                          onClick={() => setCapturePage(capture.page)}
                        >
                          {capture.page}
                        </DDSButton>
                      ))}
                    </div>
                  ) : null}
                  {selectedCapture.captureUrl ? (
                    <DDSButton
                      size="sm"
                      kind="outline"
                      onClick={() => setCaptureOpen(true)}
                    >
                      Open captured page
                    </DDSButton>
                  ) : null}
                  <div className="evidence-rule">
                    <span>Checkpoint</span>
                    <strong>{activeFinding.rule}</strong>
                    <span className="ai-label">
                      {selectedCapture.evaluator}
                    </span>
                  </div>
                  <div className="evidence-block evidence-problem">
                    <span className="evidence-label">Problem</span>
                    <p>{selectedCapture.problem}</p>
                  </div>
                  {selectedCapture.reasoning ? (
                    <div className="evidence-block">
                      <span className="evidence-label">
                        Why the agent flagged this
                      </span>
                      <p>{selectedCapture.reasoning}</p>
                    </div>
                  ) : null}
                  <div className="evidence-block">
                    <span className="evidence-label">Suggested correction</span>
                    <p>{selectedCapture.correction}</p>
                  </div>
                  <div className="proof-panel">
                    <div className="proof-header">
                      <span className="evidence-label">Proof text</span>
                      <DDSButton
                        kind="minimal"
                        size="sm"
                        onClick={() => copyProof(selectedCapture.proof)}
                      >
                        {copied ? "Copied" : "Copy proof"}
                      </DDSButton>
                    </div>
                    <p>{selectedCapture.proof}</p>
                  </div>
                  <div className="locator-row">
                    <span>DOM locator</span>
                    <code>{selectedCapture.locator}</code>
                  </div>
                  <div className="evidence-footer">
                    <span>
                      <i className="confidence-dot" /> Evidence verified
                    </span>
                    <span>Confidence 0.94</span>
                  </div>
                </DDSCard>
              ) : null}
            </div>
          </DDSTabPanel>

          <DDSTabPanel tab="comparison">
            {crossPageFields.length > 0 ? (
              <>
                <div className="comparison-heading">
                  <div>
                    <h3>Cross-page comparison</h3>
                    <p>
                      Invariant facts must match across locale pages.
                      Market-sensitive facts may differ.
                    </p>
                  </div>
                  <DDSBadge color="informative" size="sm">
                    {crossPageFields.length} facts
                  </DDSBadge>
                </div>
                <div className="comparison-grid">
                  <div
                    className="comparison-head"
                    style={{ gridTemplateColumns: crossPageColumns }}
                  >
                    <span>Fact</span>
                    {crossPageLocales.map((locale) => (
                      <span key={locale}>{locale.toUpperCase()}</span>
                    ))}
                  </div>
                  {crossPageFields.map((field) => {
                    const majority = majorityFact(field.values);
                    return (
                      <div
                        className="comparison-line"
                        key={field.field}
                        style={{ gridTemplateColumns: crossPageColumns }}
                      >
                        <div>
                          <strong>{field.label}</strong>
                          <small>
                            {crossPageCategoryLabel[field.category]}
                          </small>
                          <DDSBadge
                            color={crossPageStatusColor[field.status]}
                            size="sm"
                          >
                            {crossPageStatusLabel[field.status]}
                          </DDSBadge>
                        </div>
                        {field.values.map((value) => (
                          <span
                            className={factMarker(field, value, majority)}
                            key={value.url}
                          >
                            {value.value ?? "Missing"}
                          </span>
                        ))}
                      </div>
                    );
                  })}
                </div>
              </>
            ) : null}

            <div className="comparison-heading">
              <div>
                <h3>Run comparison</h3>
                <p>
                  Dynamic status from the selected audit run and its previous
                  comparable run.
                </p>
              </div>
              <DDSBadge color="informative" size="sm">
                {comparison?.previous_run_id
                  ? "Previous run"
                  : "No previous run"}
              </DDSBadge>
            </div>
            {Object.values(comparisonGroups).some(
              (groups) => groups.length > 0,
            ) ? (
              <div className="comparison-grid">
                {Object.entries(comparisonGroups).flatMap(([status, groups]) =>
                  groups.map((group) => (
                    <div
                      className="comparison-line"
                      key={`${status}-${group.issueKey ?? group.id}`}
                    >
                      <strong>{transitionLabel[status] ?? status}</strong>
                      <span>{group.page}</span>
                      <span>
                        {group.problem}
                        <small>
                          {[
                            ...new Set(
                              (group.members ?? [group]).map(
                                (member) => member.category,
                              ),
                            ),
                          ].join(", ")}
                        </small>
                      </span>
                      <span className={`status-${status}`}>{group.rule}</span>
                    </div>
                  )),
                )}
              </div>
            ) : (
              <DDSMessageBar color="informative" dismissible={false}>
                No comparable run data is available yet.
              </DDSMessageBar>
            )}
          </DDSTabPanel>

          <DDSTabPanel tab="trace">
            <div className="trace-heading">
              <div>
                <h3>How the agent reasoned</h3>
                <p>
                  Each checkpoint applied to this run and the reason it passed
                  or failed.
                </p>
              </div>
              <DDSBadge color="informative" size="sm">
                {applicableTrace.length} checkpoints
              </DDSBadge>
            </div>
            <div className="trace-list">
              {applicableTrace.length ? (
                orderedTrace.map((entry, index) => (
                  <div className="trace-row" key={`${entry.rule}-${index}`}>
                    <span className="trace-number">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <div>
                      <strong>{entry.rule}</strong>
                      <small>
                        zone={entry.zone}
                        {entry.locales?.length
                          ? ` · ${entry.locales.join(", ")}`
                          : ""}{" "}
                        · {entry.detail}
                      </small>
                      {entry.evidence?.map((quote) => (
                        <code className="trace-evidence" key={quote}>
                          {quote}
                        </code>
                      ))}
                      {entry.reasoning ? (
                        <p className="trace-reasoning">{entry.reasoning}</p>
                      ) : null}
                    </div>
                    <span className="trace-method">
                      {entry.evaluator} · {entry.outcome}
                    </span>
                  </div>
                ))
              ) : (
                <DDSMessageBar color="informative" dismissible={false}>
                  {trace.length
                    ? "No applicable checkpoints for this run."
                    : "Rule trace will appear after a run completes."}
                </DDSMessageBar>
              )}
            </div>
          </DDSTabPanel>
        </DDSTabsBody>
      </DDSTabs>
      <DDSDrawer
        open={captureOpen}
        onOpenChange={setCaptureOpen}
        aria-label="Captured PDP page"
        size="lg"
      >
        <DDSDrawerBody>
          <h2 className="dds__heading--4 dds__m--none">Captured page</h2>
          {captures.length > 1 ? (
            <div className="capture-switch">
              {captures.map((capture) => (
                <DDSButton
                  key={capture.page}
                  size="sm"
                  kind={
                    capture.page === selectedCapture?.page
                      ? "outline"
                      : "minimal"
                  }
                  onClick={() => setCapturePage(capture.page)}
                >
                  {capture.page}
                </DDSButton>
              ))}
            </div>
          ) : null}
          {selectedCapture?.captureUrl ? (
            <iframe
              className="captured-page-frame"
              title="Captured PDP page"
              src={selectedCapture.captureUrl}
              sandbox=""
            />
          ) : null}
        </DDSDrawerBody>
        <DDSDrawerFooter>
          <DDSButton
            size="sm"
            kind="outline"
            onClick={() => setCaptureOpen(false)}
          >
            Close
          </DDSButton>
        </DDSDrawerFooter>
      </DDSDrawer>
    </section>
  );
}
