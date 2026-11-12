import { useState } from "react";
import {
  DDSBadge,
  DDSButton,
  DDSCard,
  DDSFormField,
  DDSHelperText,
  DDSLabel,
  DDSSelect,
  DDSTextInput,
} from "@dds/react";
import {
  createSchedule,
  deleteSchedule,
  listDeliveries,
  listSchedules,
  runScheduleNow,
  updateSchedule,
} from "../../api/client";
import type { DeliveryAttempt, Schedule } from "../../api/types";
import { DeliveryStatus } from "../delivery/DeliveryStatus";

type SchedulePanelProps = Readonly<{ auditDefinitionId?: string }>;

export function SchedulePanel({ auditDefinitionId }: SchedulePanelProps) {
  const [schedules, setSchedules] = useState<Schedule[]>([]);
  const [time, setTime] = useState("08:00");
  const [timezone, setTimezone] = useState("UTC");
  const [recipients, setRecipients] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [latestDelivery, setLatestDelivery] = useState<DeliveryAttempt | null>(
    null,
  );

  const refresh = async () => {
    try {
      const nextSchedules = await listSchedules();
      setSchedules(nextSchedules);
      if (nextSchedules[0]) {
        const attempts = await listDeliveries(nextSchedules[0].id);
        setLatestDelivery(attempts[0] ?? null);
      }
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Schedule load failed",
      );
    }
  };

  const create = async () => {
    if (!auditDefinitionId) return;
    try {
      await createSchedule({
        audit_definition_id: auditDefinitionId,
        enabled: true,
        frequency: "daily",
        local_time: time,
        timezone,
        recipients: recipients
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
      });
      await refresh();
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Schedule creation failed",
      );
    }
  };

  const runNow = async (scheduleId: string) => {
    try {
      setLatestDelivery(await runScheduleNow(scheduleId));
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Scheduled run failed",
      );
    }
  };

  return (
    <DDSCard className="schedule-panel">
      <div className="section-label-row">
        <DDSLabel>Recurring reports</DDSLabel>
        <DDSBadge color="informative" size="sm">
          SMTP
        </DDSBadge>
      </div>
      <DDSFormField>
        <DDSLabel htmlFor="schedule-time">Local time</DDSLabel>
        <DDSTextInput
          id="schedule-time"
          type="time"
          size="sm"
          value={time}
          onChange={(event) => setTime(event.target.value)}
        />
      </DDSFormField>
      <DDSFormField>
        <DDSLabel htmlFor="schedule-timezone">Timezone</DDSLabel>
        <DDSSelect
          id="schedule-timezone"
          size="sm"
          value={timezone}
          onChange={(event) => setTimezone(event.target.value)}
        >
          <option value="UTC">UTC</option>
          <option value="America/New_York">America/New_York</option>
          <option value="America/Los_Angeles">America/Los_Angeles</option>
          <option value="Europe/London">Europe/London</option>
        </DDSSelect>
        <DDSHelperText>Reports use this local timezone.</DDSHelperText>
      </DDSFormField>
      <DDSFormField>
        <DDSLabel htmlFor="schedule-recipients">Recipients</DDSLabel>
        <DDSTextInput
          id="schedule-recipients"
          size="sm"
          value={recipients}
          onChange={(event) => setRecipients(event.target.value)}
        />
      </DDSFormField>
      <div className="schedule-actions">
        <DDSButton
          size="sm"
          onClick={() => void create()}
          inactive={!auditDefinitionId}
        >
          Save daily schedule
        </DDSButton>
        <DDSButton size="sm" kind="minimal" onClick={() => void refresh()}>
          Refresh schedules
        </DDSButton>
      </div>
      {schedules.map((schedule) => (
        <div className="schedule-row" key={schedule.id}>
          <DDSBadge color={schedule.enabled ? "success" : "neutral"} size="sm">
            {schedule.enabled ? "Enabled" : "Paused"}
          </DDSBadge>
          <span>
            {schedule.local_time} · {schedule.timezone}
          </span>
          <DDSButton
            size="xs"
            kind="minimal"
            onClick={() =>
              void updateSchedule(schedule.id, {
                enabled: !schedule.enabled,
              }).then(refresh)
            }
          >
            {schedule.enabled ? "Pause" : "Resume"}
          </DDSButton>
          <DDSButton
            size="xs"
            kind="minimal"
            onClick={() => void runNow(schedule.id)}
          >
            Run now
          </DDSButton>
          <DDSButton
            size="xs"
            kind="minimal"
            color="destructive"
            onClick={() => void deleteSchedule(schedule.id).then(refresh)}
          >
            Delete
          </DDSButton>
        </div>
      ))}
      <DeliveryStatus attempt={latestDelivery} />
      {error ? <DDSHelperText>{error}</DDSHelperText> : null}
    </DDSCard>
  );
}
