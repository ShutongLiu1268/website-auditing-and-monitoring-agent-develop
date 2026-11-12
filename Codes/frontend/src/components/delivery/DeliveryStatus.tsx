import { DDSBadge, DDSMessageBar } from "@dds/react";
import type { DeliveryAttempt } from "../../api/types";

type DeliveryStatusProps = Readonly<{ attempt?: DeliveryAttempt | null }>;

export function DeliveryStatus({ attempt }: DeliveryStatusProps) {
  if (!attempt) {
    return <DDSMessageBar color="informative" dismissible={false}>No delivery attempt recorded yet.</DDSMessageBar>;
  }
  const color = attempt.status === "sent" ? "success" : attempt.status === "failed" ? "error" : "informative";
  return (
    <DDSMessageBar color={color} dismissible={false}>
      <DDSBadge color={color} size="sm">{attempt.status}</DDSBadge>{" "}
      {attempt.status === "failed" ? attempt.error_code ?? "Delivery failed" : "Report delivery status updated."}
    </DDSMessageBar>
  );
}
