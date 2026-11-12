import { DDSFormField, DDSLabel, DDSSelect } from "@dds/react";
import type { IssueStatus, Severity } from "../../types/audit";

type ComparisonFiltersProps = Readonly<{
  status: IssueStatus | "all";
  severity: Severity | "all";
  onStatusChange: (status: IssueStatus | "all") => void;
  onSeverityChange: (severity: Severity | "all") => void;
}>;

export function ComparisonFilters({
  status,
  severity,
  onStatusChange,
  onSeverityChange,
}: ComparisonFiltersProps) {
  return (
    <div className="comparison-filters">
      <DDSFormField>
        <DDSLabel htmlFor="comparison-status">Status</DDSLabel>
        <DDSSelect
          id="comparison-status"
          size="sm"
          value={status}
          onChange={(event) =>
            onStatusChange(event.target.value as IssueStatus | "all")
          }
        >
          <option value="all">All statuses</option>
          <option value="new">New</option>
          <option value="unresolved">Unresolved</option>
          <option value="resolved">Not reported</option>
          <option value="not_rechecked">Not rechecked</option>
        </DDSSelect>
      </DDSFormField>
      <DDSFormField>
        <DDSLabel htmlFor="comparison-severity">Severity</DDSLabel>
        <DDSSelect
          id="comparison-severity"
          size="sm"
          value={severity}
          onChange={(event) =>
            onSeverityChange(event.target.value as Severity | "all")
          }
        >
          <option value="all">All severities</option>
          <option value="critical">Critical</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </DDSSelect>
      </DDSFormField>
    </div>
  );
}
