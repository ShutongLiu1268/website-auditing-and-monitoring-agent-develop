"""Settle a rendered page so late sections and lazy images are in the capture."""

from contextlib import suppress

from playwright.async_api import Page, ViewportSize
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from app.config import settings

CAPTURE_VIEWPORT: ViewportSize = {"width": 1280, "height": 1400}

_SCROLL_THROUGH_PAGE = """
async () => {
  const nextFrame = () =>
    new Promise((resolve) => {
      requestAnimationFrame(() => setTimeout(resolve, 100));
      setTimeout(resolve, 400);
    });
  const step = Math.max(400, Math.floor(window.innerHeight * 0.8));
  let y = 0;
  for (let i = 0; i < 60 && y < document.documentElement.scrollHeight; i++) {
    window.scrollTo({ top: y, behavior: 'instant' });
    window.dispatchEvent(new Event('scroll'));
    await nextFrame();
    y += step;
  }
  window.scrollTo({ top: 0, behavior: 'instant' });
  window.dispatchEvent(new Event('scroll'));
  await nextFrame();
}
"""

_PROMOTE_LAZY_SOURCES = r"""
() => {
  const LAZY_NAMES = ['data-src', 'data-lazy-src', 'data-original', 'data-lazy'];
  const URL_LIKE = /^(https?:\/\/|\/\/|\/|data:image\/)/;
  const IMAGE_LIKE = /\.(png|jpe?g|webp|gif|svg|avif)([?#]|$)|\/is\/image\/|^data:image\//i;
  for (const img of document.querySelectorAll('img')) {
    const current = img.getAttribute('src') || '';
    if (current && !current.startsWith('data:')) continue;
    const data = [...img.attributes]
      .filter((attr) => attr.name.startsWith('data-'))
      .map((attr) => ({ name: attr.name, value: attr.value.trim() }));
    const lazy =
      data.find((attr) => LAZY_NAMES.includes(attr.name) && URL_LIKE.test(attr.value)) ||
      data.find((attr) => IMAGE_LIKE.test(attr.value));
    if (lazy) img.setAttribute('src', lazy.value);
  }
  for (const el of document.querySelectorAll('img[data-srcset], source[data-srcset]')) {
    if (!el.hasAttribute('srcset')) el.setAttribute('srcset', el.getAttribute('data-srcset'));
  }
}
"""

_WAIT_FOR_IMAGES = """
async () => {
  const pending = Array.from(document.images).filter((img) => !img.complete);
  await Promise.all(
    pending.map(
      (img) =>
        new Promise((resolve) => {
          img.addEventListener('load', resolve, { once: true });
          img.addEventListener('error', resolve, { once: true });
          setTimeout(resolve, 5000);
        })
    )
  );
}
"""


async def settle_for_capture(page: Page) -> None:
    """Scroll through the page, promote lazy image sources, and wait for them to load."""
    await page.evaluate(_SCROLL_THROUGH_PAGE)
    await page.evaluate(_PROMOTE_LAZY_SOURCES)
    with suppress(PlaywrightTimeoutError):
        await page.wait_for_load_state(
            "networkidle", timeout=settings.PLAYWRIGHT_IDLE_MS
        )
    await page.evaluate(_WAIT_FOR_IMAGES)
