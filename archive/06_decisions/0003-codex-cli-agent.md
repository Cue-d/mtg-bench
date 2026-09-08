# Decision 0003: Codex CLI Agent

Date: 2026-05-25

## Decision

Use local `codex exec` as the first real model-backed player instead of requiring API keys.

## Why

The shell has a logged-in Codex CLI but no `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, or `ANTHROPIC_API_KEY`.

The CLI supports `--output-schema`, which lets the harness require a strict JSON action shape:

```json
{"actionId": 0, "reason": "Only legal action is pass priority."}
```

## Verified

The harness ran:

- one real Codex step
- a 16-step Codex episode
- an 8-step Codex episode with Scryfall oracle context

Every Codex-selected `actionId` was validated against Argentum's current legal-action mask before stepping the engine.

## Implication

The harness can now prove the loop:

1. Argentum emits observation and legal actions.
2. Harness renders a Codex-facing prompt and tool surface.
3. Codex returns schema-valid JSON.
4. Harness validates the action.
5. Argentum executes the move.

The remaining problem is not legality. It is game-play quality and latency. The next layer should compress action windows and avoid calling Codex for trivial pass-priority decisions.
