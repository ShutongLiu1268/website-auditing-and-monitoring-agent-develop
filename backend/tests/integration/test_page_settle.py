"""Real-browser check that settling a page captures late sections and lazy images."""

import pytest
from playwright.async_api import async_playwright

from app.acquisition.page_settle import settle_for_capture

LAZY_GIF = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7"
PIXEL_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)
PAGE = f"""
<html><body>
  <img id="lazy" src="{LAZY_GIF}" data-src="{PIXEL_PNG}">
  <div style="height: 3000px"></div>
  <script>
    window.addEventListener("scroll", () => {{
      if (!document.getElementById("late")) {{
        const section = document.createElement("p");
        section.id = "late";
        section.textContent = "Late section";
        document.body.appendChild(section);
      }}
    }});
  </script>
</body></html>
"""


@pytest.mark.asyncio
async def test_settle_loads_lazy_images_and_late_sections():
    """Test scrolling reveals late sections and lazy image sources replace placeholders."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": 1280, "height": 720})
            await page.set_content(PAGE)

            await settle_for_capture(page)

            assert await page.get_attribute("#lazy", "src") == PIXEL_PNG
            assert await page.locator("#late").count() == 1
            assert await page.evaluate("() => document.getElementById('lazy').naturalWidth") == 1
        finally:
            await browser.close()
