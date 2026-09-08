# mage-bench Smoke

Repository: `05_evidence/repos/mage-bench`

## Checkout

| Fact | Value |
|---|---|
| Size | 1.4 GB |
| Files | 41,869 checkout files |
| Commit | `e723aacf` |
| Commit date | 2026-05-22 08:15:07 -0700 |

## Local Tooling

| Tool | Result |
|---|---|
| `uv` | Present, `uv 0.7.12` |
| FFmpeg | Present, `ffmpeg version 7.1.1` |
| Maven | Installed during run, `Apache Maven 3.9.16` |
| JDK | Pinned to Homebrew `openjdk@21`, Java `21.0.11` |

## Python Smoke

Command:

```bash
uv run pytest tests/test_magebench_imports.py tests/test_jumpstart.py -q
```

Result:

```text
12 passed in 0.03s
```

## Observed Architecture

mage-bench has three core layers:

1. XMage server for rules and game state.
2. Java bridge/observer clients, where the bridge exposes MCP tools and the observer records/logs games.
3. Python orchestrator/pilot/export pipeline for running games, calling LLMs, tracking costs, exporting replays, and running blunder analysis.

Default config `jumpstart-dumb` runs two CPU players and should not need API keys once Maven/Java build tooling is available.

## Maven Build Smoke

Command:

```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21 mvn -q -DskipTests -pl Mage.Server,Mage.Client,Mage.Client.Bridge -am install
```

Result: exited `0`.

## CPU Game Smoke

Command:

```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21 uv run python -m magebench.cli --config configs/jumpstart-dumb.json --skip-compile
```

Result:

| Check | Result |
|---|---|
| Server startup | Ready on port `17171` |
| Config | `configs/jumpstart-dumb.json` |
| Mage 1 deck | `Discarding 2 + Feathered Friends` |
| Mage 2 deck | `Elves + Rainbow` |
| Spectator | Connected and watched game |
| Game completion | `GAME_OVER` in server and spectator logs |
| Export/lifecycle | Manual `SIGINT` was needed; merged `game.jsonl` only contains `reason=spectator_closed` |

Log directory:

```text
/Users/snbafana/.mage-bench/logs/game_20260524_161359
```

Relevant evidence:

```text
spectator.log: GAME_OVER received for game cef341cb-23c0-430f-8e8f-675bd540f2b5
server.log: endGame completed for game cef341cb-23c0-430f-8e8f-675bd540f2b5
```

## Interpretation

mage-bench should be treated as the full-card-coverage reference path and possible fork point. It is less attractive than Argentum for a clean first Gym adapter, but much more attractive for real public LLM-vs-MTG evaluation because it already has the XMage bridge, replay, website, and leaderboard pipeline.

The immediate blocker is not buildability or rules execution; those work. The blocker is clean unattended lifecycle/export for the default CPU smoke in this local run.
