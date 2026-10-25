from loguru import logger
from pydantic import ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from zenml.client import Client
from zenml.exceptions import EntityExistsError


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    APP_NAME: str
    APP_VERSION: str
    DATABASE_HOST: str
    DATABASE_NAME: str

    @classmethod
    def load_settings(cls) -> "Settings":
        """
        Load settings from ZenML secrets.
        Fall back to the .env file if the secret is missing or invalid.
        """
        try:
            logger.info("Loading settings from the ZenML secret store.")

            settings_secrets = Client().get_secret("settings")
            return cls.model_validate(settings_secrets.secret_values)

        except (RuntimeError, KeyError, ValidationError):
            logger.warning(
                "Failed to load settings from the ZenML secret store. "
                "Loading settings from the .env file."
            )

            # BaseSettings loads values from .env at runtime.
            # Pylance cannot infer that these required fields come from .env.
            return cls()  # pyright: ignore[reportCallIssue]

    def export(self) -> None:
        """Export the settings to the ZenML secret store."""

        env_vars = {key: str(value) for key, value in self.model_dump().items()}

        client = Client()

        try:
            client.create_secret(name="settings", values=env_vars)
        except EntityExistsError:
            logger.warning(
                "Secret 'settings' already exists. Delete it with "
                "'zenml secret delete settings' before recreating it."
            )


settings = Settings.load_settings()
