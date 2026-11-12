"""Typed deterministic facts collected from a rendered PDP."""

from collections.abc import Iterable

from pydantic import BaseModel, Field

_TOPIC_FIELDS = {
    "link": ("links",),
    "image": ("images",),
    "accessibility": ("images",),
    "dimensions": ("dimensions",),
    "units": ("dimensions",),
    "weight": ("dimensions",),
    "media": ("media",),
}


class LinkFact(BaseModel):
    """A page link and observed response information."""

    href: str
    locator: str
    status_code: int | None = None
    reachable: bool | None = None
    in_zone: bool = False


class ImageFact(BaseModel):
    """An image source, load state, and alternative text."""

    src: str
    locator: str
    loaded: bool
    alt: str | None = None


class DimensionFact(BaseModel):
    """A parsed dimension or weight value."""

    text: str
    value: float | None
    unit: str | None
    locator: str


class MediaFact(BaseModel):
    """A video source and whether it failed to load."""

    src: str
    locator: str
    broken: bool = False


class PageFacts(BaseModel):
    """All deterministic facts collected for one rendered page."""

    links: list[LinkFact] = Field(default_factory=list)
    images: list[ImageFact] = Field(default_factory=list)
    dimensions: list[DimensionFact] = Field(default_factory=list)
    media: list[MediaFact] = Field(default_factory=list)
    network_warnings: list[str] = Field(default_factory=list)

    def scoped(self, topics: Iterable[str]) -> dict[str, object]:
        """Return only the fact categories that a checkpoint's topics declare."""
        fields = {
            field for topic in topics for field in _TOPIC_FIELDS.get(topic.lower(), ())
        }
        return self.model_dump(include=fields) if fields else {}
