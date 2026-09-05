# Six advanced Sovereign Agent patterns

```text
Author:        Principal (sovereign-agent), operated by Rod Rivera
Verified on:   2026-09-05
Verified by:   Principal (sovereign-agent), operated by Rod Rivera
Verified with: sovereign-agent 1.3.0, uv
Audience:      Agent builders who know the basic governed-work loop
Time:          30–45 minutes, or about 5 minutes per focused lesson
```

Six small programs turn Sovereign Agent 1.3's advanced mechanisms into
experiments you can read, run, and modify. Each lesson starts from a disposable
SQLite organization, exercises one failure boundary with no model or network,
and asserts the invariant before it prints the observation. The combined smoke
test runs every lesson in a separate process so hidden state cannot make a later
example pass.

## What you will learn

| Lesson | Question it answers | Invariant you can falsify |
|---|---|---|
| `isolation_policy.py` | Which boundary authorized this action? | Passing one isolation plane says nothing about another; deny wins. |
| `durable_automation.py` | Did a scheduled check actually create work? | A non-firing condition persists state but creates no run; a due slot fires once. |
| `recoverable_context.py` | Can context shrink without deleting history? | Compaction appends a derived view while every source transcript row survives. |
| `session_incarnations.py` | Which host may finish after takeover? | A higher incarnation fences the expired worker; delivery attempts remain durable. |
| `tool_discovery.py` | Does finding a tool permit its use? | Discovery ranks candidates; policy independently authorizes or refuses them. |
| `hybrid_memory.py` | Why did this memory rank, and was it visible? | Access filtering precedes ranking, and every score exposes its components. |

These are not six unrelated utilities. Together they separate questions that
agent systems often collapse:

```text
what can the process reach?        isolation policy
what work is due?                  durable automation
what context should the model see? derived context view
which worker still owns the run?   session incarnation
what capability is relevant?       tool discovery
what prior fact is relevant?        hybrid memory
```

No answer in one row grants authority in another.

## Run everything

From this directory:

```bash
uv sync
uv run python src/run_all.py
uv run python check_examples.py
```

The first command installs the exact catalog pin from PyPI. `run_all.py` shows
the observations; `check_examples.py` is the behavioral smoke test CI runs.

## What you should observe

This is the real output produced by `uv run python src/run_all.py`:

```text
=== isolation_policy ===
inside path allowed: True
process isolation: UNAVAILABLE
outside path: REFUSED
deny wins: REFUSED
=== durable_automation ===
first check: NO_FIRE, runs=0, state={"checks":1}
second check: SUCCEEDED, runs=1, payload=order vanilla
=== recoverable_context ===
compaction appended: True
source rows: 7 -> 7
rendered: 6, summaries=1, user messages=2
=== session_incarnations ===
incarnation: 1 -> 2
stale completion: REFUSED
durable completions: 1
delivery attempts: 2
=== tool_discovery ===
safe discovery: read_inventory, matches=2, truncated=True
dangerous discovery: delete_inventory
dangerous authorization: REFUSED
=== hybrid_memory ===
visible ids: public-rule,public-supplier
private-other visible: False
top score provenance: lexical=0.400, semantic=1.000, recency=0.968, importance=0.800
semantic status: used
```

The smoke test produces one line per independently executed lesson:

```text
PASS isolation_policy.py: 2 invariants
PASS durable_automation.py: 2 invariants
PASS recoverable_context.py: 2 invariants
PASS session_incarnations.py: 2 invariants
PASS tool_discovery.py: 2 invariants
PASS hybrid_memory.py: 2 invariants
```

## Run one lesson

Every file is a standalone program:

```bash
uv run python src/isolation_policy.py
uv run python src/durable_automation.py
uv run python src/recoverable_context.py
uv run python src/session_incarnations.py
uv run python src/tool_discovery.py
uv run python src/hybrid_memory.py
```

Read the file immediately after running it. The examples deliberately keep the
setup beside the observation: no framework wrapper hides the SQLite query,
fixed clock, policy, or failure that makes the result true.

## Break-it experiments

Try one change at a time, predict the result, then rerun both the lesson and
`check_examples.py`:

1. Add the outside directory to `filesystem_roots`. Which refusal disappears,
   and why does the tool denial remain?
2. Change the first automation decision to `fire=True`. The checker's
   `runs=0` invariant should fail, exposing the difference between observing a
   condition and creating work.
3. Replace context compaction with deletes from `transcript_messages`. The
   `7 -> 7` source-history assertion should fail even if the rendered prompt is
   shorter.
4. Remove the incarnation comparison from your mental model and predict what
   the stale host would overwrite. The shipped API still refuses its finish.
5. Put `delete_inventory` in both allow and deny. It already is: the refusal
   demonstrates deny precedence rather than allowlist membership.
6. Change `private-other` to `public`. It should become a ranking candidate,
   proving that access control—not a low relevance score—kept it absent.

## Why the examples use fixed clocks and disposable roots

Automation, leases, recency, and ranking all depend on time. A wall clock would
make the output drift and hide boundary cases, so the lessons inject a fixed UTC
instant. Each stateful lesson uses `TemporaryDirectory`; it leaves no database
behind and cannot inherit a previous run's rows. The coordination lesson uses
two explicit instants to make lease expiry and takeover observable without
sleeping.

## What this does not show

- `IsolationPolicy` is application-level enforcement. `process=UNAVAILABLE` is
  honest: this resource does not create an OS sandbox, container, or egress
  firewall.
- The automation lesson calls one due item directly. It is not a daemon,
  distributed scheduler, or exactly-once claim across arbitrary side effects.
- Compaction uses a deterministic local summarizer. No model is called, and a
  summary is a derived view rather than a replacement for source evidence.
- Host leases use one SQLite database. The lesson teaches fencing semantics,
  not multi-region consensus or clock synchronization.
- Tool discovery is lexical and bounded. It does not execute tools or imply
  that retrieved schemas are safe.
- Memory embeddings are supplied tuples. Sovereign Agent does not generate
  embeddings or claim semantic quality; `semantic_status` reports whether the
  supplied vector contributed.
- No example proves production readiness. The resource is an inspectable
  teaching device that exercises real package code and real refusal paths.

For the mechanisms in the complete governed-store scenario, run
`uvx sovereign-agent@1.3.0 mechanisms`. For the build-break-repair treatment,
continue with the canonical
[Sovereign Agent book](https://github.com/profrodai/sovereign-agent/tree/main/book).

## Files

| File | Purpose |
|---|---|
| `src/isolation_policy.py` | independent isolation planes and deny precedence |
| `src/durable_automation.py` | non-fire state persistence and one successful due run |
| `src/recoverable_context.py` | append-only source transcript plus compact rendered view |
| `src/session_incarnations.py` | lease expiry, takeover fencing, and delivery attempts |
| `src/tool_discovery.py` | bounded relevance search followed by independent policy |
| `src/hybrid_memory.py` | visibility filtering, hybrid ranking, and score provenance |
| `src/run_all.py` | separate-process runner for the six observations |
| `check_examples.py` | catalog smoke test for behavior and expected output |
| `pyproject.toml` / `uv.lock` | exact released dependency and reproducible resolution |
