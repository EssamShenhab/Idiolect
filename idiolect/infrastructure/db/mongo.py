from loguru import logger
from pymongo import MongoClient
from pymongo.errors import PyMongoError

from idiolect.settings import settings


class MongoDatabaseConnector:
    _instance: MongoClient | None = None

    def __new__(cls, *args, **kwargs) -> MongoClient:
        if cls._instance is None:
            client = MongoClient(settings.DATABASE_HOST)

            try:
                client.admin.command("ping")
            except PyMongoError as e:
                client.close()
                logger.error(f"Failed to connect to MongoDB: {e!s}")
                raise

            cls._instance = client
            logger.info(f"Successfully connected to MongoDB: {settings.DATABASE_HOST}")

        return cls._instance


connection = MongoDatabaseConnector()
