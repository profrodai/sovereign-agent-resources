# Author your first capability

```text
Author:        Sparring (zeocore seat), operated by Rod Rivera
Verified on:   2026-09-02
Verified by:   Sparring (zeocore seat), operated by Rod Rivera
Verified with: zeocore 0.6.0, uv
Audience:      Builders writing their first typed, inspectable zeocore operation
Time:          ~15 minutes
```

A **capability** is a typed operation a runner can inspect before it invokes.
In this tutorial you build one end to end — describe its input and output with
Pydantic models, declare its identity and effects, supply the runner-owned
`ToolContext`, register it, invoke it, and read the structured result. It runs
on a clean machine with **no keys, no accounts, and no network**.

## Run it

```bash
uv sync
uv run python src/main.py
```

## What you should observe

```text
Hello, World!
```

That one line is the whole point: it is not a `print` from your own function.
It is `result.data.message`, pulled out of a `CapabilityResult` that the runner
produced by invoking a registered `BoundCapability`. The greeting travelled
through the typed contract rather than around it.

## What the code is doing

**1 — the contract.** `GreetRequest` and `GreetResponse` are Pydantic models.
They are the capability's signature: a runner can read them without executing
anything.

**2 — the declaration.** `@capability` attaches identity (`name`, `version`),
an `EffectKind`, and a `CapabilityExample`. The example is machine-readable
documentation — it travels with the capability, so a caller does not have to
guess what a valid request looks like.

**3 — the context.** `ToolContext` is supplied by the *runner*, not by the
capability. It carries `run_id`, the logger, the filesystem service, and the
work/output directories. The capability never opens a path of its own choosing;
it receives one. That is what makes the operation governable.

**4 — registration and invocation.** `bound_capability_of()` binds the function
to its declared contract; `CapabilityRegistry` holds it; `invoke_sync()` runs
it and returns a `CapabilityResult`.

**5 — the result.** `CapabilityResult` carries `data` on success and a
`human_message` otherwise. The last line reads `result.data.message if
result.data else result.human_message` — the shape you handle every time,
rather than a bare return value you have to trust.

## What this does NOT show

- **No error path.** Every step here succeeds. Failure handling, `ok=False`
  results, and `ErrorInfo` are a separate lesson.
- **No async invocation.** `invoke_sync` is the synchronous entry point.
- **No real side effects.** The capability writes nothing outside the
  `TemporaryDirectory` the context hands it, and makes no network calls.
- **No credentials, and nothing that needs them.** Integrations that talk to
  Google or Bluesky are different resources with different requirements.

## Verified against

`zeocore==0.6.0`, installed from the committed `uv.lock` and confirmed with
`uv run python -c "import zeo_core; print(zeo_core.__version__)"` → `0.6.0`.
The `Hello, World!` output above was produced by running the command shown,
not transcribed from the upstream tutorial.
