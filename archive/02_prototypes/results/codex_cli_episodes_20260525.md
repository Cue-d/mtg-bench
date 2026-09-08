# Codex CLI Episodes

Date: 2026-05-25

## What Changed

The harness now has a real `CodexCliAgent` that calls local `codex exec` with a JSON schema:

```text
schemas/codex_action.schema.json
```

The returned `actionId` is validated against the current Argentum legal-action mask before the engine is stepped.

## Runs

### One-Step Baseline

Command:

```bash
uv run python 02_prototypes/scripts/run_codex_cli_episode.py --steps 1 --timeout-seconds 240 --output 02_prototypes/results/codex_cli_episode_20260525T0343Z.json
```

Result:

| Check | Result |
|---|---|
| Status | `ok=true` |
| Events | 2 |
| Codex choice | `actionId=0` |
| Validation | `valid=true`, legal IDs `[0]` |
| Engine step | State digest changed after pass priority |

### Sixteen-Step Episode

Command:

```bash
uv run python 02_prototypes/scripts/run_codex_cli_episode.py --steps 16 --timeout-seconds 240 --output 02_prototypes/results/codex_cli_episode_20260525T0344Z.json
```

Result:

| Check | Result |
|---|---|
| Status | `ok=true` |
| Events | 17 |
| Validated Codex steps | 16 |
| Non-pass choices | Played `Mountain`, cast `Raging Goblin` |
| Final state | Turn 1, combat/end combat |
| Latency finding | One `codex exec` per priority action is usable for smokes, but too slow for full games |

### Oracle-Context Episode

Command:

```bash
uv run python 02_prototypes/scripts/run_codex_cli_episode.py --steps 8 --include-oracle-context --timeout-seconds 240 --output 02_prototypes/results/codex_cli_oracle_episode_20260525T0346Z.json
```

Result:

| Check | Result |
|---|---|
| Status | `ok=true` |
| Events | 9 |
| Validated Codex steps | 8 |
| Tool context | Scryfall-backed oracle context enabled |
| Notable choice | Played `Mountain`, then declined to float unused red mana |

## Interpretation

Codex can now play legal moves through the harness. The current play quality is limited by observation design, stateless prompting, and one-Codex-call-per-priority latency. The next research step is action-window compression: auto-pass forced priority windows and call Codex only when there is a strategic choice.
