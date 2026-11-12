"""Black-box fixture demo flow against a running API."""

import asyncio
import os

import httpx
import pytest


@pytest.mark.asyncio
async def test_fixture_demo_flow():
    """Verify health, multi-target audit, run polling, issues, and report."""
    base_url = os.getenv("SMOKE_API_BASE_URL", "http://localhost:8000")
    async with httpx.AsyncClient(base_url=base_url, timeout=10.0) as client:
        try:
            health = await client.get("/health")
        except httpx.HTTPError:
            pytest.skip("Start the API before running black-box E2E tests")
        if health.status_code != 200:
            pytest.fail(f"Health endpoint returned {health.status_code}")

        targets = [
            {"url": "https://www.dell.com/en-ca/shop/laptops", "locale": "en-CA"},
            {"url": "https://www.dell.com/en-us/shop/laptops", "locale": "en-US"},
            {"url": "https://www.dell.com/fr-ca/shop/laptops", "locale": "fr-CA"},
        ]
        audit = await client.post(
            "/api/audits", json={"mode": "r3", "targets": targets}
        )
        assert audit.status_code == 200
        run = await client.post(f"/api/audits/{audit.json()['id']}/runs")
        assert run.status_code == 200
        run_id = run.json()["run_id"]

        for _ in range(120):
            await asyncio.sleep(0.25)
            status = await client.get(f"/api/runs/{run_id}/status")
            assert status.status_code == 200
            payload = status.json()
            if payload["status"] in {"completed", "partial", "failed"}:
                break
        else:
            pytest.fail("Demo run did not reach a terminal state")

        issues = await client.get(f"/api/runs/{run_id}/issues")
        report = await client.get(f"/api/runs/{run_id}/report")
        assert issues.status_code == 200
        assert report.status_code == 200

        schedule = await client.post(
            "/api/schedules",
            json={
                "audit_definition_id": audit.json()["id"],
                "frequency": "daily",
                "local_time": "08:00",
                "timezone": "UTC",
                "recipients": ["demo@example.com"],
            },
        )
        assert schedule.status_code == 200
        run_now = await client.post(
            f"/api/schedules/{schedule.json()['id']}/run-now", timeout=120.0
        )
        assert run_now.status_code == 200
        assert run_now.json()["status"] in {"sent", "failed"}
