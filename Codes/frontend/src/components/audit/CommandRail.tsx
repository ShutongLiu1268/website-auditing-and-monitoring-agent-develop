import {
  DDSBadge,
  DDSButton,
  DDSCard,
  DDSFormField,
  DDSHelperText,
  DDSLabel,
  DDSMessageBar,
  DDSSelect,
  DDSTextArea,
} from "@dds/react";
import { usePromptPreview } from "../../hooks/usePromptPreview";
import type { AuditMode, ProfileDetails } from "../../types/audit";

type CommandRailProps = Readonly<{
  prompt: string;
  setPrompt: (prompt: string) => void;
  mode: AuditMode;
  activeProfile: ProfileDetails;
  handleModeChange: (mode: AuditMode) => void;
  isRunning: boolean;
  runAudit: () => void;
}>;

export function CommandRail({
  prompt,
  setPrompt,
  mode,
  activeProfile,
  handleModeChange,
  isRunning,
  runAudit,
}: CommandRailProps) {
  const preview = usePromptPreview(prompt);
  const canRun =
    preview.targets.length > 0 &&
    preview.problems.length === 0 &&
    !preview.pending;

  return (
    <aside className="command-rail" aria-label="Audit configuration">
      <div className="rail-heading">
        <div>
          <p className="eyebrow">COMMAND CENTER</p>
          <h1>Run an audit</h1>
        </div>
        <DDSBadge color="informative" size="sm">
          Manual
        </DDSBadge>
      </div>

      <div className="rail-section scan-type-section">
        <div className="section-label-row">
          <p className="section-label">SCAN TYPE</p>
          <span className="section-count">GLOBAL</span>
        </div>
        <DDSFormField>
          <DDSLabel htmlFor="audit-mode">Review profile</DDSLabel>
          <DDSSelect
            id="audit-mode"
            value={mode}
            onChange={(event) =>
              handleModeChange(event.target.value as AuditMode)
            }
            size="sm"
            aria-describedby="profile-helper"
          >
            <option value="sprint_launch">Sprint / Launch</option>
            <option value="r2">R2</option>
            <option value="r3">R3</option>
          </DDSSelect>
          <DDSHelperText id="profile-helper">
            {activeProfile.helper}
          </DDSHelperText>
        </DDSFormField>
      </div>

      <DDSCard variant="ai" className="prompt-card">
        <div className="card-kicker">
          <span className="pulse-dot" aria-hidden="true" />
          <span>Agent prompt</span>
        </div>
        <DDSFormField>
          <DDSLabel htmlFor="audit-prompt">What should I inspect?</DDSLabel>
          <DDSTextArea
            id="audit-prompt"
            aria-describedby="prompt-helper"
            value={prompt}
            onChange={(event) => setPrompt(event.target.value)}
            rows={7}
            size="sm"
            variant="ai"
          />
          <DDSHelperText id="prompt-helper">
            Include the PDP URLs and their locales, for example
            https://www.dell.com/en-ca/…
            {!preview.targets.length && !preview.pending
              ? " Add an HTTPS PDP URL to enable the audit."
              : ""}
          </DDSHelperText>
        </DDSFormField>
        <div className="prompt-actions">
          <DDSButton
            variant="ai"
            kind="filled"
            size="sm"
            block
            onClick={runAudit}
            inactive={isRunning || !canRun}
          >
            {isRunning ? "Auditing pages…" : "Run agent audit"}
          </DDSButton>
          <span className="shortcut">⌘ ↵</span>
        </div>
      </DDSCard>

      <div className="rail-section target-section">
        <div className="section-label-row">
          <p className="section-label">PAGES FROM PROMPT</p>
          <span className="section-count">
            {String(preview.targets.length).padStart(2, "0")}
          </span>
        </div>
        {preview.problems.map((problem) => (
          <DDSMessageBar key={problem} color="warning" dismissible={false}>
            {problem}
          </DDSMessageBar>
        ))}
        <div className="target-list">
          {preview.targets.map((target) => (
            <div className="target-row-readonly" key={target.url}>
              <strong>{target.locale}</strong>
              <small>{target.url}</small>
            </div>
          ))}
        </div>
      </div>
    </aside>
  );
}
