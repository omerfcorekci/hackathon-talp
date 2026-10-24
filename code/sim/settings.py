"""Run settings and stable, order-independent exposure draws."""

import hashlib
import math
from dataclasses import asdict, dataclass


def draw(seed: int, *parts: object) -> float:
    """A reproducible U[0,1) draw, independent of async completion order."""
    import json

    payload = json.dumps([seed, *parts], ensure_ascii=False, separators=(",", ":"))
    return int.from_bytes(hashlib.sha256(payload.encode()).digest()[:8], "big") / 2**64


@dataclass(frozen=True)
class Settings:
    seed: int = 42
    weeks: int = 10
    concurrency: int = 24
    temperature: float = 0.8
    model: str = "gemini-3.5-flash-lite"
    fallback_model: str = "gemini-3.1-flash-lite"
    attempts: int = 3
    timeout_seconds: float = 60.0
    max_peer_messages: int = 2
    stranger_probability: float = 0.05
    following_probability: float = 0.35
    close_friend_probability: float = 0.65
    whatsapp_probability: float = 0.80

    def __post_init__(self):
        for name, low, high in (("weeks", 1, 10), ("concurrency", 1, 256),
                                ("attempts", 1, 10), ("max_peer_messages", 0, 20)):
            value = getattr(self, name)
            if type(value) is not int or not low <= value <= high:
                raise ValueError(f"{name} must be an integer between {low} and {high}")
        if type(self.seed) is not int or not 0 <= self.seed < 2**31:
            raise ValueError("seed must be an integer in [0, 2**31)")
        if not math.isfinite(self.temperature) or not 0 < self.temperature <= 2:
            raise ValueError("temperature must be positive and at most 2")
        if not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("model must be a nonempty string")
        if not isinstance(self.fallback_model, str):
            raise ValueError("fallback_model must be a string (empty disables fallback)")
        for name in ("stranger_probability", "following_probability",
                     "close_friend_probability", "whatsapp_probability"):
            value = getattr(self, name)
            if isinstance(value, bool) or not math.isfinite(value) or not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")

    def to_dict(self):
        return asdict(self)
