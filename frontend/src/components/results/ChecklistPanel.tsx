import { useState } from "react";
import {
  DDSAccordion,
  DDSAccordionContent,
  DDSAccordionHeading,
  DDSAccordionItem,
  DDSBadge,
  DDSCheckbox,
  DDSMessageBar,
  DDSProgressBar,
} from "@dds/react";
import type { ChecklistResponse } from "../../api/types";
import { statusMeta, visibleGroups } from "../../utils/checklist";

type ChecklistPanelProps = Readonly<{
  checklist: ChecklistResponse | null;
  error: string | null;
}>;

export function ChecklistPanel({ checklist, error }: ChecklistPanelProps) {
  const [showNotApplicable, setShowNotApplicable] = useState(false);
  if (!checklist) {
    return (
      <DDSMessageBar
        color={error ? "warning" : "informative"}
        dismissible={false}
      >
        {error
          ? `Checklist unavailable (${error}). Restart the backend if this persists.`
          : "Checklist appears when a run starts."}
      </DDSMessageBar>
    );
  }
  const { counts } = checklist;
  const groups = visibleGroups(checklist.groups, showNotApplicable);
  return (
    <div className="checklist-body">
      <div className="checklist-meta">
        <p>
          Guide {checklist.rule_version.slice(0, 8)} ·{" "}
          {checklist.mode.toUpperCase()}
        </p>
        <DDSProgressBar
          value={counts.checked}
          max={Math.max(counts.total, 1)}
          size="sm"
          aria-label={`${counts.checked} of ${counts.total} checkpoints checked`}
        />
        <p>
          {counts.checked} of {counts.total} checked · {counts.issues} with
          issues
        </p>
        <label className="checklist-toggle">
          <DDSCheckbox
            checked={showNotApplicable}
            onChange={(event) => setShowNotApplicable(event.target.checked)}
          />
          Show not applicable ({counts.not_applicable})
        </label>
      </div>
      {groups.length ? (
        <DDSAccordion
          multiple
          defaultExpandedItems={groups.map((group) => group.title)}
        >
          {groups.map((group) => (
            <DDSAccordionItem key={group.title} id={group.title}>
              <DDSAccordionHeading>
                {group.title} · {group.counts.checked} of {group.counts.total}{" "}
                checked
              </DDSAccordionHeading>
              <DDSAccordionContent>
                <ul className="checklist-rows">
                  {group.checkpoints.map((checkpoint) => (
                    <li className="checklist-row" key={checkpoint.id}>
                      <span>{checkpoint.label}</span>
                      <DDSBadge
                        color={statusMeta[checkpoint.status].color}
                        size="sm"
                      >
                        {statusMeta[checkpoint.status].label}
                      </DDSBadge>
                    </li>
                  ))}
                </ul>
              </DDSAccordionContent>
            </DDSAccordionItem>
          ))}
        </DDSAccordion>
      ) : (
        <DDSMessageBar color="informative" dismissible={false}>
          No applicable checkpoints for this run.
        </DDSMessageBar>
      )}
    </div>
  );
}
