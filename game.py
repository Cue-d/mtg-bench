"""Four agent-neutral tools for an Argentum game-server player connection.

Run `uv run game.py serve --token TOKEN` as a stdio MCP server.
Argentum owns the game; this client only caches its masked full-state messages.
"""
from __future__ import annotations

import argparse
import copy
from datetime import datetime, timezone
from functools import wraps
import inspect
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
import tomllib
import urllib.request
import uuid
from typing import Any

import websocket
from mcp.server.fastmcp import FastMCP


class Game:
    def __init__(self, token: str, url: str = "ws://localhost:8080/game", name: str = "Agent"):
        self.socket = websocket.create_connection(url, timeout=20)
        self.changed = threading.Condition()
        self.operation = threading.Lock()
        self.view: dict[str, Any] = {}
        self.player_id: str | None = None
        self.error: str | None = None
        self.failure: str | None = None
        self.revision = 0
        self.dirty = False
        self.closed = False
        self.socket.send(json.dumps({"type": "connect", "playerName": name, "token": token}))
        self.reader = threading.Thread(target=self._receive, daemon=True)
        self.reader.start()

    def _send(self, message: dict) -> None:
        self.socket.send(json.dumps(message))

    def _receive(self) -> None:
        try:
            while not self.closed:
                try:
                    message = json.loads(self.socket.recv())
                except websocket.WebSocketTimeoutException:
                    self._send({"type": "ping"})
                    continue
                kind = message["type"]
                with self.changed:
                    if kind in ("connected", "reconnected"):
                        self.player_id = message["playerId"]
                    elif kind == "stateDeltaUpdate":
                        # Ask the existing backend for the full projection; don't implement
                        # another delta reducer or derive rules state here.
                        if not self.dirty:
                            self.dirty = True
                            self._send({"type": "requestResync"})
                    elif kind == "stateUpdate":
                        changed = any(self.view.get(key) != message.get(key) for key in (
                            "state", "legalActions", "pendingDecision", "interactionEpoch"))
                        self.view = message
                        self.dirty = False
                        if changed:
                            self.revision += 1
                    elif kind in ("mulliganDecision", "chooseBottomCards"):
                        self.view = {"openingDecision": message, "legalActions": []}
                        self.revision += 1
                    elif kind in ("waitingForOpponentMulligan", "mulliganComplete"):
                        self.view = {"status": kind, "legalActions": []}
                        self.revision += 1
                    elif kind == "gameOver":
                        self.view["gameOver"] = message
                        self.revision += 1
                    elif kind == "error":
                        self.error = f"{message.get('code')}: {message.get('message')}"
                        self.revision += 1
                    elif kind == "sessionReplaced":
                        raise RuntimeError("This player's connection was replaced")
                    self.changed.notify_all()
        except Exception as exc:
            with self.changed:
                if not self.closed:
                    self.failure = str(exc)
                self.changed.notify_all()

    def _check(self) -> None:
        if self.failure and not self.view.get("gameOver") and not self.view.get("state", {}).get("isGameOver"):
            raise RuntimeError(f"Game connection failed: {self.failure}")

    def observe(self, wait_for_action: bool = False, timeout: float = 30) -> dict:
        """Read the server's player-masked state. Optionally wait for our next choice."""
        deadline = time.monotonic() + min(max(timeout, 0), 60)
        with self.changed:
            while True:
                self._check()
                actionable = bool(self.view.get("legalActions") or self.view.get("pendingDecision")
                                  or self.view.get("openingDecision") or self.view.get("gameOver")
                                  or self.view.get("state", {}).get("isGameOver"))
                if self.view and not self.dirty and (not wait_for_action or actionable):
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                self.changed.wait(min(remaining, 20))
                self._send({"type": "ping"})
            return {"playerId": self.player_id, "revision": self.revision,
                    "waiting": not actionable, **copy.deepcopy(self.view)}

    def legal_actions(self) -> dict:
        """Return unmodified backend action templates and all choice constraints."""
        view = self.observe()
        return {key: view.get(key) for key in (
            "playerId", "revision", "legalActions", "pendingDecision", "openingDecision")}

    def _submit(self, message: dict, revision: int) -> dict:
        with self.operation:
            with self.changed:
                self._check()
                if self.dirty or revision != self.revision:
                    raise ValueError("Stale observation: call observe or legal_actions again")
                self.error = None
                self._send(message)
                if not self.changed.wait_for(
                    lambda: self.failure or self.error or self.revision > revision, timeout=20
                ):
                    raise TimeoutError("No confirmation; observe before retrying this action")
                self._check()
                if self.error:
                    raise ValueError(self.error)
            return self.observe()

    def act(self, action: dict, revision: int, explanation: str | None = None) -> dict:
        """Submit a completed GameAction. Optional explanation is a brief public rationale, logged only."""
        if action.get("playerId") != self.player_id:
            raise ValueError("action.playerId must identify this connection's player")
        if action.get("type") == "SubmitDecision":
            raise ValueError("Use resolve_decision for SubmitDecision")
        return self._submit({"type": "submitAction", "action": action,
                             "messageId": str(uuid.uuid4()),
                             "interactionEpoch": self.view.get("interactionEpoch")}, revision)

    def resolve_decision(self, response: dict, revision: int, explanation: str | None = None) -> dict:
        """Answer a pending choice. Optional explanation is a brief public rationale, logged only."""
        opening = self.view.get("openingDecision")
        if opening:
            allowed = {"keepHand", "mulligan"} if opening["type"] == "mulliganDecision" else {"chooseBottomCards"}
            if response.get("type") not in allowed:
                raise ValueError(f"Opening decision expects one of {sorted(allowed)}")
            message = response
        else:
            pending = self.view.get("pendingDecision")
            if not pending or response.get("decisionId") != pending.get("id"):
                raise ValueError("response.decisionId must match pendingDecision.id")
            message = {"type": "submitAction", "messageId": str(uuid.uuid4()),
                       "interactionEpoch": self.view.get("interactionEpoch"),
                       "action": {"type": "SubmitDecision", "playerId": self.player_id, "response": response}}
        return self._submit(message, revision)

    def close(self) -> None:
        self.closed = True
        self.socket.close()


def traced(game: Game, method, path: Path):
    """Append explicit tool I/O, never model internals or connection credentials."""
    signature = inspect.signature(method)

    def write(entry):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry, ensure_ascii=False) + "\n")

    @wraps(method)
    def call(*args, **kwargs):
        arguments = signature.bind(*args, **kwargs)
        arguments.apply_defaults()
        call_id = str(uuid.uuid4())
        started = time.monotonic()
        with game.changed:
            view = copy.deepcopy(game.view)
            revision = game.revision
        state = view.get("state", {})
        context = {key: state.get(key) for key in (
            "turnNumber", "currentPhase", "currentStep", "activePlayerId", "priorityPlayerId", "players")}
        context.update(playerId=game.player_id, revision=revision,
                       pendingDecision=view.get("pendingDecision"), openingDecision=view.get("openingDecision"))
        action = arguments.arguments.get("action", {})
        if action:
            context["offeredActions"] = [item for item in view.get("legalActions", [])
                if item.get("action", {}).get("type") == action.get("type")
                and item.get("action", {}).get("cardId") == action.get("cardId")]
        write({"time": datetime.now(timezone.utc).isoformat(), "callId": call_id,
               "event": "call", "tool": method.__name__, "arguments": arguments.arguments,
               "context": context})
        try:
            result = method(*args, **kwargs)
        except Exception as exc:
            write({"time": datetime.now(timezone.utc).isoformat(), "callId": call_id,
                   "event": "error", "tool": method.__name__,
                   "elapsedMs": round((time.monotonic() - started) * 1000),
                   "error": f"{type(exc).__name__}: {exc}"})
            raise
        write({"time": datetime.now(timezone.utc).isoformat(), "callId": call_id,
               "event": "result", "tool": method.__name__,
               "elapsedMs": round((time.monotonic() - started) * 1000), "result": result})
        return result
    return call


def serve(token: str, url: str) -> None:
    game = Game(token, url)
    server = FastMCP("argentum", instructions=(
        "Play through the four tools. Copy action templates from legal_actions and complete their "
        "choices. Use the latest revision. The backend validates all rules. Observe includes only "
        "your player's permitted information. Use observe(wait_for_action=True) while the opponent acts."
    ))
    trace = Path(__file__).resolve().parent / ".local" / "tools.jsonl"
    for method in (game.observe, game.legal_actions, game.act, game.resolve_decision):
        server.tool()(traced(game, method, trace))
    try:
        server.run(transport="stdio")
    finally:
        game.close()


def codex_command(token: str, url: str) -> list[str]:
    """Connect Codex to these same functions through standard stdio MCP."""
    bundled = Path("/Applications/ChatGPT.app/Contents/Resources/codex")
    command = [str(bundled) if bundled.exists() else "codex", "exec",
               "--skip-git-repo-check", "--sandbox", "read-only",
               "--model", "gpt-6-astra", "-c", 'model_reasoning_effort="low"']
    config_path = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex"))) / "config.toml"
    if config_path.exists():
        config = tomllib.loads(config_path.read_text())
        for name in config.get("mcp_servers", {}):
            command += ["-c", f'mcp_servers.{name}.enabled=false']
    command += ["-c", f'mcp_servers.argentum.command={json.dumps(sys.executable)}',
                "-c", "mcp_servers.argentum.args=" + json.dumps(
                    [str(Path(__file__).resolve()), "serve", "--token", token, "--url", url]),
                "-c", "mcp_servers.argentum.enabled=true",
                "-c", 'mcp_servers.argentum.default_tools_approval_mode="approve"',
                "-c", "mcp_servers.argentum.tool_timeout_sec=90"]
    return command + ["--"]


def play(url: str, self_play: bool = False) -> None:
    base = url.replace("ws://", "http://").replace("wss://", "https://").removesuffix("/game")
    with urllib.request.urlopen(base + "/api/decks/examples") as response:
        decks = {deck["id"]: deck for deck in json.load(response)}
    human_deck, agent_deck = decks["selesnya_rabbits"], decks["boros_mice"]
    sockets = []

    def receive(sock, expected):
        while True:
            message = json.loads(sock.recv())
            if message["type"] == "error":
                raise RuntimeError(message)
            if message["type"] == expected:
                return message

    try:
        for name in ("Astra Rabbits · low" if self_play else "You", "Astra Mice · low"):
            sock = websocket.create_connection(url, timeout=30)
            sockets.append(sock)
            sock.send(json.dumps({"type": "connect", "playerName": name}))
        human = receive(sockets[0], "connected")
        agent = receive(sockets[1], "connected")
        sockets[0].send(json.dumps({"type": "createGame", "deckList": human_deck["cards"]}))
        created = receive(sockets[0], "gameCreated")
        sockets[1].send(json.dumps({"type": "joinGame", "sessionId": created["sessionId"],
                                   "deckList": agent_deck["cards"]}))
        receive(sockets[1], "gameStarted")
        local = Path(__file__).resolve().parent / ".local"
        local.mkdir(exist_ok=True)
        record = {"sessionId": created["sessionId"], "humanToken": human["token"],
                  "agentToken": agent["token"], "humanDeck": human_deck, "agentDeck": agent_deck,
                  "humanUrl": "http://localhost:5173/?token=" + human["token"]}
        if self_play:
            local = local / created["sessionId"]
            local.mkdir()
        record_path = local / "game.json"
        record_path.write_text(json.dumps(record, indent=2))
        record_path.chmod(0o600)
        print(json.dumps({"humanUrl": None if self_play else record["humanUrl"], "sessionId": record["sessionId"],
                          "humanDeck": human_deck["name"], "agentDeck": agent_deck["name"]}), flush=True)
    finally:
        for sock in sockets:
            sock.close()
    skill = (Path(__file__).resolve().parent / ".agents/skills/argentum/SKILL.md").read_text()
    prompt = skill + "\nPlay this complete game against your opponent using the argentum MCP tools. " \
        "Choose your own actions and strategy. Include brief public explanations for nontrivial moves. " \
        "Keep playing until gameOver. While the opponent acts, " \
        "use observe(wait_for_action=true, timeout=60); waiting is normal, not completion. " \
        "Do not inspect .local, logs, any opponent token or unmasked backend state. " \
        "Do not use other apps. Only use shell to read the documented protocol reference if needed."
    seats = [("mice", agent)]
    if self_play:
        seats.insert(0, ("rabbits", human))
    processes = []
    try:
        for name, seat in seats:
            with (local / (f"codex-{name}.log" if self_play else "codex.log")).open("w") as log:
                processes.append(subprocess.Popen(codex_command(seat["token"], url) + [prompt],
                    cwd=Path(__file__).resolve().parent, stdout=log, stderr=subprocess.STDOUT))
        codes = [process.wait() for process in processes]
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait()
    raise SystemExit(next((code for code in codes if code), 0))


def resume(url: str, session: str) -> None:
    """Reconnect the existing game and Codex conversation after a bridge update."""
    root = Path(__file__).resolve().parent
    record = json.loads((root / ".local/game.json").read_text())
    prompt = ((root / ".agents/skills/argentum/SKILL.md").read_text()
              + "\nResume this same game. Call observe to get a fresh revision after reconnecting. "
              "Continue playing until gameOver; wait with observe(wait_for_action=true, timeout=60) "
              "while the human acts. Include brief public explanations for nontrivial moves.")
    command = codex_command(record["agentToken"], url)[:-1] + ["resume", session, "--", prompt]
    with (root / ".local/codex.log").open("a") as log:
        result = subprocess.run(command, cwd=root, stdout=log, stderr=subprocess.STDOUT)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["serve", "play", "resume"])
    parser.add_argument("--session")
    parser.add_argument("--token")
    parser.add_argument("--self-play", action="store_true", help="Run Astra low in both seats")
    parser.add_argument("--url", default="ws://localhost:8080/game")
    args = parser.parse_args()
    if args.command == "play":
        play(args.url, args.self_play)
    elif args.command == "resume":
        if not args.session:
            parser.error("resume requires --session CODEX_SESSION_ID")
        resume(args.url, args.session)
    elif args.token:
        serve(args.token, args.url)
    else:
        parser.error("serve requires --token")
