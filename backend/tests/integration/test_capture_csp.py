"""Captured-page responses must let the browser load https video and embedded frames."""

from types import SimpleNamespace

import pytest
from playwright.async_api import async_playwright

from app import main

PREVIOUS_POLICY = (
    "default-src 'none'; img-src https: data:; style-src 'unsafe-inline' https:; "
    "font-src https: data:; base-uri https:; form-action 'none'"
)
EMBEDS = (
    '<iframe src="https://example.invalid/frame"></iframe>'
    '<video src="https://example.invalid/clip.mp4"></video>'
)


class _Snapshots:
    async def get(self, snapshot_id: str) -> SimpleNamespace:
        return SimpleNamespace(
            id=snapshot_id,
            run_id="run-1",
            url="https://www.dell.com/en-us/shop/laptops",
            html_capture_id="capture-1",
        )


class _Captures:
    async def get(self, capture_id: str) -> bytes:
        return b"<html><head></head><body><p>Captured</p></body></html>"


@pytest.fixture
def capture_repos(mocker):
    mocker.patch.object(main.app.state, "snapshot_repo", _Snapshots(), create=True)
    mocker.patch.object(main.app.state, "capture_repo", _Captures(), create=True)


async def _refusals(policy: str) -> list[str]:
    messages: list[str] = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            page.on("console", lambda message: messages.append(message.text))
            await page.set_content(
                f'<meta http-equiv="Content-Security-Policy" content="{policy}">{EMBEDS}'
            )
            await page.wait_for_timeout(1000)
        finally:
            await browser.close()
    return [
        message
        for message in messages
        if "violates the following Content Security Policy" in message
    ]


@pytest.mark.asyncio
async def test_capture_csp_allows_https_media_and_frames(capture_repos):
    """Test the captured-page policy names https media and frame sources."""
    response = await main.get_snapshot_html("run-1", "snapshot-1")

    policy = response.headers["Content-Security-Policy"]
    assert "media-src https:" in policy
    assert "frame-src https:" in policy


@pytest.mark.asyncio
async def test_browser_loads_https_embeds_under_capture_policy(capture_repos):
    """Test a real browser refuses https embeds under the old policy and accepts them now."""
    response = await main.get_snapshot_html("run-1", "snapshot-1")
    policy = response.headers["Content-Security-Policy"]

    previous = await _refusals(PREVIOUS_POLICY)
    assert any(message.startswith("Framing") for message in previous)
    assert any("Loading media" in message for message in previous)
    assert await _refusals(policy) == []
