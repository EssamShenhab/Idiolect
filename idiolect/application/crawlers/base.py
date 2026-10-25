from abc import ABC, abstractmethod
from contextlib import ExitStack

from scrapling.spiders import Response
from scrapling.fetchers import StealthySession

from idiolect.domain.db_schemes.documents import NoSQLBaseDocument

from patchright.sync_api import TimeoutError as PatchrightTimeout
from playwright.sync_api import TimeoutError as PlaywrightTimeout

_TIMEOUTS = (PatchrightTimeout, PlaywrightTimeout)


class BaseCrawler(ABC):
    model: type[NoSQLBaseDocument]

    @abstractmethod
    def extract(self, link: str, **kwargs) -> None: ...

    def close(self) -> None:
        """Release resources. No-op by default; browser crawlers override this."""


class BaseBrowserCrawler(BaseCrawler, ABC):
    """Scrapling-backed browser crawler. The browser starts on first fetch."""

    session_cls = StealthySession

    def __init__(
        self, scroll_limit: int = 5, profile_dir: str | None = None, **session_kwargs
    ) -> None:
        self.scroll_limit = scroll_limit
        self._opts = {"headless": True, **session_kwargs}
        if profile_dir:
            self._opts["user_data_dir"] = profile_dir
        self._stack = ExitStack()
        self._session = None

    @property
    def session(self):
        if self._session is None:
            self._session = self._stack.enter_context(self.session_cls(**self._opts))
        return self._session

    def close(self) -> None:
        self._stack.close()
        self._session = None

    def __enter__(self):
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def fetch_page(self, url: str, scroll: bool = False, **kwargs) -> Response:
        if scroll:
            user_action = kwargs.pop("page_action", None)

            def combined(page) -> None:
                if user_action is not None:
                    user_action(page)
                self._scroll_to_bottom(page)

            kwargs["page_action"] = combined
        return self.session.fetch(url, **kwargs)

    def _scroll_to_bottom(self, page) -> None:
        limit = self.scroll_limit if self.scroll_limit is not None else 1000
        last = page.evaluate("document.body.scrollHeight")
        for _ in range(limit):  # 0 means no scrolling
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            try:
                page.wait_for_function(
                    "h => document.body.scrollHeight > h", arg=last, timeout=5000
                )
            except _TIMEOUTS:
                break
            last = page.evaluate("document.body.scrollHeight")
