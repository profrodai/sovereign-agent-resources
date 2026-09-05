# Class runbook Rev 3 — bounded providers and ZeoCore credential loading

**Created:** 2026-09-05 · **Last-updated:** 2026-09-05 · **Status:** ACTIVE

This revision supersedes `CLASS-RUNBOOK-2026-09-03-Rev-2.md`. Use Rev 2 for
the full narration and provider setup; the following corrections are binding.

## Credential loading

`model_provider.load_dotenv` now delegates to
`zeo_core.config.load_dotenv_file(..., override=False)`. ZeoCore owns the
explicit configuration-file boundary, while this resource owns only the
provider-specific variable names. Existing process variables still take
precedence, `.env` remains ignored, and no key is printed.

## Timeout behavior

Every provider HTTP request has a 45-second deadline. Sovereign Agent 1.1.1
fences an actor subprocess at 60 seconds, so the inner request must fail first:
the resource-local worker can write a strict failed `ActorReport` instead of
being killed before it records an outcome. A timeout is not completion and does
not authorize a retry or effect.

## Offline proof

`uv run python test_model_provider.py` now runs both live scripts through
loopback protocol doubles for Ollama, OpenAI, and Anthropic. This six-path test
proves provider selection, tool-call translation, report production, and the
full governed acceptance loop without a cloud key or external network request.
It does not replace a real provider render in class.
