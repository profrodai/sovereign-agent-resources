#!/usr/bin/env bash
# One-time setup for the live Sovereign Agent demo.
# Safe to re-run. Usage: bash setup.sh [ollama|openai|anthropic]
set -euo pipefail
cd "$(dirname "$0")"

echo "==> 1/4  Checking uv ..."
if ! command -v uv >/dev/null 2>&1; then
  echo "    ERROR: 'uv' not found. Install it first:"
  echo "      curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "    (or: brew install uv)  Docs: https://docs.astral.sh/uv/"
  exit 1
fi
echo "    using: $(uv --version)"

echo "==> 2/4  Installing sovereign-agent + zeocore from PyPI (uv supplies Python 3.14) ..."
uv sync
echo "    installed:"
uv pip list 2>/dev/null | grep -Ei 'sovereign-agent|zeocore' || true

PROVIDER_ARGS=()
if [[ $# -gt 1 ]]; then
  echo "ERROR: usage: bash setup.sh [ollama|openai|anthropic]"
  exit 2
elif [[ $# -eq 1 ]]; then
  PROVIDER_ARGS=(--provider "$1")
fi
PROVIDER="$(uv run python model_provider.py "${PROVIDER_ARGS[@]}" --print-provider)"

echo "==> 3/4  Checking provider: $PROVIDER ..."
if [[ "$PROVIDER" == "ollama" ]]; then
  if ! command -v ollama >/dev/null 2>&1; then
    echo "    ERROR: 'ollama' not found. Install it from https://ollama.com/download"
    exit 1
  fi
  MODEL="$(uv run python model_provider.py "${PROVIDER_ARGS[@]}" --print-model)"
  OLLAMA_MODELS="$(ollama list 2>/dev/null)"
  # Capture before grep: grep -q can otherwise SIGPIPE `ollama list` under pipefail.
  if ! grep -F "$MODEL" <<<"$OLLAMA_MODELS" >/dev/null; then
    echo "    pulling model $MODEL (this is a few GB, one time) ..."
    ollama pull "$MODEL"
  else
    echo "    model $MODEL already present."
  fi
else
  uv run python model_provider.py "${PROVIDER_ARGS[@]}"
  echo "    key found in the environment or ignored local .env (value not printed)."
fi

echo "==> 4/4  Finalizing ..."
if [[ "$PROVIDER" == "ollama" ]]; then
  echo "    warming the local model so the live run is fast ..."
  printf '' | ollama run "$MODEL" >/dev/null 2>&1 || true
else
  echo "    no API call made during setup. The first live demo makes the first billed request."
fi

echo
echo "Setup complete. Now run, in order:"
echo "  uv run sovereign-agent demo store --mode simulated   # offline, deterministic"
echo "  uv run python demo_tool_calling.py --provider $PROVIDER"
echo "  uv run python demo_full_governance.py --provider $PROVIDER"
