from urllib.parse import urlparse

from loguru import logger

from .base import BaseCrawler
from .custom_article import CustomArticleCrawler
from .github import GithubCrawler
from .medium import MediumCrawler
from .youtube import YoutubeCrawler


class CrawlerDispatcher:
    def __init__(self) -> None:
        self._crawlers: dict[str, tuple[type[BaseCrawler], bool]] = {}
        self._instances: dict[type[BaseCrawler], BaseCrawler] = {}

    @staticmethod
    def _hostname(url: str) -> str:
        """Extract and normalize a hostname from a URL or domain."""
        value = url.strip()

        if not value:
            return ""

        if "://" not in value:
            value = f"https://{value}"

        parsed = urlparse(value)
        return (parsed.hostname or "").lower().removeprefix("www.")

    def _instance(self, cls: type[BaseCrawler]) -> BaseCrawler:
        """Return a cached crawler instance, creating it when needed."""
        if cls not in self._instances:
            self._instances[cls] = cls()

        return self._instances[cls]

    def get_crawler(self, url: str) -> BaseCrawler:
        """Find the crawler registered for a URL."""
        host = self._hostname(url)

        for domain, (crawler_cls, include_subdomains) in self._crawlers.items():
            if host == domain or (include_subdomains and host.endswith(f".{domain}")):
                return self._instance(crawler_cls)

        logger.warning(
            f"No crawler found for {url!r}. " "Defaulting to CustomArticleCrawler."
        )
        return self._instance(CustomArticleCrawler)

    def register(
        self,
        domain: str,
        crawler: type[BaseCrawler],
        *,
        subdomains: bool = False,
    ) -> None:
        """Register a crawler for a domain."""
        host = self._hostname(domain)

        if not host:
            raise ValueError(
                f"Invalid domain: {domain!r}. "
                "Pass a domain or full URL, such as 'https://medium.com'."
            )

        self._crawlers[host] = (crawler, subdomains)

    def close(self) -> None:
        """Close all cached crawler instances."""
        for crawler in self._instances.values():
            try:
                crawler.close()
            except Exception as exc:
                logger.warning(f"Failed to close {type(crawler).__name__}: {exc!s}")

        self._instances.clear()

    @classmethod
    def build(cls) -> "CrawlerDispatcher":
        """Create a dispatcher with the default crawler registrations."""
        dispatcher = cls()

        dispatcher.register(
            "https://medium.com",
            MediumCrawler,
            subdomains=True,
        )
        dispatcher.register("https://github.com", GithubCrawler)
        dispatcher.register("https://youtube.com", YoutubeCrawler)
        dispatcher.register("https://m.youtube.com", YoutubeCrawler)
        dispatcher.register("https://youtu.be", YoutubeCrawler)

        return dispatcher
