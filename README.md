# MTGBench Dataroom

Research repo for getting Codex-style agents to play Magic: The Gathering through an open rules engine.

## Human versus Codex

[`game.py`](game.py) is the live player bridge: `observe`, `legal_actions`, `act`,
and `resolve_decision`, exposed over stdio MCP. It joins Argentum's existing
game-server WebSocket as one player; the existing browser occupies the other
seat. No engine patches or second game-state store are required. The agent
protocol skill is [`.agents/skills/argentum/SKILL.md`](.agents/skills/argentum/SKILL.md).

Run `uv sync`, start `just server` in the pinned Argentum checkout with Java 21,
then run `npm ci` and `npm run dev -- --host 127.0.0.1` in its `web-client`.
From this repo, run:

```bash
uv run game.py play
```

This creates a normal game with Selesnya Rabbits for the human and Boros Mice for
Codex, prints the human's browser URL, and starts GPT-6 Astra with low reasoning.
Open the printed URL and choose your opening hand. Codex runs one continuing
session with the four game tools preapproved for this invocation. Other configured
MCP servers are disabled for this invocation; global Codex configuration is unchanged.
The app-bundled Codex binary is preferred over an older shell installation.

For two independent Astra-low agents, run `uv run game.py play --self-play`.
The same launcher connects one agent per seat and keeps both sessions running.
Each match saves credentials and separate `codex-rabbits.log` / `codex-mice.log`
files under `.local/<sessionId>/`; tool traces still include each player's ID.
Watch through `http://localhost:5173/?spectate=<sessionId>`, never through a
player token, which would replace that agent's connection.

`.local/game.json` holds the reconnect tokens and deck lists; `.local/codex.log`
holds the agent process output. Both are ignored by Git. Treat tokens as private
seat credentials. The launcher stays running until Codex exits; restarting the
game server loses the game. Do not run `play` again to reconnect: use the saved
human URL, or `codex_command(agentToken, url)` for the existing agent seat.

Explicit tool tracing appends to `.local/tools.jsonl`: paired call/result (or
error) records with timestamps, correlation IDs, arguments, timing, pre-call
turn/phase/player context, and full player-masked results. An optional
`explanation` on action/decision calls records a short public move rationale;
it is never passed to the engine. This is tool I/O, not private model reasoning.
The debug trace can expose the agent's hand; avoid reading it during competitive
play. Logging begins when the instrumented bridge starts, not retroactively.
To reload the bridge while preserving a match and the agent's conversation,
stop its launcher and run `uv run game.py resume --session CODEX_SESSION_ID`
using the session ID from `codex.log`. This appends to both logs.

For another agent runtime, run `uv run game.py serve --token TOKEN` and use its
four standard MCP tools. State and action templates come directly from the
player-masked backend projection. The bridge requests a full projection when it
receives a delta, avoiding a second reducer. `revision` guards stale submissions;
backend `interactionEpoch` is echoed on actions. The bridge does not implement
strategy, memory, rules lookup, or hypothetical rollouts.

Validation:

```bash
uv run pytest -q
ARGENTUM_LIVE=1 uv run pytest tests/test_game.py::test_live_player_contract -q
ARGENTUM_CODEX=1 uv run pytest tests/test_game.py::test_codex_four_tools -q
```

## Historical gym prototype

The following scripts use separate gym environments; they do not attach to the
human's browser game.

The current verified path is:

1. Argentum `gym-server` produces observations and legal action masks.
2. `mtgbench_harness` renders a Codex-facing state/action/tool surface.
3. Local `codex exec` returns schema-valid JSON.
4. The harness validates the selected `actionId`.
5. Argentum executes the move.
6. The two-agent match runner routes each decision to the agent seated for the current Argentum player id.

## Quick Start

Install Python deps:

```bash
uv sync --dev
uv run pytest -q
```

Clone and run Argentum separately (see [DEPENDENCIES.md](DEPENDENCIES.md) for
the pinned upstream revision and build requirements):

```bash
mkdir -p 05_evidence/repos
git clone https://github.com/wingedsheep/argentum-engine.git 05_evidence/repos/argentum-engine
cd 05_evidence/repos/argentum-engine
git checkout --detach d812e2a418a9fba8f6a9b24c4582d338e0296405
JAVA_HOME=/opt/homebrew/opt/openjdk@21 just gym-server
```

From this repo root, run live smokes:

```bash
uv run python 02_prototypes/scripts/run_argentum_smokes.py --max-steps 64
```

Run a real Codex CLI episode:

```bash
uv run python 02_prototypes/scripts/run_codex_cli_episode.py --steps 8 --include-oracle-context
```

Run a two-agent Argentum match:

```bash
uv run python 02_prototypes/scripts/run_two_agent_match.py --agent-a first-legal --agent-b codex-heuristic --max-steps 128
```

## Dependencies

See [DEPENDENCIES.md](DEPENDENCIES.md).

Short version:

- `uv`
- Python 3.11+
- Java 21 for Argentum
- local `codex` CLI for real Codex episodes
- network access for Scryfall/source probes

Runtime Python code is stdlib-only. `pytest` is the only dev dependency.

## Read First

1. `06_decisions/0003-codex-cli-agent.md` - current Codex player decision.
2. `06_decisions/0004-two-agent-argentum-harness.md` - two-agent match runner decision.
3. `02_prototypes/results/two_agent_match_20260525T2031Z.md` - full heuristic-vs-heuristic game evidence.
4. `02_prototypes/results/codex_cli_episodes_20260525.md` - real Codex run evidence.
5. `06_decisions/0002-uv-harness-shape.md` - uv harness shape.
6. `03_architecture/implementation_detail.md` - proposed MTGBench architecture and first milestone.
7. `01_landscape/open_engines_and_products.md` - engine and product landscape.

## Layout

- `mtgbench_harness/`: reusable Python harness.
- `schemas/`: structured output schema for Codex action choices.
- `tests/`: pure uv/pytest checks.
- `02_prototypes/scripts/`: minimal runnable scripts.
- `02_prototypes/results/`: small evidence snapshots.
- `00_admin/`, `01_landscape/`, `03_architecture/`, `04_datasets/`, `06_decisions/`: research dataroom docs.
- `05_evidence/repos/`: ignored local engine checkouts.

## Minimal Scripts

- `02_prototypes/scripts/run_argentum_smokes.py`
- `02_prototypes/scripts/run_codex_cli_episode.py`
- `02_prototypes/scripts/run_two_agent_match.py`
- `02_prototypes/scripts/probe_mtg_sources.py`

## Evidence Snapshots

- `02_prototypes/results/codex_cli_episodes_20260525.md` - real Codex CLI episodes.
- `02_prototypes/results/two_codex_cli_match_20260525T2114Z.md` - real Codex CLI vs Codex CLI bounded match evidence.
- `02_prototypes/results/two_agent_match_20260525T2031Z.md` - two-agent Argentum match summary, including full terminal heuristic game.
- `02_prototypes/results/two_agent_match_20260525T2030Z.json` - raw mixed-agent route smoke.
- `02_prototypes/results/argentum_smokes_20260525T2030Z.json` - raw 13-smoke live run with two-agent match coverage.
- `02_prototypes/results/argentum_harness_smokes_20260525T0339Z.md` - uv harness and live smoke summary.
- `02_prototypes/results/argentum_smokes_20260525T0339Z.json` - raw 12-smoke live run.
- `02_prototypes/results/source_probe_20260524T230431Z.json` - live API/source probe.
- `02_prototypes/results/magebench_smoke_20260524T2312Z.md` - mage-bench clone/build/run smoke.

## Current Status

Codex can legally play through the harness, including a 16-step episode that played `Mountain` and cast `Raging Goblin`. The two-agent Argentum runner can also complete a heuristic-vs-heuristic game to terminal state. The remaining research problem is action-window compression, hidden-information perspective handling, card/action coverage, and play quality, not basic move legality.

## Older Research Index

1. `03_architecture/implementation_detail.md` - proposed MTGBench architecture and first milestone.
2. `06_decisions/0001-first-engine-spike.md` - current engine decision.
3. `01_landscape/apis_and_data.md` - open card/data/API sources.
4. `01_landscape/open_engines_and_products.md` - engine and product landscape.
5. `01_landscape/game_ai_precedents.md` - LLM/game-agent precedent map.
