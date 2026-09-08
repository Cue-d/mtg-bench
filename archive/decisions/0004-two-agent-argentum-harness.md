# Decision 0004: Two-Agent Argentum Harness

Date: 2026-05-25

## Decision

Use a reusable two-agent match runner on top of `ArgentumGymAdapter`.

The runner assigns Argentum player ids to two agent seats, routes each legal-action decision to the agent for the current `agentToAct` / `priorityPlayerId`, validates the selected `actionId` through the adapter, and records a replayable JSON trace.

## Rationale

This extends the existing owner instead of creating a second runtime:

- `ArgentumGymAdapter` remains the only HTTP step/validation owner.
- `Agent` / `choose_action(observation)` remains the agent contract.
- existing smoke episodes now use the same two-agent loop.
- `run_two_agent_match.py` is only a thin CLI wrapper around the reusable runner.

## Verification

Pure harness tests:

```bash
uv run pytest -q
```

Result: `11 passed`.

Live Argentum mixed-agent smoke:

```bash
uv run python 02_prototypes/scripts/run_two_agent_match.py \
  --agent-a first-legal \
  --agent-b codex-heuristic \
  --max-steps 64 \
  --output 02_prototypes/results/two_agent_match_20260525T2030Z.json
```

Result: `ok=True steps=64 terminated=False truncated=True`.

Live Argentum full heuristic match:

```bash
uv run python 02_prototypes/scripts/run_two_agent_match.py \
  --agent-a codex-heuristic \
  --agent-b codex-heuristic \
  --max-steps 1000 \
  --output 02_prototypes/results/two_agent_match_full_20260525T2031Z.json
```

Result: `ok=True steps=703 terminated=True truncated=False winnerSeat=A`.

Expanded Argentum smoke suite:

```bash
uv run python 02_prototypes/scripts/run_argentum_smokes.py \
  --max-steps 16 \
  --output 02_prototypes/results/argentum_smokes_20260525T2030Z.json
```

Result: `13 passed, 0 failed`.

## Current Limitations

This first runner proves two-agent routing and full-game completion. It does not yet solve stronger play quality, pass-priority compression, per-seat hidden-information perspective switching, richer deck selection, or broader Argentum card/action coverage.
