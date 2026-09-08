# Decision 0002: uv Harness Shape

Date: 2026-05-25

## Decision

Promote the one-off Argentum HTTP script into a uv-backed Python harness package inside the dataroom.

## Current Shape

| Path | Purpose |
|---|---|
| `pyproject.toml` | uv project definition and dev dependency group |
| `mtgbench_harness/argentum.py` | Argentum HTTP client, observation summaries, agent view |
| `mtgbench_harness/gym_adapter.py` | Gymnasium-shaped adapter with local legal-action validation |
| `mtgbench_harness/agents.py` | First-legal and Codex-heuristic placeholder agents |
| `mtgbench_harness/codex_surface.py` | Codex-facing prompt/tool/action-mask surface |
| `mtgbench_harness/smokes.py` | Live smoke suite against Argentum |
| `tests/test_harness_core.py` | Pure unit checks for agent/action/prompt behavior |

## Why

The user goal is to get Codex playing Magic, not just prove Argentum can step. The harness now exposes the exact surface an LLM needs:

- current phase/step/turn/priority state
- visible cards
- legal action IDs
- action descriptions
- tool specs for choosing, card lookup, search, and simulation
- validation that a proposed action ID is currently legal

## Verified

`uv run pytest -q` passed.

`uv run python 02_prototypes/scripts/run_argentum_smokes.py --max-steps 64 --output 02_prototypes/results/argentum_smokes_20260525T0339Z.json` passed 12/12 live smokes against `gym-server`.

## Not Done

The Codex agent is still deterministic placeholder logic. The next step is to plug in a real model/tool loop that reads `render_codex_prompt()`, returns a `choose_action` call, and lets `ArgentumGymAdapter` validate and execute it.
