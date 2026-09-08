# Dependencies

## Required For Local Tests

| Dependency | Why |
|---|---|
| `uv` | Python environment and command runner |
| Python 3.11+ | Harness runtime |
| `pytest` | Dev/test dependency installed by `uv sync --dev` |

The historical gym harness uses the Python standard library. The live `game.py`
bridge uses `websocket-client` and the official Python `mcp` SDK, pinned by `uv.lock`.

## Required For Live Argentum Smokes

| Dependency | Why |
|---|---|
| Java 21 | Argentum `gym-server` build/run |
| Argentum Engine | MTG rules engine and HTTP gym server |

Argentum remains a separate, unmodified upstream checkout in the ignored evidence
directory. Updated from upstream `main` on 2026-09-07 to
`d812e2a418a9fba8f6a9b24c4582d338e0296405` (previously `d40ea1de2`).
Use that exact revision to reproduce this baseline; do not silently track a moving branch.

Clone Argentum into the ignored evidence directory:

```bash
mkdir -p 05_evidence/repos
git clone https://github.com/wingedsheep/argentum-engine.git 05_evidence/repos/argentum-engine
git -C 05_evidence/repos/argentum-engine checkout --detach d812e2a418a9fba8f6a9b24c4582d338e0296405
```

Run the server:

```bash
cd 05_evidence/repos/argentum-engine
JAVA_HOME=/opt/homebrew/opt/openjdk@21 just gym-server
```

Install `just` if missing (`brew install just` on macOS). Upstream's build/test
recipes use a machine-wide build semaphore. Verify the HTTP integration with
`JAVA_HOME=/opt/homebrew/opt/openjdk@21 just test-gym-server`.

The upstream engine owns game state, rule enforcement, legal actions, snapshots,
and forks. Our Python client is a transport boundary, not another rules engine.
The updated API also supports action parameters (attackers, blockers, targets,
and X values) and a separate decision-submission endpoint. The old harness does
not yet expose those capabilities. Observations have a fixed configured player
perspective; switching agents does not automatically switch that perspective.

Baseline verified on 2026-09-07: `just test-gym-server` rebuilt the SDK, all
card modules, rules engine, gym, and HTTP server and passed 11 tests. The Python
suite passed 11 tests; the existing live smoke runner passed 13/13 with
`--max-steps 64`. The three 64-step heuristic episodes took 78–143 ms each,
including HTTP and harness overhead on this machine. These smoke results do not
establish full-game correctness or correct two-seat private-information handling.

## Required For Real Codex Episodes

| Dependency | Why |
|---|---|
| local `codex` CLI | Model-backed action selection via `codex exec` |
| Codex login | The shell does not need API keys if the CLI is already authenticated |

The harness invokes:

```bash
codex exec --ephemeral --skip-git-repo-check --sandbox read-only --output-schema schemas/codex_action.schema.json ...
```

## Optional Network Dependencies

| Source | Why |
|---|---|
| Scryfall API | Card oracle context for visible cards |
| MTGJSON | Bulk card/set/product data research |
| Commander Spellbook | Combo-task research |
| 17Lands public datasets | Draft/game-data research |

These are documented in `00_admin/source_ledger.csv`.
