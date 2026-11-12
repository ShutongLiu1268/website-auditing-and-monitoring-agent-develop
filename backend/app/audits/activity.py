import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncIterator, Mapping
from datetime import UTC, datetime


class RunActivityLog:
    def __init__(self) -> None:
        self._events: defaultdict[str, list[dict[str, str | None]]] = defaultdict(list)
        self._closed: set[str] = set()
        self._changed = asyncio.Condition()

    def knows(self, run_id: str) -> bool:
        return run_id in self._events or run_id in self._closed

    async def record(self, run_id: str, stage: str, message: str, page: str | None = None) -> None:
        self._events[run_id].append(
            {
                "stage": stage,
                "message": message,
                "page": page,
                "at": datetime.now(UTC).isoformat(),
            }
        )
        await self._notify()

    async def close(self, run_id: str) -> None:
        self._closed.add(run_id)
        await self._notify()

    async def stream(self, run_id: str) -> AsyncIterator[str]:
        sent = 0
        while True:
            events = self._events.get(run_id, [])
            while sent < len(events):
                yield _sse("activity", events[sent])
                sent += 1
            if run_id in self._closed:
                yield _sse("done", {})
                return
            async with self._changed:
                await self._changed.wait_for(
                    lambda: sent < len(self._events.get(run_id, [])) or run_id in self._closed
                )

    async def _notify(self) -> None:
        async with self._changed:
            self._changed.notify_all()


def _sse(event: str, payload: Mapping[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(payload)}\n\n"
