from pathlib import Path
from typing import Self

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        arbitrary_types_allowed=True,
        env_ignore_empty=True,
        env_nested_delimiter="__",
        extra="ignore",
    )

    base_dir: Path = Path(__file__).parent.parent
    """Base directory of the project."""

    assets_dir: Path = base_dir / "assets"
    """Directory holding assets."""

    dump_dir: Path = base_dir / "dump"
    """Directory holding dump files."""

    selenium_hub_url: str = "http://localhost:4444"
    """URL of Selenium Hub for remote webdriver."""

    @model_validator(mode="after")
    def _create_directories(self) -> Self:
        self.dump_dir.mkdir(parents=True, exist_ok=True)
        return self


settings = Settings()
