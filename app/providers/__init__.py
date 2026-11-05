"""Provider registry."""

from app import config
from app.providers.base import Provider, ProviderError
from app.providers.meta import MetaProvider
from app.providers.openrouter import OpenRouterProvider


def get_provider(name: str | None = None) -> Provider:
    name = (name or config.LLM_PROVIDER).strip().lower()
    if name == "openrouter":
        return OpenRouterProvider()
    if name == "meta":
        return MetaProvider()
    raise ProviderError(f"unknown provider: {name}")
