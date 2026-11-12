import asyncio
import json

import pytest

from app.audits.activity import RunActivityLog


async def _collect(stream):
    return [chunk async for chunk in stream]


@pytest.mark.asyncio
async def test_stream_replays_recorded_events_in_order_then_done():
    activity = RunActivityLog()
    await activity.record("run-1", "render", "Rendering en-CA page", page="en-CA")
    await activity.record("run-1", "evaluate", "Found 2 issues", page="en-CA")
    await activity.close("run-1")

    chunks = await _collect(activity.stream("run-1"))

    assert [chunk.splitlines()[0] for chunk in chunks] == [
        "event: activity",
        "event: activity",
        "event: done",
    ]
    first_payload = json.loads(chunks[0].splitlines()[1].removeprefix("data: "))
    assert first_payload["message"] == "Rendering en-CA page"
    assert first_payload["page"] == "en-CA"
    assert chunks[-1] == "event: done\ndata: {}\n\n"


@pytest.mark.asyncio
async def test_stream_of_closed_run_without_events_only_sends_done():
    activity = RunActivityLog()
    await activity.close("run-2")

    assert await _collect(activity.stream("run-2")) == ["event: done\ndata: {}\n\n"]


@pytest.mark.asyncio
async def test_stream_waits_for_events_recorded_after_subscribing():
    activity = RunActivityLog()

    async def record_later():
        await asyncio.sleep(0)
        await activity.record("run-3", "run", "Auditing 1 PDP URL")
        await activity.close("run-3")

    recorder = asyncio.create_task(record_later())
    chunks = await _collect(activity.stream("run-3"))
    await recorder

    assert chunks[0].startswith("event: activity")
    assert chunks[-1] == "event: done\ndata: {}\n\n"
