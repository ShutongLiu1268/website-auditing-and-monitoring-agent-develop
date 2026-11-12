from collections.abc import Callable

import pytest
from playwright.async_api import Error as PlaywrightError
from pytest_mock import MockerFixture

from app.facts.link_probe import LinkProber
from app.facts.models import LinkFact, PageFacts

OK = "https://www.dell.com/ok"
MISSING = "https://www.dell.com/missing"


def _link(
    href: str,
    position: int,
    status: int | None = None,
    reachable: bool | None = None,
    in_zone: bool = True,
) -> LinkFact:
    return LinkFact(
        href=href,
        locator=f"a:nth-of-type({position})",
        status_code=status,
        reachable=reachable,
        in_zone=in_zone,
    )


def _prober(
    max_urls: int = 10,
    cache_seconds: float = 0,
    clock: Callable[[], float] = lambda: 0.0,
) -> LinkProber:
    return LinkProber(
        max_urls=max_urls,
        concurrency=2,
        timeout_ms=1000,
        cache_seconds=cache_seconds,
        clock=clock,
    )


def _request(
    mocker: MockerFixture,
    head: dict[str, int | Exception],
    get: dict[str, int | Exception] | None = None,
):
    def responder(outcomes: dict[str, int | Exception]):
        def send(url: str, **_):
            outcome = outcomes[url]
            if isinstance(outcome, Exception):
                raise outcome
            return mocker.Mock(status=outcome, dispose=mocker.AsyncMock())

        return send

    return mocker.Mock(
        head=mocker.AsyncMock(side_effect=responder(head)),
        get=mocker.AsyncMock(side_effect=responder(get or {})),
    )


class TestLinkProber:
    @pytest.mark.asyncio
    async def test_probes_public_links_and_marks_status(self, mocker: MockerFixture):
        # Arrange
        request = _request(mocker, head={OK: 200, MISSING: 404}, get={MISSING: 404})
        facts = PageFacts(links=[_link(OK, 1), _link(MISSING, 2)])

        # Act
        probed, warnings = await _prober().probe(request, facts)

        # Assert
        statuses = {
            link.href: (link.status_code, link.reachable) for link in probed.links
        }
        assert statuses == {OK: (200, True), MISSING: (404, False)}
        assert warnings == []

    @pytest.mark.asyncio
    async def test_method_not_allowed_on_head_retries_with_get(
        self, mocker: MockerFixture
    ):
        # Arrange
        request = _request(mocker, head={OK: 405}, get={OK: 200})
        facts = PageFacts(links=[_link(OK, 1)])

        # Act
        probed, _ = await _prober().probe(request, facts)

        # Assert
        assert (probed.links[0].status_code, probed.links[0].reachable) == (200, True)

    @pytest.mark.asyncio
    async def test_forbidden_status_is_unverifiable_not_broken(
        self, mocker: MockerFixture
    ):
        # Arrange
        request = _request(mocker, head={OK: 403}, get={OK: 403})
        facts = PageFacts(links=[_link(OK, 1)])

        # Act
        probed, _ = await _prober().probe(request, facts)

        # Assert
        assert (probed.links[0].status_code, probed.links[0].reachable) == (403, None)

    @pytest.mark.asyncio
    async def test_bot_denied_status_is_unverifiable(self, mocker: MockerFixture):
        # Arrange
        request = _request(mocker, head={OK: 999}, get={OK: 999})
        facts = PageFacts(links=[_link(OK, 1)])

        # Act
        probed, _ = await _prober().probe(request, facts)

        # Assert
        assert (probed.links[0].status_code, probed.links[0].reachable) == (999, None)

    @pytest.mark.asyncio
    async def test_network_error_keeps_existing_status(self, mocker: MockerFixture):
        # Arrange
        request = _request(
            mocker, head={OK: PlaywrightError("net::ERR_NAME_NOT_RESOLVED")}
        )
        facts = PageFacts(links=[_link(OK, 1, status=None, reachable=True)])

        # Act
        probed, _ = await _prober().probe(request, facts)

        # Assert
        assert probed.links[0].reachable is True

    @pytest.mark.asyncio
    async def test_links_outside_zones_are_not_probed(self, mocker: MockerFixture):
        # Arrange
        request = _request(mocker, head={})
        facts = PageFacts(links=[_link(OK, 1, in_zone=False)])

        # Act
        probed, warnings = await _prober().probe(request, facts)

        # Assert
        request.head.assert_not_awaited()
        assert probed.links[0].reachable is None
        assert warnings == []

    @pytest.mark.asyncio
    async def test_private_and_non_http_links_are_not_probed(
        self, mocker: MockerFixture
    ):
        # Arrange
        request = _request(mocker, head={})
        facts = PageFacts(
            links=[
                _link("http://10.0.0.5/admin", 1),
                _link("javascript:void(0)", 2),
                _link("mailto:sales@dell.com", 3),
            ]
        )

        # Act
        probed, warnings = await _prober().probe(request, facts)

        # Assert
        request.head.assert_not_awaited()
        assert probed.links == facts.links
        assert warnings == []

    @pytest.mark.asyncio
    async def test_probe_limit_adds_warning(self, mocker: MockerFixture):
        # Arrange
        request = _request(mocker, head={OK: 200, MISSING: 200})
        facts = PageFacts(links=[_link(OK, 1), _link(MISSING, 2)])

        # Act
        _, warnings = await _prober(max_urls=1).probe(request, facts)

        # Assert
        assert request.head.await_count == 1
        assert warnings == ["link_probe_capped:1/2"]

    @pytest.mark.asyncio
    async def test_duplicate_links_are_probed_once(self, mocker: MockerFixture):
        # Arrange
        request = _request(mocker, head={OK: 200})
        facts = PageFacts(links=[_link(OK, 1), _link(OK, 2)])

        # Act
        await _prober().probe(request, facts)

        # Assert
        assert request.head.await_count == 1

    @pytest.mark.asyncio
    async def test_cached_status_is_reused_within_window(self, mocker: MockerFixture):
        # Arrange
        request = _request(mocker, head={OK: 200})
        facts = PageFacts(links=[_link(OK, 1)])
        prober = _prober(cache_seconds=60, clock=lambda: 0.0)

        # Act
        await prober.probe(request, facts)
        probed, _ = await prober.probe(request, facts)

        # Assert
        assert request.head.await_count == 1
        assert probed.links[0].reachable is True

    @pytest.mark.asyncio
    async def test_cached_status_expires_after_window(self, mocker: MockerFixture):
        # Arrange
        request = _request(mocker, head={OK: 200})
        facts = PageFacts(links=[_link(OK, 1)])
        ticks = iter([0.0, 61.0])
        prober = _prober(cache_seconds=60, clock=lambda: next(ticks))

        # Act
        await prober.probe(request, facts)
        await prober.probe(request, facts)

        # Assert
        assert request.head.await_count == 2

    @pytest.mark.asyncio
    async def test_cached_links_do_not_count_toward_probe_limit(
        self, mocker: MockerFixture
    ):
        # Arrange
        request = _request(mocker, head={OK: 200, MISSING: 200})
        prober = _prober(max_urls=1, cache_seconds=60, clock=lambda: 0.0)
        await prober.probe(request, PageFacts(links=[_link(OK, 1)]))

        # Act
        _, warnings = await prober.probe(
            request, PageFacts(links=[_link(OK, 1), _link(MISSING, 2)])
        )

        # Assert
        assert request.head.await_count == 2
        assert warnings == []
