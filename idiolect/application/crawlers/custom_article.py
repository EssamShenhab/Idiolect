from urllib.parse import urlparse

from loguru import logger
from scrapling.fetchers import Fetcher

from idiolect.domain.db_schemes.documents import ArticleDocument

from .base import BaseCrawler

MIN_CONTENT_CHARS = 200  # arbitrary threshold, tune on real pages


class CustomArticleCrawler(BaseCrawler):
    model: type[ArticleDocument] = ArticleDocument

    def extract(self, link: str, **kwargs) -> None:
        if self.model.find(link=link) is not None:
            logger.info(f"Article already exists in DB: {link}")
            return
        logger.info(f"Fetching article: {link}")

        page = Fetcher.get(link, timeout=30)
        if page.status != 200:
            raise RuntimeError(f"HTTP {page.status} for {link}")

        body = (
            page.markdown(css_selector="article")
            if page.css("article")
            else page.markdown(main_content_only=True)
        )
        content = {
            "title": page.css("title::text").get(),
            "subtitle": page.css('meta[name="description"]::attr(content)').get(),
            "body": str(body),
        }
        if len(content["body"]) < MIN_CONTENT_CHARS:
            raise RuntimeError(
                f"Almost no content extracted from {link}; "
                "it may need the browser tier"
            )

        user = kwargs["user"]
        self.model(
            content=content,
            link=link,
            platform=urlparse(link).netloc,
            author_id=user.id,
            author_full_name=user.full_name,
        ).save()

        logger.info(f"Article saved to DB: {link}")
