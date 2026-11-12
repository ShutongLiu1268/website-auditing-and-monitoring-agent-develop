"""Run code checkpoints and screen hybrid checkpoints against zone text and page facts."""

import uuid

from app.acquisition.zone_extractor import Zone
from app.checks.models import CheckInput, Finding
from app.checks.registry import CODE_CHECKS, GATE_CHECKS
from app.domain.models import (
    AuditRun,
    CheckOutcome,
    CheckResult,
    PageSnapshot,
    RulePassage,
    Severity,
)
from app.facts.models import PageFacts


class DeterministicFactRunner:
    """Evaluate code checkpoints and screen hybrid checkpoints without an LLM call."""

    def evaluate(
        self,
        rule: RulePassage,
        run: AuditRun,
        snapshot: PageSnapshot,
        zone: Zone,
        facts: PageFacts,
    ) -> list[CheckResult]:
        """Return the verdict results of one code checkpoint."""
        check = CODE_CHECKS.get(rule.check or "")
        if check is None:
            return [
                self._result(
                    rule,
                    run,
                    snapshot,
                    zone,
                    CheckOutcome.ERROR,
                    problem="No code check is registered for this checkpoint.",
                    error="unsupported_deterministic_rule",
                )
            ]
        findings = check(CheckInput(zone=zone, facts=facts, locale=snapshot.locale))
        if findings is None:
            return [
                self._result(rule, run, snapshot, zone, CheckOutcome.NOT_APPLICABLE)
            ]
        if not findings:
            return [self._result(rule, run, snapshot, zone, CheckOutcome.PASS)]
        return [self._issue(rule, run, snapshot, zone, finding) for finding in findings]

    def screen(
        self,
        rule: RulePassage,
        locale: str,
        zone: Zone,
        facts: PageFacts,
    ) -> list[str] | None:
        """Return gate candidates, or None when the checkpoint has no registered gate."""
        gate = GATE_CHECKS.get(rule.check or "")
        if gate is None:
            return None
        return gate(CheckInput(zone=zone, facts=facts, locale=locale))

    def skipped(
        self,
        rule: RulePassage,
        run: AuditRun,
        snapshot: PageSnapshot,
        zone: Zone,
    ) -> CheckResult:
        """Return the not-applicable result for a gate that found no candidates."""
        return self._result(
            rule,
            run,
            snapshot,
            zone,
            CheckOutcome.NOT_APPLICABLE,
            reasoning="Nothing to evaluate: the zone is empty or the code screen found no candidates.",
        )

    def _issue(
        self,
        rule: RulePassage,
        run: AuditRun,
        snapshot: PageSnapshot,
        zone: Zone,
        finding: Finding,
    ) -> CheckResult:
        return self._result(
            rule,
            run,
            snapshot,
            zone,
            CheckOutcome.ISSUE,
            problem=finding.problem,
            evidence_quote=finding.evidence,
            dom_locator=finding.locator,
            suggested_correction=finding.suggestion,
        )

    def _result(
        self,
        rule: RulePassage,
        run: AuditRun,
        snapshot: PageSnapshot,
        zone: Zone,
        outcome: CheckOutcome,
        *,
        problem: str | None = None,
        evidence_quote: str | None = None,
        dom_locator: str | None = None,
        suggested_correction: str | None = None,
        error: str | None = None,
        reasoning: str | None = None,
    ) -> CheckResult:
        deterministic = outcome in {CheckOutcome.PASS, CheckOutcome.ISSUE}
        return CheckResult(
            id=str(uuid.uuid4()),
            run_id=run.id,
            page_snapshot_id=snapshot.id,
            rule_passage_id=rule.id,
            zone=zone.name,
            outcome=outcome,
            problem=problem,
            proof_text=suggested_correction or evidence_quote,
            suggested_correction=suggested_correction,
            severity=rule.severity or Severity.MEDIUM,
            rule_quote=rule.original_text,
            evidence_quote=evidence_quote,
            dom_locator=dom_locator or zone.dom_locator,
            confidence=1.0 if deterministic else 0.0,
            review_required=False,
            reasoning=reasoning or f"Deterministic check {rule.check}.",
            error=error,
        )
