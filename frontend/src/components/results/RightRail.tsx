import { useEffect, useRef } from "react";
import { DDSBadge, DDSCard, DDSMessageBar } from "@dds/react";
import type { ActivityEvent, ChecklistResponse } from "../../api/types";
import { ChecklistPanel } from "./ChecklistPanel";

type RightRailProps = Readonly<{
  activity: ReadonlyArray<ActivityEvent>;
  checklist: ChecklistResponse | null;
  checklistError: string | null;
  isRunning: boolean;
}>;

export function RightRail({
  activity,
  checklist,
  checklistError,
  isRunning,
}: RightRailProps) {
  const activityListRef = useRef<HTMLOListElement | null>(null);
  useEffect(() => {
    const list = activityListRef.current;
    if (list) list.scrollTop = list.scrollHeight;
  }, [activity.length]);
  return (
    <aside className="right-rail" aria-label="Bot activity and checklist">
      <DDSCard className="activity-card">
        <div className="activity-heading">
          <div>
            <p className="section-label">BOT ACTIVITY</p>
            <h3>What the agent is doing</h3>
          </div>
          <DDSBadge color={isRunning ? "informative" : "success"} size="sm">
            {isRunning ? "Live" : "Recorded"}
          </DDSBadge>
        </div>
        {activity.length ? (
          <ol
            className="activity-list"
            aria-live="polite"
            ref={activityListRef}
          >
            {activity.map((event, index) => (
              <li key={`${event.at}-${index}`}>
                <span className="activity-stage">{event.stage}</span>
                <span>{event.message}</span>
              </li>
            ))}
          </ol>
        ) : (
          <DDSMessageBar color="informative" dismissible={false}>
            Bot activity appears here once a run starts.
          </DDSMessageBar>
        )}
      </DDSCard>
      <DDSCard className="checklist-card">
        <div className="activity-heading">
          <div>
            <p className="section-label">CHECKLIST</p>
            <h3>Guide checkpoints</h3>
          </div>
        </div>
        <ChecklistPanel checklist={checklist} error={checklistError} />
      </DDSCard>
    </aside>
  );
}
