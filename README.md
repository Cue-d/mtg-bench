# Magic agent tools

One Python file, four player-scoped tools, and an unmodified Argentum engine.
[`game.py`](game.py) exposes `observe`, `legal_actions`, `act`, and
`resolve_decision` over stdio MCP. Argentum owns rules, state, legal actions,
and hidden-information masking; strategy and memory belong to the agent.
The [protocol skill](.agents/skills/argentum/SKILL.md) explains action parameters
and decision responses, with references to the pinned upstream definitions.

## Setup

Requires `uv`, Python 3.11+, Git, Java 21, `just`, Node.js 22.12+ with npm,
and an authenticated Codex CLI with access to `gpt-6-astra`.
The launcher prefers the CLI bundled in `/Applications/ChatGPT.app`; otherwise
it uses `codex` on PATH. No API key is needed when that CLI is already logged in.

From this repository, install the locked Python dependencies and clone the
engine once:

```bash
uv sync --locked
mkdir -p evidence/repos
git clone https://github.com/wingedsheep/argentum-engine.git evidence/repos/argentum-engine
git -C evidence/repos/argentum-engine checkout --detach d812e2a418a9fba8f6a9b24c4582d338e0296405
npm --prefix evidence/repos/argentum-engine/web-client ci
```

Keep the engine running in one terminal:

```bash
cd evidence/repos/argentum-engine
just server
```

Set `JAVA_HOME` to your Java 21 installation if needed. On Apple Silicon with
Homebrew, use `JAVA_HOME=/opt/homebrew/opt/openjdk@21 just server`.
The game server listens on port 8080. This bridge does not use `gym-server`.

Keep the existing UI running in another terminal:

```bash
npm --prefix evidence/repos/argentum-engine/web-client run dev -- --host 127.0.0.1
```

## Play

From the repository root, choose one command:

```bash
uv run game.py play              # Human Rabbits vs Astra-low Mice
uv run game.py play --self-play  # Independent Astra-low sessions in both seats
```

The decks are Argentum's 60-card Selesnya Rabbits and Boros Mice examples.
For human play, open the printed `humanUrl` and choose your opening hand.
For self-play, watch `http://localhost:5173/?spectate=<sessionId>` using the
printed session ID. Never spectate through a player's token: that replaces
the agent connection.

Each agent has one continuing Codex session and the same four preapproved tools.
Other configured MCP servers are disabled only for that invocation; global
Codex settings are unchanged. The launcher waits for the agents to exit.
Restarting the engine loses the match. Running `play` creates a new match.

To use another runtime, attach its MCP client to:

```bash
uv run game.py serve --token TOKEN
```

`--url ws://localhost:8080/game` selects the backend. The launcher assumes the
browser UI is at `http://localhost:5173`. It has no rules lookup, search,
simulation, or agent-memory tools.

## Logs and reconnecting

Human matches save credentials in `.local/game.json` and process output in
`.local/codex.log`. Self-play saves a separate `.local/<sessionId>/game.json`
and `codex-rabbits.log` / `codex-mice.log` for each match.
All are ignored by Git. Tokens grant control of a seat; keep them private.

Tool I/O appends to `.local/tools.jsonl`, with call IDs, timestamps, player IDs,
revisions, arguments, full masked results, errors, and elapsed time. Optional
`explanation` arguments record brief public move rationales, not private model
reasoning. Logs across seats collectively reveal private hands, so agents must
not read them. A trace is debugging evidence, not a replayable rules engine.

Reopen the saved human URL to reconnect. To restart the agent bridge for that
same human match, stop its launcher and resume its Codex conversation:

```bash
uv run game.py resume --session CODEX_SESSION_ID
```

Use the Codex session ID from `.local/codex.log`, not the game session ID.
This convenience command currently resumes only the saved human match.

## Test

```bash
uv run pytest -q
ARGENTUM_LIVE=1 uv run pytest tests/test_game.py -q
ARGENTUM_CODEX=1 uv run pytest tests/test_game.py::test_codex_four_tools -q
```

The live check needs the engine on port 8080 and tests private-hand masking,
revision checks, playing a land, and a cleanup discard. The Codex check also
needs login/model access and spends model usage to exercise all four tools.
Neither requires the browser UI. A successful short smoke is not a full-game
correctness claim.

## Historical research

[`archive/`](archive/) preserves the source ledger, research, decisions, and
original run evidence. The superseded gym runtime and its tests were removed;
recover them from commit `4ea6e4c` if needed. Historical commands and counts in
the archive describe that older implementation, not the current setup.
