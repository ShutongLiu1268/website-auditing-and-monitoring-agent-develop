"""Verify evidence emitted by deterministic and DSX evaluators."""

import re
import unicodedata
from dataclasses import dataclass

from app.acquisition.zone_extractor import Zone
from app.domain.models import CheckOutcome, CheckResult, RulePassage
from app.facts.models import PageFacts


@dataclass(frozen=True)
class VerificationResult:
    """Verification decision for one check result."""

    accepted: bool
    result: CheckResult
    reason: str | None = None


_QUOTE_MAP = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u2010": "-",
        "\u2011": "-",
        "\u2012": "-",
        "\u2013": "-",
        "\u2014": "-",
    }
)


_EVIDENCE_SPLIT = re.compile(r"\n|\.\.\.|\u2026")


def _normalize(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).translate(_QUOTE_MAP).split())


def _contains(haystack: str, needle: str) -> bool:
    normalized = _normalize(needle)
    return bool(normalized) and normalized in _normalize(haystack)


class EvidenceVerifier:
    """Reject issue results without exact source evidence."""

    def verify(
        self,
        result: CheckResult,
        rule: RulePassage,
        zone: Zone,
        facts: PageFacts,
    ) -> VerificationResult:
        """Validate rule quote, evidence quote, and locator."""
        if result.outcome != CheckOutcome.ISSUE:
            return VerificationResult(accepted=True, result=result)

        if not result.rule_quote or not _contains(
            rule.original_text, result.rule_quote
        ):
            return self._reject(result, "rule_quote_not_found")
        if not result.evidence_quote or not self._evidence_exists(
            result.evidence_quote, zone, facts
        ):
            return self._reject(result, "evidence_quote_not_found")
        if result.dom_locator and not self._locator_exists(
            result.dom_locator, zone, facts
        ):
            return self._reject(result, "dom_locator_not_found")
        return VerificationResult(accepted=True, result=result)

    def _evidence_exists(self, evidence: str, zone: Zone, facts: PageFacts) -> bool:
        """Check zone text and normalized fact values."""
        values = [
            zone.text,
            *(link.href for link in facts.links),
            *(image.src for image in facts.images),
            *(dimension.text for dimension in facts.dimensions),
            *(media.src for media in facts.media),
        ]
        segments = [
            segment
            for segment in _EVIDENCE_SPLIT.split(evidence)
            if _normalize(segment)
        ]
        return bool(segments) and all(
            any(_contains(value, segment) for value in values) for segment in segments
        )

    def _locator_exists(self, locator: str, zone: Zone, facts: PageFacts) -> bool:
        """Check extracted zone and fact locators."""
        if locator == zone.dom_locator:
            return True
        fact_locators = [link.locator for link in facts.links]
        fact_locators.extend(image.locator for image in facts.images)
        fact_locators.extend(dimension.locator for dimension in facts.dimensions)
        fact_locators.extend(media.locator for media in facts.media)
        return locator in fact_locators

    def _reject(self, result: CheckResult, reason: str) -> VerificationResult:
        """Convert an unverifiable issue into an error result."""
        return VerificationResult(
            accepted=False,
            reason=reason,
            result=result.model_copy(
                update={
                    "outcome": CheckOutcome.ERROR,
                    "confidence": 0.0,
                    "error": f"evidence_verification_failed:{reason}",
                }
            ),
        )
