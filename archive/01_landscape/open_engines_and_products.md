# Open Engines And Products

## Engine Shortlist

| Candidate | What It Is | Local Result | Why It Matters | Risk |
|---|---|---|---|---|
| Argentum Engine | Kotlin MTG rules engine with `gym`, HTTP `gym-server`, MCTS/self-play trainer, LLM mode | Passed `:gym:test :gym-server:test :gym-trainer:test`; live HTTP create/step/dispose smoke passed | Best first adapter shape: reset, observe, legal actions, step, fork, snapshot, batch | Young project, smaller card coverage, license not detected by GitHub API though repo file is MIT |
| mage-bench | XMage fork/bridge where LLMs play real MTG through MCP tools | Cloned; Python smoke `12 passed`; Maven compile passed; CPU Jumpstart smoke reached game-over but needed manual interrupt to exit/export | Closest existing answer to "LLMs play Magic"; public leaderboard and game export pipeline | Heavy 1.4 GB repo; Java/Maven/GUI/XMage lifecycle complexity |
| XMage | Java rules engine/server/client | Metadata probed | Broad rules/card coverage; mage-bench proves LLM bridge possible | Large codebase, server/client lifecycle complexity |
| Forge | Java MTG game/rules/AI | Metadata probed | Mature, active, broad card support, built-in AI | GPL-3, integration/headless adapter risk |
| Cockatrice | Multiplayer tabletop card client | Metadata probed | Open playtesting UX and protocol reference | Not the rules-enforced simulation core |
| Magarena | Java MTG AI/rules project | Metadata probed | Historical AI reference | Stale; lower priority |
| Wagic | C++ MTG-like engine | Metadata probed | Active-ish engine lineage | Coverage/adapter unknown |
| OpenMTG | Small Python experimental MCTS framework | Search-reviewed | Good toy ideas | Too small for real benchmark core |

## Argentum Verification

Repository cloned to `05_evidence/repos/argentum-engine`.

The initial run failed under Java 25 because Gradle/Kotlin could not parse `25.0.2`. After installing Homebrew `openjdk@21` and pinning `JAVA_HOME=/opt/homebrew/opt/openjdk@21`, the focused test suite passed:

```text
BUILD SUCCESSFUL in 1m 52s
32 actionable tasks: 32 executed
```

The passing modules covered:

| Module | Evidence |
|---|---|
| `:gym` | environment creation, reset, legal actions, step, fork, snapshot/restore, hidden hand masking, sealed decks, MCTS rollout pattern |
| `:gym-server` | `/health`, `/schema-hash`, OpenAPI, create/observe/step/dispose, HTTP error mapping |
| `:gym-trainer` | AlphaZero-style search basics, self-play loop, JSONL self-play rows |

Live HTTP smoke:

| Check | Result |
|---|---|
| `GET /health` | `{"status":"ok"}` |
| `GET /schema-hash` | `argentum-gym-contract@v1.1-oracle-text` |
| `POST /envs` with two explicit Mountain/Raging Goblin decks | created env |
| first legal action | `PassPriority` |
| `POST /envs/{id}/step` | state digest changed |
| `DELETE /envs` | `204` |

The reusable Python client prototype in `02_prototypes/scripts/argentum_http_client.py` also ran successfully against a live server:

| Check | Result |
|---|---|
| Steps requested | 5 |
| Observations returned | 6 |
| Wall time | 296 ms |
| First state | turn 1, beginning/untap |
| Last state | turn 1, beginning/draw |
| Dispose | `204` |

## mage-bench Verification

Repository cloned to `05_evidence/repos/mage-bench`.

Observed repo facts:

| Fact | Value |
|---|---|
| Size | 1.4 GB |
| Files | 41,869 checkout files |
| Commit inspected | `e723aacf`, 2026-05-22 |
| Default free config | `jumpstart-dumb`, two CPU players |
| Architecture | XMage server + Java MCP bridge/observer + Python orchestrator/pilot/export |

Python-side smoke:

```text
uv run pytest tests/test_magebench_imports.py tests/test_jumpstart.py -q
12 passed in 0.03s
```

Maven was installed and the Java compile path passed under JDK 21:

```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21 mvn -q -DskipTests -pl Mage.Server,Mage.Client,Mage.Client.Bridge -am install
```

The smallest CPU config then reached a real XMage game:

```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21 uv run python -m magebench.cli --config configs/jumpstart-dumb.json --skip-compile
```

Observed in logs:

- XMage server ready on port `17171`.
- Two random Jumpstart decks selected: `Discarding 2 + Feathered Friends` and `Elves + Rainbow`.
- Spectator connected and watched game `cef341cb-23c0-430f-8e8f-675bd540f2b5`.
- Server and spectator logs both showed `GAME_OVER`.
- The orchestrator/client did not exit cleanly after game-over; manual `SIGINT` merged only an interrupted `game.jsonl` record.

This validates that mage-bench can build and run a local CPU game here, but its no-LLM smoke still needs lifecycle cleanup before it is a reliable unattended benchmark runner.

## Product/Tool Map

| Product/tool | Open path | Use in MTGBench |
|---|---|---|
| Draftmancer | Open TypeScript repo | Draft UI, sealed/draft task design, bot baseline ideas |
| CubeCobra | Open TypeScript repo | Cube ingestion, deck/cube product model, custom environments |
| Cockatrice | Open client/server | Human playtest table UX, replay/network ideas |
| mage-bench website | Public benchmark UI | Leaderboard, replay, blunder-analysis precedent |
| 17Lands | Public datasets and site UX | Draft/game supervised data and analytics product reference |
| Commander Spellbook | Open backend/API | Combo task source and deterministic reasoning corpus |

## Recommendation

Use a two-track engine strategy:

1. Argentum first for the clean benchmark adapter and training loop, because it already speaks the right shape.
2. mage-bench/XMage second for full-card-coverage LLM evaluation and replay/leaderboard precedent.

Do not start by writing a custom rules engine. The hard part is not a single rules interaction; it is complete priority, stack, hidden information, replacement effects, legal action generation, and replayable state.
