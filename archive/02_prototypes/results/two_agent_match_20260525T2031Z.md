# Two-Agent Argentum Match Smoke

Date: 2026-05-25

## What Changed

Added a reusable two-agent match runner for Argentum.

The runner:

- creates an Argentum env through `ArgentumGymAdapter`
- assigns current player ids to seats `A` and `B`
- routes each decision to the matching agent
- validates every selected `actionId` before stepping
- records seat, player id, agent name, action id, before/after summaries, terminal state, and winner

## Commands

Unit tests:

```bash
uv run pytest -q
```

Result: `11 passed`.

Mixed-agent route smoke:

```bash
uv run python 02_prototypes/scripts/run_two_agent_match.py \
  --agent-a first-legal \
  --agent-b codex-heuristic \
  --max-steps 64 \
  --output 02_prototypes/results/two_agent_match_20260525T2030Z.json
```

Result: `ok=True steps=64 terminated=False truncated=True`.

Full heuristic match:

```bash
uv run python 02_prototypes/scripts/run_two_agent_match.py \
  --agent-a codex-heuristic \
  --agent-b codex-heuristic \
  --max-steps 1000 \
  --output 02_prototypes/results/two_agent_match_full_20260525T2031Z.json
```

Result:

| Check | Result |
|---|---|
| Agents | `codex-heuristic` vs `codex-heuristic` |
| Steps | `703` |
| Terminated | `true` |
| Truncated | `false` |
| Winner seat | `A` |
| Final turn | `14` |
| Final phase/step | `BEGINNING` / `DRAW` |
| Final legal actions | `0` |

Expanded live smoke suite:

```bash
uv run python 02_prototypes/scripts/run_argentum_smokes.py \
  --max-steps 16 \
  --output 02_prototypes/results/argentum_smokes_20260525T2030Z.json
```

Result: `13 passed, 0 failed`.

## Interpretation

The current harness can now play an actual two-agent Argentum game to terminal state. The agent policy is intentionally simple; future work should improve action-window compression, card/action coverage, deck selection, and per-seat hidden-information views.
