import type { ChecklistGroup, ChecklistStatus } from "../api/types";

export const statusMeta: Record<
  ChecklistStatus,
  { label: string; color: "error" | "warning" | "informative" | "success" }
> = {
  issues: { label: "Issues", color: "error" },
  error: { label: "Error", color: "warning" },
  not_evaluated: { label: "Not evaluated", color: "warning" },
  pass: { label: "Pass", color: "success" },
  pending: { label: "Pending", color: "informative" },
  not_applicable: { label: "Not applicable", color: "informative" },
};

export function visibleGroups(
  groups: ChecklistGroup[],
  showNotApplicable: boolean,
): ChecklistGroup[] {
  return groups
    .map((group) => ({
      ...group,
      checkpoints: showNotApplicable
        ? group.checkpoints
        : group.checkpoints.filter(
            (checkpoint) => checkpoint.status !== "not_applicable",
          ),
    }))
    .filter((group) => group.checkpoints.length > 0);
}
