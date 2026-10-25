from urllib.parse import urlparse

from loguru import logger
from tqdm import tqdm
from typing_extensions import Annotated
from zenml import step, get_step_context

from idiolect.application.crawlers.dispatcher import CrawlerDispatcher
from idiolect.domain.db_schemes.documents import UserDocument


@step
def crawl_links(
    user: UserDocument,
    links: list[str],
) -> Annotated[list[str], "crawled_links"]:
    dispatcher = CrawlerDispatcher.build()

    try:
        logger.info(f"Starting to crawl {len(links)} link(s).")

        metadata = {}
        successful_crawls = 0

        for link in tqdm(links):
            successful_crawl, domain = _crawl_link(dispatcher, link, user)
            successful_crawls += successful_crawl
            metadata = _add_to_metadata(metadata, domain, successful_crawl)

        step_context = get_step_context()
        step_context.add_output_metadata(
            output_name="crawled_links",
            metadata=metadata,
        )

        logger.info(f"Successfully crawled {successful_crawls} / {len(links)} links.")

        return links
    finally:
        dispatcher.close()


def _crawl_link(
    dispatcher: CrawlerDispatcher, link: str, user: UserDocument
) -> tuple[bool, str]:
    crawler = dispatcher.get_crawler(link)
    crawler_domain = urlparse(link).netloc

    try:
        crawler.extract(link=link, user=user)
        return True, crawler_domain
    except Exception as e:
        logger.warning(f"Failed to crawl {link}: {e!s}")
        return False, crawler_domain


def _add_to_metadata(metadata: dict, domain: str, successfull_crawl: bool) -> dict:
    if domain not in metadata:
        metadata[domain] = {}
    metadata[domain]["successful"] = metadata[domain].get("successful", 0) + int(
        successfull_crawl
    )
    metadata[domain]["total"] = metadata[domain].get("total", 0) + 1
    metadata[domain]["failed"] = metadata[domain].get("failed", 0) + int(
        not successfull_crawl
    )

    return metadata
