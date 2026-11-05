"""Meta Model API provider: Muse Spark via Chat Completions."""

from app import config
from app.providers.chat import ChatProvider


class MetaProvider(ChatProvider):
    name = "meta"
    model = config.META_MODEL
    api_key = config.META_API_KEY
    base_url = config.META_BASE_URL
    max_tokens_param = "max_completion_tokens"
    input_price_per_m = config.META_INPUT_PRICE_PER_M
    output_price_per_m = config.META_OUTPUT_PRICE_PER_M
