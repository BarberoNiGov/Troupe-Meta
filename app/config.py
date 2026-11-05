"""Paths and environment. .env is authoritative for this project."""

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = ROOT / ".env"
DATA_DIR = ROOT / "data"
RUNS_DIR = DATA_DIR / "runs"
STATIC_DIR = Path(__file__).resolve().parent / "static"


def load_env(path: Path = ENV_PATH) -> None:
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ[key.strip()] = value.strip().strip('"').strip("'")


load_env()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter").strip().lower()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta/muse-spark-1.3-contributor").strip()

META_API_KEY = os.getenv("META_API_KEY", "").strip()
META_BASE_URL = os.getenv("META_BASE_URL", "https://api.meta.ai/v1").rstrip("/")
META_MODEL = os.getenv("META_MODEL", "muse-spark-1.3").strip()

MAX_HTML_BYTES = int(os.getenv("MAX_HTML_BYTES", "200000"))
MAX_CAST = int(os.getenv("MAX_CAST", "8"))
MAX_CONCURRENCY = int(os.getenv("MAX_CONCURRENCY", "6"))

# Muse Spark is slow; keep this above the slowest observed call.
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "600"))

# Per-response ceiling. Observed outputs are 5-8k tokens; 48k covers a file up
# to the 200 KB validator cap with margin, without allowing a runaway.
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "48000"))


def _price(name: str, default: float = 0.0) -> float:
    try:
        return float(os.getenv(name, str(default)) or default)
    except ValueError:
        return default


# Prices are USD per 1M tokens. Used only when the provider does not report cost.
OPENROUTER_INPUT_PRICE_PER_M = _price("OPENROUTER_INPUT_PRICE_PER_M", 0.10)
OPENROUTER_OUTPUT_PRICE_PER_M = _price("OPENROUTER_OUTPUT_PRICE_PER_M", 0.20)
META_INPUT_PRICE_PER_M = _price("META_INPUT_PRICE_PER_M")
META_OUTPUT_PRICE_PER_M = _price("META_OUTPUT_PRICE_PER_M")

DEFAULT_BRIEF = os.getenv(
    "DEFAULT_BRIEF",
    "Create an 8-second animated logo reveal for Kape, a Filipino coffee brand. "
    "Warm palette, kinetic type, 1080x1080, seamless loop.",
)


def provider_label() -> str:
    if LLM_PROVIDER == "openrouter":
        return f"muse-spark / {OPENROUTER_MODEL}"
    if LLM_PROVIDER == "meta":
        return f"muse-spark / {META_MODEL}"
    return LLM_PROVIDER


def ensure_dirs() -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
