# ADR-0002: Hackathon Runtime Architecture

## Status

Accepted

## Context

Production architecture includes Redis workers, SSE, scheduling, email delivery, and retention jobs. For a hackathon, this infrastructure adds significant complexity without proportional demo value. The core value proposition is agentic checkpoint application and evidence-backed findings.

## Decision

The hackathon runtime uses in-process `asyncio.Queue` workers instead of Redis. Progress is delivered through 3-second frontend polling instead of SSE. Scheduling, recurring runs, and email delivery are deferred to post-hackathon. MongoDB persists audit history, and Docker Compose runs API, web, and MongoDB. No Redis or Mailpit service is required.

## Consequences

- Simpler local development and demo setup.
- Reduced infrastructure surface area.
- In-process job loss on restart is an accepted limitation; persisted statuses allow detection of interrupted runs.
- No recurring automation; runs are manual or Run Now only.
- Email reports are not generated; browser report is always available.
- Production roadmap will add Redis, SSE, scheduling, SMTP, and retention.

## Alternatives Considered

- Redis worker queue: rejected for added complexity and hackathon time constraints.
- SSE: rejected for client complexity; polling is sufficient for demo.
- Scheduling and email: rejected to focus on core audit/comparison features.
