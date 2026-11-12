import { useState } from "react";
import {
  DDSButton,
  DDSCard,
  DDSFormField,
  DDSHelperText,
  DDSLabel,
  DDSMessageBar,
  DDSTextArea,
} from "@dds/react";
import { sendChat } from "../../api/client";
import type { ChatResponse } from "../../api/types";

type ChatPanelProps = Readonly<{
  onAuditAccepted?: (response: ChatResponse) => void;
}>;

export function ChatPanel({ onAuditAccepted }: ChatPanelProps) {
  const [message, setMessage] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const submit = async () => {
    if (!message.trim() || sending) return;
    setSending(true);
    setError(null);
    try {
      const nextResponse = await sendChat(message);
      setResponse(nextResponse);
      if (nextResponse.type === "accepted") onAuditAccepted?.(nextResponse);
      setMessage("");
    } catch (requestError) {
      setError(
        requestError instanceof Error
          ? requestError.message
          : "Chat request failed",
      );
    } finally {
      setSending(false);
    }
  };

  return (
    <DDSCard className="chat-panel">
      <DDSFormField>
        <DDSLabel htmlFor="audit-chat">Audit assistant</DDSLabel>
        <DDSTextArea
          id="audit-chat"
          size="sm"
          value={message}
          onChange={(event) => setMessage(event.target.value)}
          placeholder="Review these PDPs against R3 for en-US and fr-CA..."
          aria-describedby="audit-chat-helper"
        />
        <DDSHelperText id="audit-chat-helper">
          Include HTTPS URLs, locales, framework, or result questions.
        </DDSHelperText>
      </DDSFormField>
      <DDSButton
        size="sm"
        kind="filled"
        onClick={() => void submit()}
        inactive={sending}
      >
        {sending ? "Sending…" : "Send to assistant"}
      </DDSButton>
      {error ? (
        <DDSMessageBar color="error" dismissible={false}>
          {error}
        </DDSMessageBar>
      ) : null}
      {response ? (
        <DDSMessageBar
          color={response.type === "accepted" ? "success" : "informative"}
          dismissible={false}
        >
          {response.message}
        </DDSMessageBar>
      ) : null}
    </DDSCard>
  );
}
