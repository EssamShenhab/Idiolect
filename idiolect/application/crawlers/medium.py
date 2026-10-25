from loguru import logger
from scrapling.spiders import Response

from idiolect.domain.db_schemes.documents import ArticleDocument

from .base import BaseBrowserCrawler

MIN_CONTENT_CHARS = 200  # arbitrary threshold, tune on real pages


def _text(page: Response, selector: str) -> str | None:
    node = page.css(selector).first
    if node is None:
        return None
    return " ".join(node.get_all_text(separator=" ", strip=True).split()) or None


def _meta(page: Response, prop: str) -> str | None:
    value = page.css(f'meta[property="{prop}"]::attr(content)').get()
    return str(value).strip() if value else None


def parse_medium_article(
    page: Response,
) -> dict[str, str | None]:
    """Parse Medium article metadata and its body."""
    has_article = bool(page.css("article"))

    return {
        "title": (
            _text(page, "h1.pw-post-title")
            or _text(page, "article h1")
            or _meta(page, "og:title")
        ),
        "subtitle": (
            _text(page, "h2.pw-subtitle-paragraph") or _meta(page, "og:description")
        ),
        "body": (str(page.markdown(css_selector="article")) if has_article else None),
    }


class MediumCrawler(BaseBrowserCrawler):
    model: type[ArticleDocument] = ArticleDocument

    def __init__(self, scroll: bool = False, **kwargs) -> None:
        super().__init__(**kwargs)
        self._scroll = scroll

    def extract(self, link: str, **kwargs) -> None:
        if self.model.find(link=link) is not None:
            logger.info(f"Article already exists in DB: {link}")
            return

        logger.info(f"Starting to scrape Medium article: {link}")

        page = self.fetch_page(link, scroll=self._scroll, wait_for_selector="article")
        if page.status != 200:
            raise RuntimeError(f"HTTP {page.status} for {link}")

        data = parse_medium_article(page)
        if len(data["body"] or "") < MIN_CONTENT_CHARS:
            raise RuntimeError(
                f"Almost no article content from {link}; it may be paywalled or blocked"
            )

        user = kwargs["user"]
        self.model(
            platform="medium",
            content=data,
            link=link,
            author_id=user.id,
            author_full_name=user.full_name,
        ).save()

        logger.info(f"Successfully scraped and saved article: {link}")
