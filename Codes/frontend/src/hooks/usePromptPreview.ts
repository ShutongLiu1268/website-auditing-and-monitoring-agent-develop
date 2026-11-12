import { useEffect, useState } from "react";
import { ApiRequestError, parsePrompt } from "../api/client";
import type { PromptTarget } from "../api/types";

type PromptPreview = {
  targets: PromptTarget[];
  problems: string[];
  pending: boolean;
};

type ParsedPrompt = {
  prompt: string;
  targets: PromptTarget[];
  problems: string[];
};

const EMPTY_PREVIEW: PromptPreview = {
  targets: [],
  problems: [],
  pending: false,
};

const PROMPT_ROUTE_MISSING =
  "The backend doesn't have the prompt route yet. Restart the backend to load the latest routes.";

function promptErrorMessage(error: unknown): string {
  if (error instanceof ApiRequestError && error.status === 404)
    return PROMPT_ROUTE_MISSING;
  return error instanceof Error ? error.message : "Could not read the prompt";
}

export function usePromptPreview(prompt: string): PromptPreview {
  const [parsed, setParsed] = useState<ParsedPrompt>({
    prompt: "",
    targets: [],
    problems: [],
  });

  useEffect(() => {
    if (!prompt.trim()) return;
    let cancelled = false;
    const timer = window.setTimeout(() => {
      parsePrompt(prompt)
        .then((result) => {
          if (!cancelled) setParsed({ prompt, ...result });
        })
        .catch((parseError: unknown) => {
          if (!cancelled)
            setParsed({
              prompt,
              targets: [],
              problems: [promptErrorMessage(parseError)],
            });
        });
    }, 350);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, [prompt]);

  if (!prompt.trim()) return EMPTY_PREVIEW;
  if (parsed.prompt !== prompt) return { ...EMPTY_PREVIEW, pending: true };
  return { targets: parsed.targets, problems: parsed.problems, pending: false };
}
