# Decision 0001: First Engine Spike

Date: 2026-05-24

## Decision

Use Argentum as the first implementation adapter and keep mage-bench/XMage as the full-card-coverage reference path.

## Rationale

Argentum already exposes the benchmark-shaped surface:

- env creation/reset
- observations
- legal action IDs
- stepping
- fork/snapshot/restore
- batch stepping
- hidden-information masking
- OpenAPI over HTTP
- MCTS/self-play trainer

The local verification passed under JDK 21, including both unit/integration tests and a live HTTP create/step/dispose smoke.

mage-bench is more mature as a public LLM benchmark and much broader because it builds on XMage. But it is heavier operationally: 1.4 GB checkout, Java/Maven build, server/client/observer orchestration, and GUI/video concerns. Its Python-side smoke passed, so it remains a strong second path.

## Consequences

First prototype:

1. Write a Python adapter for Argentum `gym-server`.
2. Build a tiny task registry around explicit decks and supported sets.
3. Run random/heuristic/LLM agents through the same adapter.
4. Emit JSONL decisions and score from engine state.

Second prototype:

1. Finish mage-bench Java build/run once Maven is available.
2. Run `jumpstart-dumb` CPU config.
3. Inspect exported game logs and MCP tool surfaces.
4. Decide whether to fork mage-bench, wrap it, or only borrow architecture.

## Rejected For Now

Do not hand-roll a new Magic engine.

Do not depend on live scraping of 17Lands curated UI data.

Do not make full-game win rate the first benchmark metric; start with deterministic subtasks and short-horizon decisions.

