"""One small provider boundary shared by both live demos.

The demos keep governance provider-neutral: Ollama, OpenAI, and Anthropic all
produce the same normalized assistant message. API keys are loaded from the
resource-local ``.env`` file and are never printed or written to run artifacts.
Only Python's standard library is used, so choosing a cloud model adds no SDK.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PROVIDERS = ("ollama", "openai", "anthropic")
DEFAULT_MODELS = {
    "ollama": "qwen3:latest",
    "openai": "gpt-5-mini",
    "anthropic": "claude-sonnet-4-6",
}
DEFAULT_URLS = {
    "ollama": "http://localhost:11434/api/chat",
    "openai": "https://api.openai.com/v1/chat/completions",
    "anthropic": "https://api.anthropic.com/v1/messages",
}
_KEY = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ProviderConfigurationError(ValueError):
    """Configuration is incomplete or unsafe to interpret."""


class ProviderRequestError(RuntimeError):
    """A provider request failed without disclosing credential material."""


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    url: str
    api_key: str = field(default="", repr=False)

    @property
    def location(self) -> str:
        labels = {"openai": "OpenAI", "anthropic": "Anthropic"}
        return "this machine" if self.name == "ollama" else f"the {labels[self.name]} API"


def load_dotenv(path: Path | None = None) -> Path:
    """Load simple KEY=value lines without overriding the process environment.

    This intentionally does not execute shell syntax or interpolate variables.
    """
    env_path = path or Path(__file__).with_name(".env")
    if not env_path.is_file():
        return env_path
    for line_number, raw in enumerate(env_path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            raise ProviderConfigurationError(f"{env_path.name}:{line_number}: expected KEY=value")
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip()
        if not _KEY.fullmatch(key):
            raise ProviderConfigurationError(f"{env_path.name}:{line_number}: invalid variable name")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        os.environ.setdefault(key, value)
    return env_path


def resolve_config(
    provider: str | None = None,
    *,
    env_path: Path | None = None,
    load_file: bool = True,
) -> ProviderConfig:
    if load_file:
        load_dotenv(env_path)
    name = (provider or os.environ.get("SOVEREIGN_DEMO_PROVIDER") or "ollama").lower()
    if name not in PROVIDERS:
        raise ProviderConfigurationError(
            f"unknown provider {name!r}; choose one of: {', '.join(PROVIDERS)}"
        )
    prefix = name.upper()
    model = (
        os.environ.get(f"{prefix}_MODEL")
        or os.environ.get("SOVEREIGN_DEMO_MODEL")
        or DEFAULT_MODELS[name]
    )
    url = os.environ.get(f"{prefix}_URL") or DEFAULT_URLS[name]
    key_name = f"{prefix}_API_KEY"
    api_key = os.environ.get(key_name, "") if name != "ollama" else ""
    if name != "ollama" and not api_key:
        raise ProviderConfigurationError(
            f"{key_name} is missing. Copy .env.example to .env, add the key, "
            "and keep .env uncommitted."
        )
    return ProviderConfig(name=name, model=model, url=url, api_key=api_key)


def _request_json(config: ProviderConfig, body: dict[str, Any], *, timeout: float) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if config.name == "openai":
        headers["Authorization"] = f"Bearer {config.api_key}"
    elif config.name == "anthropic":
        headers.update({"x-api-key": config.api_key, "anthropic-version": "2023-06-01"})
    request = urllib.request.Request(config.url, data=json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310
            payload = json.load(response)
    except urllib.error.HTTPError as error:
        raise ProviderRequestError(
            f"{config.name.title()} returned HTTP {error.code}. Check the API key, model, and account access."
        ) from error
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        raise ProviderRequestError(
            f"Could not reach {config.name} at {config.url}: {type(error).__name__}."
        ) from error
    if not isinstance(payload, dict):
        raise ProviderRequestError(f"{config.name.title()} returned a non-object response.")
    return payload


def _anthropic_messages(messages: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    system_parts: list[str] = []
    out: list[dict[str, Any]] = []
    for message in messages:
        role = message["role"]
        if role == "system":
            system_parts.append(str(message.get("content") or ""))
            continue
        if role == "assistant":
            content: list[dict[str, Any]] = []
            if message.get("content"):
                content.append({"type": "text", "text": str(message["content"])})
            for call in message.get("tool_calls") or []:
                arguments = call["function"]["arguments"]
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                content.append(
                    {
                        "type": "tool_use",
                        "id": call["id"],
                        "name": call["function"]["name"],
                        "input": arguments,
                    }
                )
            out.append({"role": "assistant", "content": content})
            continue
        if role == "tool":
            out.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message["tool_call_id"],
                            "content": str(message.get("content") or ""),
                        }
                    ],
                }
            )
            continue
        out.append({"role": "user", "content": str(message.get("content") or "")})
    return "\n\n".join(system_parts), out


def chat(
    config: ProviderConfig,
    messages: list[dict[str, Any]],
    tools: list[dict[str, Any]] | None = None,
    *,
    timeout: float = 120.0,
) -> dict[str, Any]:
    """Return one provider-neutral assistant message."""
    tools = tools or []
    if config.name == "anthropic":
        system, anthropic_messages = _anthropic_messages(messages)
        body: dict[str, Any] = {
            "model": config.model,
            "max_tokens": 1024,
            "messages": anthropic_messages,
        }
        if system:
            body["system"] = system
        if tools:
            body["tools"] = [
                {
                    "name": tool["function"]["name"],
                    "description": tool["function"].get("description", ""),
                    "input_schema": tool["function"]["parameters"],
                }
                for tool in tools
            ]
        payload = _request_json(config, body, timeout=timeout)
        text_parts: list[str] = []
        calls: list[dict[str, Any]] = []
        for block in payload.get("content") or []:
            if block.get("type") == "text":
                text_parts.append(str(block.get("text") or ""))
            elif block.get("type") == "tool_use":
                calls.append(
                    {
                        "id": block["id"],
                        "type": "function",
                        "function": {"name": block["name"], "arguments": block.get("input") or {}},
                    }
                )
        return {"role": "assistant", "content": "\n".join(text_parts), "tool_calls": calls}

    wire_messages = messages
    if config.name == "openai":
        # Ollama names a tool in a result; OpenAI instead keys it solely by the
        # preceding call id and rejects unknown message fields.
        wire_messages = [
            (
                {
                    "role": "tool",
                    "content": message.get("content") or "",
                    "tool_call_id": message["tool_call_id"],
                }
                if message["role"] == "tool"
                else message
            )
            for message in messages
        ]
    body = {"model": config.model, "messages": wire_messages, "stream": False}
    if tools:
        body["tools"] = tools
    payload = _request_json(config, body, timeout=timeout)
    if config.name == "ollama":
        message = payload.get("message")
    else:
        choices = payload.get("choices") or []
        message = choices[0].get("message") if choices else None
    if not isinstance(message, dict):
        raise ProviderRequestError(f"{config.name.title()} returned no assistant message.")
    return message


def parse_provider_argument(description: str) -> ProviderConfig:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--provider", choices=PROVIDERS, help="overrides SOVEREIGN_DEMO_PROVIDER")
    args = parser.parse_args()
    return resolve_config(args.provider)


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve and validate the live-demo provider.")
    parser.add_argument("--provider", choices=PROVIDERS)
    parser.add_argument("--print-provider", action="store_true")
    parser.add_argument("--print-model", action="store_true")
    args = parser.parse_args()
    config = resolve_config(args.provider)
    if args.print_provider:
        print(config.name)
    elif args.print_model:
        print(config.model)
    else:
        print(f"provider={config.name} model={config.model} location={config.location}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
