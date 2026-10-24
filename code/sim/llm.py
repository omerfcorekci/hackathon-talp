"""Async Vertex transport and logged, validated attempts; no behavior defaults."""

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Protocol

from .schema import TURN_SCHEMA


class Transport(Protocol):
    async def generate(self, *, prompt, model, seed, temperature, schema) -> str: ...


class VertexTransport:
    def __init__(self, *, timeout_seconds):
        import os
        from google import genai
        from google.genai import types

        key = os.environ.get("TALP_KEY")
        if not key:
            raise ValueError("Export TALP_KEY before running the Vertex engine")
        # SDK retries are disabled so every actual request has its own audit row.
        self.client = genai.Client(
            vertexai=True, api_key=key,
            http_options=types.HttpOptions(timeout=int(timeout_seconds * 1000),
                                           retry_options=types.HttpRetryOptions(attempts=1)),
        )
        self.types = types

    async def generate(self, *, prompt, model, seed, temperature, schema):
        config = {"temperature": temperature, "seed": seed,
                  "response_mime_type": "application/json", "response_json_schema": schema,
                  "automatic_function_calling": {"disable": True}}
        if "automatic_continuation" in self.types.GenerateContentConfig.model_fields:
            config["automatic_continuation"] = False
        response = await self.client.aio.models.generate_content(model=model, contents=prompt, config=config)
        return response.text or ""

    async def close(self):
        await self.client.aio.aclose()
        self.client.close()


class FakeTransport:
    """Offline stand-in for VertexTransport: no key, no network, no cost.

    Answers are generated from the response schema, seeded by sha256(seed, model, prompt), so they
    are deterministic per (seed, prompt) and differ between seeds. Text fields are short neutral
    placeholders that never quote the prompt; outgoing messages stay empty so contact and channel
    validation cannot fail. Only for testing the pipeline: run with a model name starting "fake:".
    """

    STATUS_WEIGHTS = (("main bank", 80), ("second bank", 13), ("dormant", 5), ("left", 2))
    # Actions every current persona lists; talk actions are left out because they need a message.
    SAFE_ACTIONS = ("log in and check balance", "wait and see", "try a transfer or P2P payment",
                    "call or chat with support", "use Cobalt less", "move some money to another bank")

    def __init__(self, *, timeout_seconds=None):
        self.calls = 0

    async def generate(self, *, prompt, model, seed, temperature, schema):
        import hashlib
        import json
        import random

        self.calls += 1
        digest = hashlib.sha256(json.dumps([seed, model, prompt]).encode()).digest()
        rng = random.Random(int.from_bytes(digest[:8], "big"))
        data = self._value(schema, rng, "")
        if isinstance(data, dict) and "status" in data:
            self._turn(data, rng, retried="previous answer was rejected" in prompt)
        return json.dumps(data, ensure_ascii=False)

    def _value(self, schema, rng, name):
        kind = schema.get("type")
        if isinstance(kind, list):
            kind = next((k for k in kind if k != "null"), "null")
        if "enum" in schema:
            return rng.choice(schema["enum"])
        if kind == "object":
            return {key: self._value(sub, rng, key) for key, sub in schema.get("properties", {}).items()}
        if kind == "array":
            return []
        if kind == "integer":
            return rng.randint(schema.get("minimum", 1), schema.get("maximum", 5))
        if kind == "number":
            return float(rng.randint(int(schema.get("minimum", 0)), 1000))
        if kind == "boolean":
            return rng.random() < 0.8
        if kind == "string":
            return f"fake {name or 'text'} {rng.randrange(16**6):06x}"[: schema.get("maxLength", 200)]
        return None

    def _turn(self, data, rng, *, retried):
        statuses, weights = zip(*self.STATUS_WEIGHTS)
        status = rng.choices(statuses, weights)[0]
        data["status"] = status
        # money is cumulative and may not go down; a retry answers "moved most", which never does.
        data["money"] = ("moved most" if status == "left" or retried else
                         rng.choices(("kept", "moved some", "moved most"), (85, 12, 3))[0])
        if "new_money" in data:
            data["new_money"] = rng.choices(("none", "some", "a lot"), (85, 12, 3))[0]
        data["balance"] = None
        data["active_in_last_30_days"] = status in ("main bank", "second bank")
        data["actions"] = rng.sample(self.SAFE_ACTIONS, 0 if status == "left" else rng.randint(1, 2))
        data["heard_from"] = [rng.choice(("bank", "news", "none"))]
        # A rating needs the review action. A retry always rates, so it never erases a round-one rating.
        if retried or (status != "left" and rng.random() < 0.3):
            data["actions"].append("post a review (App Store / Google / Trustpilot)")
            data["app_rating"] = rng.randint(3, 5) if rng.random() < 0.7 else rng.randint(1, 2)
        else:
            data["app_rating"] = None
        # A retry after a round-two rejection takes the highest complaint, which is never refused.
        data["complaint"] = "cfpb" if retried else rng.choices(("none", "bank", "cfpb"), (90, 8, 2))[0]
        data["messages"] = []

    async def close(self):
        return None


@dataclass(frozen=True)
class ModelResult:
    data: dict
    call: str
    model: str


class LoggedModel:
    def __init__(self, transport, writer, settings):
        self.transport = transport
        self.writer = writer
        self.settings = settings
        self.semaphore = asyncio.Semaphore(settings.concurrency)

    async def turn(self, *, persona, week, round_number, prompt, validate, schema=TURN_SCHEMA):
        rejection = None
        last_stage = "transport"
        for attempt in range(1, self.settings.attempts + 1):
            model = self.settings.model
            if attempt == self.settings.attempts and attempt > 1 and self.settings.fallback_model:
                model = self.settings.fallback_model
            actual_prompt = prompt
            if attempt > 1:
                actual_prompt += "\n\nReturn valid JSON matching the response schema and permitted contacts. "
                actual_prompt += "Preserve actions already taken this week. Do not add extra fields."
                if rejection:
                    # Only our own validation messages are echoed; SDK errors may carry URLs or keys.
                    actual_prompt += f"\nYour previous answer was rejected for this reason: {rejection} Fix exactly that."
            record = {"id": uuid.uuid4().hex, "persona": persona, "week": week,
                      "round": round_number, "prompt": actual_prompt, "response": "",
                      "model": model, "seed": self.settings.seed, "attempt": attempt}
            started = time.monotonic()
            succeeded = False
            async with self.semaphore:
                stage = "transport"
                try:
                    raw = await asyncio.wait_for(
                        self.transport.generate(prompt=actual_prompt, model=model,
                                                seed=self.settings.seed,
                                                temperature=self.settings.temperature, schema=schema),
                        timeout=self.settings.timeout_seconds,
                    )
                    if not isinstance(raw, str):
                        raise ValueError("Model response must be text")
                    record["response"] = raw
                    stage = "validation"
                    data = validate(raw)
                    succeeded = True
                    record["valid"] = True
                except asyncio.CancelledError:
                    record["valid"] = False
                    record["error_type"] = "CancelledError"
                    raise
                except Exception as error:
                    # SDK exception strings can contain authenticated URLs: never log them.
                    record["valid"] = False
                    record["error_type"] = type(error).__name__
                    record["error_stage"] = stage
                    rejection = str(error)[:300] if stage == "validation" else None
                    last_stage = stage
                finally:
                    record["elapsed_seconds"] = round(time.monotonic() - started, 4)
                    self.writer.append("calls.jsonl", record)
            if succeeded:
                return ModelResult(data, record["id"], model)
            if attempt < self.settings.attempts:
                # A rejected answer is retried at once with the reason; a transport failure (rate limit,
                # timeout, connection) backs off long enough for the quota window to pass.
                if last_stage == "validation":
                    await asyncio.sleep(0.5)
                else:
                    await asyncio.sleep(min(self.settings.transport_backoff_seconds * 2 ** (attempt - 1), 30))
        raise RuntimeError(f"Model attempts exhausted for persona {persona}, week {week}, round {round_number}")
