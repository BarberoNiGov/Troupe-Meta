"""Provider base class."""

from app.cinema import cinema_prompt
from app.modes import is_3d
from app.personas import COMMON_RULES, trait_block
from app.three import HYBRID_PROMPT, THREE_PROMPT


class ProviderError(RuntimeError):
    pass


class Provider:
    name = "base"
    model = ""

    async def generate(self, persona: dict, brief: str, mode: str = "2d") -> dict:
        """Return {"approach": str, "html": str, "usage": dict}."""
        raise NotImplementedError

    def system_prompt(self, persona: dict, mode: str = "2d") -> str:
        if isinstance(mode, bool):  # backward compatibility
            mode = "3d" if mode else "2d"
        three = is_3d(mode)
        prompt = (
            f"{COMMON_RULES}\n\nYOUR TEMPERAMENT:\n{persona['prompt']}\n\n"
            f"{trait_block(persona)}\n\n"
            f"{cinema_prompt(persona['id'], three)}"
        )
        if three:
            prompt += f"\n\n{THREE_PROMPT}"
        if mode == "hybrid":
            prompt += f"\n\n{HYBRID_PROMPT}"
        return prompt

    def info(self) -> dict:
        return {"name": self.name, "model": self.model}
