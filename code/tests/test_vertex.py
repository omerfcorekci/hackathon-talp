"""Exercise the installed Google SDK against an in-memory HTTP transport only."""

import json
import unittest
from unittest.mock import patch

try:
    import httpx
    from google import genai
except ImportError:
    SDK_AVAILABLE = False
else:
    SDK_AVAILABLE = True

from sim.llm import VertexTransport
from sim.schema import TURN_SCHEMA


@unittest.skipUnless(SDK_AVAILABLE, "Install code/requirements.txt for the SDK contract test")
class VertexTests(unittest.IsolatedAsyncioTestCase):
    async def test_real_sdk_request_schema_seed_and_cleanup_without_network(self):
        captured = []
        response_text = json.dumps({"status": "main bank", "money": "kept", "balance": None,
                                    "active_in_last_30_days": False, "actions": [], "heard_from": [],
                                    "app_rating": None, "complaint": "none", "reason": "test",
                                    "memory": "test", "messages": []})

        async def respond(request):
            captured.append(json.loads(request.content))
            return httpx.Response(200, json={"candidates": [
                {"content": {"role": "model", "parts": [{"text": response_text}]}, "finishReason": "STOP"}]})

        original_client = genai.Client

        def client_factory(**kwargs):
            self.assertTrue(kwargs["vertexai"])
            self.assertNotIn("location", kwargs)
            self.assertNotIn("project", kwargs)
            self.assertEqual(kwargs["http_options"].retry_options.attempts, 1)
            kwargs["http_options"].async_client_args = {"transport": httpx.MockTransport(respond)}
            return original_client(**kwargs)

        with patch.dict("os.environ", {"TALP_KEY": "test-only-placeholder"}), patch.object(genai, "Client", side_effect=client_factory):
            transport = VertexTransport(timeout_seconds=30)
            try:
                raw = await transport.generate(prompt="SDK contract check", model="gemini-3.5-flash-lite",
                                               seed=42, temperature=0.8, schema=TURN_SCHEMA)
            finally:
                await transport.close()
        self.assertEqual(raw, response_text)
        self.assertEqual(len(captured), 1)
        config = captured[0]["generationConfig"]
        self.assertEqual(config["seed"], 42)
        self.assertEqual(config["temperature"], 0.8)
        self.assertEqual(config["responseMimeType"], "application/json")
        self.assertIn("status", config["responseJsonSchema"]["properties"])
        self.assertEqual(config["responseJsonSchema"]["propertyOrdering"][0], "reason")
