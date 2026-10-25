import re
from urllib.parse import parse_qs, urlparse

from loguru import logger
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)

from idiolect.domain.db_schemes.documents import TranscriptDocument

from .base import BaseCrawler

_VIDEO_ID = re.compile(r"[A-Za-z0-9_-]{11}")
_HOSTS = {"youtube.com", "m.youtube.com", "music.youtube.com"}
_ID_PREFIXES = {"shorts", "embed", "live", "v"}


def extract_video_id(url_or_id: str) -> str | None:
    """Return the 11-character video id from a YouTube URL or a bare id, else None."""
    value = url_or_id.strip()
    if _VIDEO_ID.fullmatch(value):
        return value

    parsed = urlparse(value)
    host = re.sub(r"^www\.", "", (parsed.hostname or "").lower())
    parts = [p for p in parsed.path.split("/") if p]

    candidate = None
    if host == "youtu.be" and parts:
        candidate = parts[0]
    elif host in _HOSTS:
        if parts == ["watch"]:
            candidate = parse_qs(parsed.query).get("v", [""])[0]
        elif len(parts) >= 2 and parts[0] in _ID_PREFIXES:
            candidate = parts[1]

    return candidate if candidate and _VIDEO_ID.fullmatch(candidate) else None


class YoutubeCrawler(BaseCrawler):
    model: type[TranscriptDocument] = TranscriptDocument

    def __init__(self, languages: tuple[str, ...] = ("ar", "en")) -> None:
        self._languages = languages
        self._api = YouTubeTranscriptApi()

    def extract(self, link: str, **kwargs) -> None:
        video_id = extract_video_id(link)
        if video_id is None:
            raise ValueError(f"Could not parse a YouTube video id from: {link}")

        # Normalise every URL form to one canonical link, so dedupe on `link` works.
        canonical_link = f"https://youtube.com/watch?v={video_id}"

        if self.model.find(link=canonical_link) is not None:
            logger.info(f"Transcript already exists in the database: {canonical_link}")
            return

        logger.info(f"Starting to fetch transcript: {video_id}")

        try:
            transcript = self._api.fetch(video_id, languages=self._languages)
        except (TranscriptsDisabled, NoTranscriptFound):
            logger.warning(
                f"No transcript in {self._languages} for {video_id}, skipping"
            )
            return

        transcript_text = " ".join(segment.text for segment in transcript)

        user = kwargs["user"]

        self.model(
            content={
                "video_id": video_id,
                "text": transcript_text,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
            },
            link=canonical_link,
            platform="youtube",
            author_id=user.id,
            author_full_name=user.full_name,
        ).save()

        logger.info(f"Finished fetching transcript: {video_id}")
