import { DDSMessageBar } from "@dds/react";
import type { RunStatusResponse } from "../../api/types";

type CoverageBannerProps = Readonly<{ status: RunStatusResponse | null }>;

const modeLabels: Record<string, string> = {
  sprint_launch: "Sprint/Launch",
  r2: "R2",
  r3: "R3",
};

function describeWarning(warning: string) {
  const [code, detail = ""] = warning.split(":");
  if (code === "fixture_checkpoints_unavailable") {
    return `No demo checkpoints for ${modeLabels[detail] ?? detail}, so findings were not evaluated.`;
  }
  if (code === "fixture_page_inaccessible") {
    return `${detail.toUpperCase()} page could not be reached, so its earlier findings were not rechecked.`;
  }
  const text = code.replace(/_/g, " ");
  return `${text.charAt(0).toUpperCase()}${text.slice(1)}${detail ? `: ${detail}` : ""}.`;
}

export function CoverageBanner({ status }: CoverageBannerProps) {
  if (!status || status.status === "completed") return null;
  if (status.status !== "failed" && status.warnings.length === 0) return null;
  const message =
    status.status === "failed"
      ? "Audit failed."
      : status.warnings.map(describeWarning).join(" ");
  return (
    <DDSMessageBar
      color={status.status === "failed" ? "error" : "warning"}
      dismissible={false}
    >
      {message}
    </DDSMessageBar>
  );
}
