# Two Real Codex CLI Agents

Date: 2026-05-25

## Successful Bounded Run

Command:

```bash
uv run python 02_prototypes/scripts/run_two_agent_match.py \
  --agent-a codex-cli \
  --agent-b codex-cli \
  --max-steps 8 \
  --codex-timeout-seconds 240 \
  --output 02_prototypes/results/two_codex_cli_match_20260525T2114Z.json
```

Result:

| Check | Result |
|---|---|
| Agents | `codex-cli` vs `codex-cli` |
| OK | `true` |
| Steps | `8` |
| Terminated | `false` |
| Truncated | `true` |
| First non-pass decision | seat `A`, turn 1 precombat main |
| First non-pass action | `actionId=1` |
| First non-pass reason | `Use the turn-one land drop; playing any Mountain is better than passing with no board development.` |

Interpretation: both seats were real `CodexCliAgent` instances calling local `codex exec`. The first six engine decisions were forced priority passes. On the first real main-phase choice, Codex chose to play a Mountain, and the harness validated the returned `actionId`.

## Longer Attempt

Command:

```bash
uv run python 02_prototypes/scripts/run_two_agent_match.py \
  --agent-a codex-cli \
  --agent-b codex-cli \
  --max-steps 32 \
  --codex-timeout-seconds 240 \
  --output 02_prototypes/results/two_codex_cli_match_20260525T2118Z.json
```

Result: `ok=false`.

Failure:

```text
TimeoutExpired: codex exec timed out after 240 seconds
```

The timeout occurred on a postcombat-main choice with two legal actions: pass priority or activate Mountain for red mana.

## Conclusion

The two-agent harness can run real Codex agents against Argentum, but the raw mode is too slow and brittle for full games because it invokes `codex exec` at every priority action. The next harness layer should compress trivial action windows and preserve partial traces on failure before attempting full real-Codex games.
