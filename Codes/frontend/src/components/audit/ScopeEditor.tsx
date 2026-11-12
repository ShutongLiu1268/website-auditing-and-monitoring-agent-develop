import {
  DDSFormField,
  DDSHelperText,
  DDSLabel,
  DDSTextInput,
} from "@dds/react";
import type { CrawlScope } from "../../api/types";

type ScopeEditorProps = Readonly<{
  scope: CrawlScope;
  onChange: (scope: CrawlScope) => void;
}>;

export function ScopeEditor({ scope, onChange }: ScopeEditorProps) {
  const updatePaths = (
    key: "include_paths" | "exclude_paths",
    value: string,
  ) => {
    onChange({
      ...scope,
      [key]: value
        .split(",")
        .map((path) => path.trim())
        .filter(Boolean),
    });
  };

  return (
    <section className="scope-editor" aria-label="Crawl scope">
      <DDSFormField>
        <DDSLabel htmlFor="include-paths">Include paths</DDSLabel>
        <DDSTextInput
          id="include-paths"
          size="sm"
          value={scope.include_paths.join(", ")}
          onChange={(event) => updatePaths("include_paths", event.target.value)}
        />
        <DDSHelperText>Comma-separated path prefixes.</DDSHelperText>
      </DDSFormField>
      <DDSFormField>
        <DDSLabel htmlFor="exclude-paths">Exclude paths</DDSLabel>
        <DDSTextInput
          id="exclude-paths"
          size="sm"
          value={scope.exclude_paths.join(", ")}
          onChange={(event) => updatePaths("exclude_paths", event.target.value)}
        />
      </DDSFormField>
      <DDSFormField>
        <DDSLabel htmlFor="page-limit">Page limit</DDSLabel>
        <DDSTextInput
          id="page-limit"
          size="sm"
          type="number"
          value={scope.page_limit}
          onChange={(event) =>
            onChange({ ...scope, page_limit: Number(event.target.value) })
          }
        />
      </DDSFormField>
    </section>
  );
}
