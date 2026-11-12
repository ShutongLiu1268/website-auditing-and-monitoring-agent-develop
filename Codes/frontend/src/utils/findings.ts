import type { Finding, IssueStatus, Severity } from "../types/audit";

const severityRank: Record<Severity, number> = {
  low: 0,
  medium: 1,
  high: 2,
  critical: 3,
};

const statusRank: Record<IssueStatus, number> = {
  resolved: 0,
  not_rechecked: 0,
  unresolved: 1,
  new: 2,
};

function strongest<T extends string>(values: T[], rank: Record<T, number>): T {
  return values.reduce((best, value) =>
    rank[value] > rank[best] ? value : best,
  );
}

export function sortBySeverity(issues: Finding[]): Finding[] {
  return [...issues].sort(
    (left, right) => severityRank[right.severity] - severityRank[left.severity],
  );
}

export function groupIssues(issues: Finding[]): Finding[] {
  const groups = new Map<string, { first: Finding; rows: Finding[] }>();
  for (const issue of issues) {
    const key = issue.issueKey ?? issue.id;
    const group = groups.get(key);
    if (group) group.rows.push(issue);
    else groups.set(key, { first: issue, rows: [issue] });
  }
  return [...groups.values()].map(({ first, rows }) => {
    const members: Finding[] = [];
    for (const row of rows) {
      if (!members.some((member) => member.page === row.page))
        members.push(row);
    }
    const pages = members.map((member) => member.page);
    return {
      ...first,
      page: pages.join(" · "),
      pages,
      members,
      severity: strongest(
        rows.map((row) => row.severity),
        severityRank,
      ),
      status: strongest(
        rows.map((row) => row.status),
        statusRank,
      ),
    };
  });
}
