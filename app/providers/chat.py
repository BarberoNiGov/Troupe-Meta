"""Shared Chat Completions provider."""

import json

import httpx

from app import config
from app.personas import temperature_for
from app.providers.base import Provider, ProviderError
from app.usage import normalize_usage


def check_truncation(payload: dict, name: str, max_tokens: int) -> None:
    """Fail loudly on a truncated response instead of a confusing JSON error."""
    try:
        reason = payload["choices"][0].get("finish_reason")
    except (KeyError, IndexError, TypeError) as exc:
        raise ProviderError(f"{name}: unexpected response shape") from exc
    if reason == "length":
        raise ProviderError(f"{name}: output truncated at {max_tokens} tokens")


def parse_json_object(content: str) -> dict:
    text = (content or "").strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ProviderError("model did not return a JSON object")
    try:
        # strict=False tolerates literal newlines/tabs inside HTML strings,
        # which some models emit instead of escaping them.
        data = json.loads(text[start:end + 1], strict=False)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"invalid JSON from model: {exc}") from exc
    if not isinstance(data, dict):
        raise ProviderError("model JSON is not an object")
    return data


class ChatProvider(Provider):
    api_key = ""
    base_url = ""
    model = ""
    extra_headers: dict = {}
    max_tokens_param = "max_tokens"
    input_price_per_m = 0.0
    output_price_per_m = 0.0

    async def _post(self, body: dict) -> dict:
        """POST a chat completion, retrying once without response_format."""
        if not self.api_key:
            raise ProviderError(f"{self.name}: API key is not set")
        headers = {"Authorization": f"Bearer {self.api_key}", **self.extra_headers}
        body = dict(body)
        async with httpx.AsyncClient(timeout=config.LLM_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions", headers=headers, json=body
            )
            # Some providers (including some Meta/OpenRouter routes) reject
            # response_format. Retry once without it; the parser handles fenced JSON.
            if response.status_code == 400 and "response_format" in body:
                body.pop("response_format", None)
                response = await client.post(
                    f"{self.base_url}/chat/completions", headers=headers, json=body
                )
        if response.status_code >= 400:
            raise ProviderError(f"{self.name} API {response.status_code}: {response.text[:300]}")
        try:
            return response.json()
        except ValueError as exc:
            raise ProviderError(f"{self.name}: response is not JSON") from exc

    async def generate(self, persona: dict, brief: str, mode: str = "2d") -> dict:
        if isinstance(mode, bool):  # backward compatibility
            mode = "3d" if mode else "2d"
        mode_line = {
            "2d": "MEDIUM: 2D. Use CSS, SVG, or 2D canvas only. No Three.js import.",
            "3d": "MEDIUM: 3D. Build with Three.js r160; the wordmark is 3D geometry.",
            "hybrid": "MEDIUM: HYBRID. Three.js world for depth, HTML/CSS wordmark and overlay.",
        }.get(mode, "MEDIUM: 2D.")
        body = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt(persona, mode)},
                {"role": "user", "content": f"THE BRIEF:\n{brief}\n\n{mode_line}\n\nReturn the JSON object now."},
            ],
            "temperature": temperature_for(persona),
            self.max_tokens_param: config.LLM_MAX_TOKENS,
            "response_format": {"type": "json_object"},
        }
        payload = await self._post(body)
        check_truncation(payload, self.name, config.LLM_MAX_TOKENS)
        try:
            content = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"{self.name}: unexpected response shape") from exc
        data = parse_json_object(content)
        data["usage"] = normalize_usage(
            payload.get("usage"),
            self.input_price_per_m,
            self.output_price_per_m,
        )
        return data
