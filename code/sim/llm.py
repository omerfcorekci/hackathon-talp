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

    async def turn(self, *, persona, week, round_number, prompt, validate):
        for attempt in range(1, self.settings.attempts + 1):
            model = self.settings.model
            if attempt == self.settings.attempts and attempt > 1 and self.settings.fallback_model:
                model = self.settings.fallback_model
            actual_prompt = prompt
            if attempt > 1:
                actual_prompt += "\n\nReturn valid JSON matching the response schema and permitted contacts. "
                actual_prompt += "Preserve actions already taken this week. Do not add extra fields."
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
                                                temperature=self.settings.temperature, schema=TURN_SCHEMA),
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
                finally:
                    record["elapsed_seconds"] = round(time.monotonic() - started, 4)
                    self.writer.append("calls.jsonl", record)
            if succeeded:
                return ModelResult(data, record["id"], model)
            if attempt < self.settings.attempts:
                await asyncio.sleep(min(2 ** (attempt - 1), 4))
        raise RuntimeError(f"Model attempts exhausted for persona {persona}, week {week}, round {round_number}")
