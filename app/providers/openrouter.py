"""OpenRouter provider: Muse Spark 1.3 Contributor."""

from app import config
from app.providers.chat import ChatProvider


class OpenRouterProvider(ChatProvider):
    name = "openrouter"
    model = config.OPENROUTER_MODEL
    api_key = config.OPENROUTER_API_KEY
    base_url = config.OPENROUTER_BASE_URL
    input_price_per_m = config.OPENROUTER_INPUT_PRICE_PER_M
    output_price_per_m = config.OPENROUTER_OUTPUT_PRICE_PER_M
    extra_headers = {
        "HTTP-Referer": "https://github.com/troupe-studio",
        "X-Title": "Troupe",
    }
