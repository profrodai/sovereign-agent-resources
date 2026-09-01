# Resource template

A resource is a directory a stranger can run. Every resource, in any tier, carries:

```
your-resource/
├── README.md        # what it is, how to run it, what you should observe
├── pyproject.toml   # pinned to the catalog versions (maintained tier)
├── uv.lock          # committed — reproducibility is the promise
└── src/ or *.py     # the actual material
```

## README requirements

1. **One-paragraph promise** — what the reader watches happen.
2. **Run it** — exact commands, `uv sync` + `uv run ...`, nothing hidden.
3. **What you should observe** — real output, honestly labeled.
4. **Verified against** — `sovereign-agent==X` / `zeocore==Y` (the migration
   tooling rewrites these lines when the catalog moves).
5. **Author + date** (community tier).

## pyproject requirements

- Exact pins for governed packages: `"sovereign-agent==1.1.1"`, not `>=`.
- Optional smoke command the catalog CI will run:

```toml
[tool.sovereign-catalog]
smoke = "python check_me.py"
```

## The bar

If `uv sync && uv run <your entry point>` does not work on a clean machine
with no keys and no accounts, it is not ready. Live-model material must state
its extra requirements (e.g. Ollama) in the README's first screen.
