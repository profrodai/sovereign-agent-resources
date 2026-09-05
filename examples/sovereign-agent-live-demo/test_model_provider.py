"""Offline behavioral checks for provider selection and wire-format normalization."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path
from unittest.mock import patch

from model_provider import (
    ProviderConfig,
    ProviderConfigurationError,
    chat,
    load_dotenv,
    resolve_config,
)


class Response(BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


@contextmanager
def clean_provider_environment():
    names = {
        "SOVEREIGN_DEMO_PROVIDER",
        "SOVEREIGN_DEMO_MODEL",
        "OLLAMA_MODEL",
        "OLLAMA_URL",
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "OPENAI_URL",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_MODEL",
        "ANTHROPIC_URL",
    }
    saved = {name: os.environ.get(name) for name in names}
    for name in names:
        os.environ.pop(name, None)
    try:
        yield
    finally:
        for name in names:
            os.environ.pop(name, None)
            if saved[name] is not None:
                os.environ[name] = saved[name] or ""


class ConfigurationTests(unittest.TestCase):
    def test_dotenv_is_data_and_does_not_override_environment(self):
        with clean_provider_environment(), tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / ".env"
            path.write_text("OPENAI_API_KEY=from-file\nOPENAI_MODEL='file-model'\n", encoding="utf-8")
            os.environ["OPENAI_API_KEY"] = "from-process"
            load_dotenv(path)
            self.assertEqual(os.environ["OPENAI_API_KEY"], "from-process")
            self.assertEqual(os.environ["OPENAI_MODEL"], "file-model")

    def test_cloud_choice_fails_closed_without_key(self):
        with clean_provider_environment(), tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ProviderConfigurationError, "OPENAI_API_KEY is missing"):
                resolve_config("openai", env_path=Path(tmp) / ".env")

    def test_ollama_remains_zero_key_default(self):
        with clean_provider_environment(), tempfile.TemporaryDirectory() as tmp:
            config = resolve_config(env_path=Path(tmp) / ".env")
            self.assertEqual((config.name, config.model, config.api_key), ("ollama", "qwen3:latest", ""))

    def test_config_repr_never_contains_api_key(self):
        config = ProviderConfig("openai", "gpt-5-mini", "https://example.invalid", "must-not-leak")
        self.assertNotIn("must-not-leak", repr(config))

    def test_actor_mode_does_not_reopen_dotenv(self):
        with clean_provider_environment(), patch("model_provider.load_dotenv") as loader:
            os.environ["OPENAI_API_KEY"] = "allowlisted"
            config = resolve_config("openai", load_file=False)
        loader.assert_not_called()
        self.assertEqual(config.name, "openai")


class WireFormatTests(unittest.TestCase):
    def test_openai_tool_call_is_normalized(self):
        payload = {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_1",
                                "type": "function",
                                "function": {"name": "inspect_inventory", "arguments": '{"sku":"SKU-VANILLA"}'},
                            }
                        ],
                    }
                }
            ]
        }
        config = ProviderConfig("openai", "gpt-5-mini", "https://example.invalid", "secret")
        with patch("urllib.request.urlopen", return_value=Response(json.dumps(payload).encode())) as opened:
            message = chat(config, [{"role": "user", "content": "inspect"}], [{"type": "function", "function": {"name": "inspect_inventory", "description": "read", "parameters": {"type": "object"}}}])
        self.assertEqual(message["tool_calls"][0]["function"]["name"], "inspect_inventory")
        self.assertEqual(opened.call_args.args[0].headers["Authorization"], "Bearer secret")

    def test_openai_tool_result_drops_ollama_only_name(self):
        payload = {"choices": [{"message": {"role": "assistant", "content": "RESTOCK_UNITS: 1"}}]}
        config = ProviderConfig("openai", "gpt-5-mini", "https://example.invalid", "secret")
        messages = [
            {"role": "user", "content": "inspect"},
            {"role": "tool", "content": "{}", "tool_name": "inspect_inventory", "tool_call_id": "call_1"},
        ]
        with patch("urllib.request.urlopen", return_value=Response(json.dumps(payload).encode())) as opened:
            chat(config, messages)
        sent = json.loads(opened.call_args.args[0].data)
        self.assertEqual(sent["messages"][-1], {"role": "tool", "content": "{}", "tool_call_id": "call_1"})

    def test_anthropic_tool_use_and_result_round_trip(self):
        first = {
            "content": [
                {
                    "type": "tool_use",
                    "id": "toolu_1",
                    "name": "inspect_inventory",
                    "input": {"sku": "SKU-VANILLA"},
                }
            ]
        }
        second = {"content": [{"type": "text", "text": "RESTOCK_UNITS: 1"}]}
        config = ProviderConfig("anthropic", "claude-sonnet-4-6", "https://example.invalid", "secret")
        responses = [Response(json.dumps(first).encode()), Response(json.dumps(second).encode())]
        messages = [{"role": "system", "content": "use the tool"}, {"role": "user", "content": "inspect"}]
        tool = {"type": "function", "function": {"name": "inspect_inventory", "description": "read", "parameters": {"type": "object"}}}
        with patch("urllib.request.urlopen", side_effect=responses) as opened:
            assistant = chat(config, messages, [tool])
            messages.extend(
                [
                    assistant,
                    {"role": "tool", "tool_call_id": "toolu_1", "tool_name": "inspect_inventory", "content": '{"on_hand":2}'},
                ]
            )
            final = chat(config, messages, [tool])
        sent = json.loads(opened.call_args_list[1].args[0].data)
        self.assertEqual(sent["messages"][-1]["content"][0]["tool_use_id"], "toolu_1")
        self.assertEqual(final["content"], "RESTOCK_UNITS: 1")
        self.assertEqual(opened.call_args_list[0].args[0].headers["X-api-key"], "secret")


if __name__ == "__main__":
    unittest.main(verbosity=2)
