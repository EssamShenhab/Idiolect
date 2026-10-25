import os
import subprocess
import tempfile
from pathlib import Path

from loguru import logger

from idiolect.domain.db_schemes.documents import RepositoryDocument

from .base import BaseCrawler

DEFAULT_IGNORE_DIRS = frozenset(
    {".git", "node_modules", ".venv", "venv", "__pycache__"}
)
DEFAULT_IGNORE_SUFFIXES = frozenset(
    {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".ico",
        ".pdf",
        ".zip",
        ".gz",
        ".lock",
        ".pyc",
        ".svg",
        ".ipynb",
    }
)


class GithubCrawler(BaseCrawler):
    model: type[RepositoryDocument] = RepositoryDocument

    def __init__(
        self,
        ignore_dirs: frozenset[str] = DEFAULT_IGNORE_DIRS,
        ignore_suffixes: frozenset[str] = DEFAULT_IGNORE_SUFFIXES,
        max_file_bytes: int = 1_000_000,
    ) -> None:
        self._ignore_dirs = ignore_dirs
        self._ignore_suffixes = ignore_suffixes
        self._max_file_bytes = max_file_bytes

    def extract(self, link: str, **kwargs) -> None:
        if self.model.find(link=link) is not None:
            logger.info(f"Repository already exists in the database: {link}")
            return

        logger.info(f"Starting to scrape GitHub repository: {link}")

        repo_name = link.rstrip("/").split("/")[-1].removesuffix(".git")

        with tempfile.TemporaryDirectory() as tmp:
            repo_path = Path(tmp) / repo_name
            subprocess.run(
                ["git", "clone", "--depth", "1", link, str(repo_path)],
                check=True,
                capture_output=True,
                text=True,
                timeout=300,
                env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},
            )
            files = self._read_tree(repo_path)

        user = kwargs["user"]

        self.model(
            content={"files": files},
            name=repo_name,
            link=link,
            platform="github",
            author_id=user.id,
            author_full_name=user.full_name,
        ).save()

        logger.info(
            f"Finished scraping GitHub repository: " f"{link} ({len(files)} files)"
        )

    def _read_tree(self, repo_path: Path) -> list[dict[str, str]]:
        files: list[dict[str, str]] = []

        for path in repo_path.rglob("*"):
            if not path.is_file():
                continue

            relative_path = path.relative_to(repo_path)

            if any(part in self._ignore_dirs for part in relative_path.parts):
                continue

            if path.suffix.lower() in self._ignore_suffixes:
                continue

            try:
                if path.stat().st_size > self._max_file_bytes:
                    continue

                data = path.read_bytes()

                if b"\0" in data[:8192]:
                    continue

                text = data.decode("utf-8")
            except (OSError, UnicodeDecodeError) as exc:
                logger.debug(f"Skipping {relative_path}: {exc}")
                continue

            files.append(
                {
                    "path": relative_path.as_posix(),
                    "text": text,
                }
            )

        return files
