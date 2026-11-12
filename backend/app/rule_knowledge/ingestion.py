"""Parse the bundled guide into checkpoints from declared headers."""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

from app.domain.models import RulePassage
from app.rule_knowledge.checkpoint_header import (
    CheckpointHeaderError,
    build_header,
    parse_market_groups,
)
from app.rule_knowledge.markets import MarketGroups

_GROUPS_RE = re.compile(r"<!--\s*market-groups\n(.*?)\n-->", re.DOTALL)
_CHECKPOINT_RE = re.compile(r"<!--\s*checkpoint\n(.*?)\n-->", re.DOTALL)


@dataclass(frozen=True)
class RuleCatalog:
    version: str
    groups: MarketGroups
    passages: list[RulePassage]


class RuleIngestor:
    """Parse the bundled guide into checkpoint passages."""

    def __init__(self, source_path: Path):
        self.source_path = source_path
        self.content = source_path.read_text(encoding="utf-8")
        self.version = hashlib.sha256(self.content.encode("utf-8")).hexdigest()

    def ingest(self) -> RuleCatalog:
        groups_match = _GROUPS_RE.search(self.content)
        if groups_match is None:
            raise CheckpointHeaderError("guide has no market-groups block")
        groups = MarketGroups(parse_market_groups(groups_match.group(1)))
        passages: list[RulePassage] = []
        seen: set[str] = set()
        for section, title, start, end, body in _checkpoint_blocks(self.content):
            text = "\n".join(body)
            match = _CHECKPOINT_RE.search(text)
            if match is None:
                raise CheckpointHeaderError(
                    f"checkpoint heading has no header: {title}"
                )
            header = build_header(match.group(1), groups.names)
            if header.id in seen:
                raise CheckpointHeaderError(f"duplicate checkpoint id: {header.id}")
            seen.add(header.id)
            passages.append(
                RulePassage(
                    id=header.id,
                    version=self.version,
                    heading_path=[section, title],
                    source_range=(start, end),
                    original_text=_CHECKPOINT_RE.sub("", text).strip(),
                    modes=list(header.profiles),
                    markets=list(header.markets),
                    zones=list(header.zones),
                    topics=list(header.topics),
                    evaluator_type=header.evaluator,
                    check=header.check,
                    review=header.review,
                    reminder=header.reminder,
                )
            )
        return RuleCatalog(version=self.version, groups=groups, passages=passages)


def _checkpoint_blocks(content: str) -> list[tuple[str, str, int, int, list[str]]]:
    """Split the guide at ## sections and ### checkpoint headings."""
    blocks: list[tuple[str, str, int, int, list[str]]] = []
    section = "Introduction"
    current: tuple[str, int, list[str]] | None = None
    lines = content.splitlines()
    for number, line in enumerate(lines, start=1):
        if line.startswith("## ") or line.startswith("### "):
            if current is not None:
                blocks.append((section, current[0], current[1], number - 1, current[2]))
                current = None
            if line.startswith("## "):
                section = line[3:].strip()
            else:
                current = (line[4:].strip(), number, [])
        elif current is not None:
            current[2].append(line)
    if current is not None:
        blocks.append((section, current[0], current[1], len(lines), current[2]))
    return blocks
