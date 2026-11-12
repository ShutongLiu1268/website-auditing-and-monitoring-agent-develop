"""Deterministic parser for supported audit chat commands."""

import re
from dataclasses import dataclass
from urllib.parse import urlparse

from pydantic import HttpUrl

from app.conversation.models import ChatCommand
from app.domain.models import AuditMode, PageTarget

_URL_RE = re.compile(r"https://[^\s,;]+", re.IGNORECASE)
_LOCALE_RE = re.compile(r"\b(?:[a-z]{2,3}-[A-Z]{2}|[a-z]{2}-[a-z]{2})\b")


class ChatCommandParser:
    """Parse URLs, modes, locales, filters, and schedule intent."""

    def parse(self, message: str) -> ChatCommand:
        """Parse one user message into a validated command."""
        text = message.strip()
        lowered = text.lower()
        urls = [self._clean_url(value) for value in _URL_RE.findall(text)]
        urls = [url for url in urls if url]
        mode = self._mode(lowered)
        locales = _LOCALE_RE.findall(text)

        if any(
            word in lowered
            for word in ("schedule", "every morning", "every day", "daily")
        ):
            return ChatCommand(
                action="schedule_create",
                mode=mode,
                targets=self._targets(urls, locales),
                clarification=self._schedule_clarification(mode, urls, locales),
            )
        if (
            any(word in lowered for word in ("show", "which", "filter", "compare"))
            and not urls
        ):
            action = (
                "comparison_query"
                if "compare" in lowered or "which" in lowered
                else "findings_query"
            )
            return ChatCommand(action=action, query=text)
        if urls or mode is not None:
            return ChatCommand(
                action="audit_create",
                mode=mode,
                targets=self._targets(urls, locales),
                clarification=self._audit_clarification(mode, urls, locales),
            )
        return ChatCommand(
            action="unknown",
            query=text,
            clarification="Provide PDP URLs and an audit mode.",
        )

    @staticmethod
    def _clean_url(value: str) -> str | None:
        """Validate URL shape before Pydantic/domain validation."""
        return clean_https_url(value)

    @staticmethod
    def _mode(text: str) -> AuditMode | None:
        """Extract audit mode."""
        if "sprint" in text or "launch" in text:
            return AuditMode.SPRINT_LAUNCH
        if "r2" in text:
            return AuditMode.R2
        if "r3" in text:
            return AuditMode.R3
        return None

    @staticmethod
    def _targets(urls: list[str], locales: list[str]) -> list[PageTarget]:
        """Pair URLs with locales, defaulting missing values to en-US."""
        return [
            PageTarget(
                url=HttpUrl(url),
                locale=locales[index] if index < len(locales) else "en-US",
                country=None,
            )
            for index, url in enumerate(urls)
        ]

    @staticmethod
    def _audit_clarification(
        mode: AuditMode | None,
        urls: list[str],
        locales: list[str],
    ) -> str | None:
        """Return missing audit configuration guidance."""
        if mode is None:
            return "Which framework should I use: Sprint/Launch, R2, or R3?"
        if not urls:
            return "Please provide at least one HTTPS PDP URL."
        if len(locales) < len(urls):
            return "Please provide the expected locale for each PDP URL."
        return None

    @staticmethod
    def _schedule_clarification(
        mode: AuditMode | None,
        urls: list[str],
        locales: list[str],
    ) -> str | None:
        """Return missing schedule configuration guidance."""
        return ChatCommandParser._audit_clarification(mode, urls, locales)


_LOCALE_SEGMENT_RE = re.compile(r"[a-z]{2,3}[-_][a-z]{2}", re.IGNORECASE)


@dataclass(frozen=True)
class PromptPageTargets:
    targets: list[PageTarget]
    problems: list[str]


def extract_prompt_targets(text: str) -> PromptPageTargets:
    """Read HTTPS PDP URLs and their locales from a free-form agent prompt."""
    matches = list(_URL_RE.finditer(text))
    locales_by_url: dict[str, set[str]] = {}
    for index, match in enumerate(matches):
        url = clean_https_url(match.group(0))
        if url is None:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        locale = _locale_from_path(url) or _locale_after(text[match.end() : end])
        found = locales_by_url.setdefault(url, set())
        if locale:
            found.add(locale)
    targets: list[PageTarget] = []
    problems: list[str] = []
    for url, locales in locales_by_url.items():
        if not locales:
            problems.append(
                f"No locale found for {url}. Add it to the URL path or after the URL, e.g. en-CA."
            )
        elif len(locales) > 1:
            problems.append(
                f"{url} is listed with conflicting locales: {', '.join(sorted(locales))}."
            )
        else:
            targets.append(
                PageTarget(url=HttpUrl(url), locale=next(iter(locales)), country=None)
            )
    return PromptPageTargets(targets=targets, problems=problems)


def _locale_from_path(url: str) -> str | None:
    for segment in urlparse(url).path.split("/"):
        if _LOCALE_SEGMENT_RE.fullmatch(segment):
            return _normalize_locale(segment)
    return None


def _locale_after(segment: str) -> str | None:
    match = _LOCALE_RE.search(segment.split("\n", 1)[0])
    return _normalize_locale(match.group(0)) if match else None


def _normalize_locale(value: str) -> str:
    language, country = re.split(r"[-_]", value)
    return f"{language.lower()}-{country.upper()}"


def clean_https_url(value: str) -> str | None:
    candidate = value.rstrip(".,)")
    parsed = urlparse(candidate)
    return candidate if parsed.scheme == "https" and parsed.netloc else None
