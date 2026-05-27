"""Vision backend configuration — local OCR engines and cloud multimodal LLMs.

Users bring their own API key for cloud backends:

    export VISION_BACKEND=openai_compatible
    export VISION_API_KEY=sk-or-...          # OpenRouter / OpenAI
    export VISION_BASE_URL=https://openrouter.ai/api/v1
    export VISION_MODEL=openai/gpt-4o

    # Or for Anthropic:
    export VISION_BACKEND=anthropic
    export VISION_API_KEY=sk-ant-...
    export VISION_MODEL=claude-3-5-sonnet-20241022

Default is 'local' — works out of the box with no API key.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class VisionBackend(Enum):
    LOCAL = "local"
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"


_DEFAULT_MODELS: dict[VisionBackend, str] = {
    VisionBackend.LOCAL: "",
    VisionBackend.OPENAI_COMPATIBLE: "openai/gpt-4o",
    VisionBackend.ANTHROPIC: "claude-3-5-sonnet-20241022",
}


@dataclass
class VisionConfig:
    backend: VisionBackend = VisionBackend.LOCAL
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = ""
    max_tokens: int = 4096
    temperature: float = 0.0

    def __post_init__(self) -> None:
        if not self.model:
            self.model = _DEFAULT_MODELS.get(self.backend, "gpt-4o")

    @classmethod
    def from_env(cls, overrides: dict[str, str] | None = None) -> VisionConfig:
        """Load vision config from environment variables.

        Priority: explicit overrides > env vars > defaults.

        Env vars:
            VISION_BACKEND: 'local' | 'openai_compatible' | 'anthropic'
            VISION_API_KEY: API key for the selected backend
            VISION_BASE_URL: Base URL for API endpoint
            VISION_MODEL: Model identifier string
            VISION_MAX_TOKENS: Max tokens in response
            VISION_TEMPERATURE: LLM temperature (0.0 = deterministic)

        Legacy fallback: OPENAI_API_KEY used if VISION_API_KEY is unset
            and backend is openai_compatible.
        """
        env = dict(os.environ)
        if overrides:
            env.update(overrides)

        backend_str = env.get("VISION_BACKEND", "local")
        try:
            backend = VisionBackend(backend_str)
        except ValueError:
            logger.warning("Unknown VISION_BACKEND=%s, falling back to local", backend_str)
            backend = VisionBackend.LOCAL

        api_key = env.get("VISION_API_KEY", "")
        if not api_key and backend == VisionBackend.OPENAI_COMPATIBLE:
            api_key = env.get("OPENAI_API_KEY", "")

        return cls(
            backend=backend,
            api_key=api_key,
            base_url=env.get("VISION_BASE_URL", "https://api.openai.com/v1"),
            model=env.get("VISION_MODEL", _DEFAULT_MODELS.get(backend, "gpt-4o")),
            max_tokens=int(env.get("VISION_MAX_TOKENS", "4096")),
            temperature=float(env.get("VISION_TEMPERATURE", "0.0")),
        )

    def validate(self) -> list[str]:
        """Check that config is usable. Returns list of issues (empty = OK)."""
        issues: list[str] = []
        if self.backend != VisionBackend.LOCAL and not self.api_key:
            issues.append(f"VISION_API_KEY required for {self.backend.value} backend")
        return issues
