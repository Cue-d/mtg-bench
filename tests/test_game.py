"""Run with ARGENTUM_LIVE=1 against the local game-server."""
import json
import os
from pathlib import Path
import subprocess
import urllib.request

import pytest

from game import Game, codex_command, traced
from types import SimpleNamespace
import threading


def test_trace_preserves_result_and_logs_errors(tmp_path):
    game = SimpleNamespace(changed=threading.Condition(), view={"state": {"turnNumber": 3}},
                           revision=7, player_id="agent")
    path = tmp_path / "tools.jsonl"
    result = {"revision": 8, "state": {"turnNumber": 3}}

    def act(action: dict, revision: int, explanation: str | None = None):
        if revision != 7:
            raise ValueError("stale")
        return result

    tool = traced(game, act, path)
    assert tool({"type": "PlayLand"}, 7, "Develop mana") is result
    with pytest.raises(ValueError, match="stale"):
        tool({"type": "PlayLand"}, 6)
    entries = [json.loads(line) for line in path.read_text().splitlines()]
    assert [e["event"] for e in entries] == ["call", "result", "call", "error"]
    assert entries[0]["arguments"]["explanation"] == "Develop mana"
    assert entries[0]["context"]["turnNumber"] == 3
    assert entries[0]["callId"] == entries[1]["callId"]
    assert entries[1]["result"] == result
    assert entries[3]["error"] == "ValueError: stale"


@pytest.mark.skipif(not os.environ.get("ARGENTUM_LIVE"), reason="requires game-server on 8080")
def test_live_player_contract():
    request = {"mode": "TWO_PLAYER", "phase": "PRECOMBAT_MAIN", "step": "PRECOMBAT_MAIN",
               "activePlayer": 1, "priorityPlayer": 1,
               "player1": {"hand": ["Mountain"] * 9, "library": ["Mountain"] * 20},
               "player2": {"hand": ["Forest", "Giant Growth"], "library": ["Forest"] * 20}}
    with urllib.request.urlopen(urllib.request.Request(
        "http://localhost:8080/api/scenarios", data=json.dumps(request).encode(),
        headers={"Content-Type": "application/json"}
    )) as response:
        scenario = json.load(response)
    first = Game(scenario["player1"]["token"])
    second = Game(scenario["player2"]["token"])
    try:
        view = first.observe()
        assert "Giant Growth" not in json.dumps(view)
        actions = first.legal_actions()
        land = next(item["action"] for item in actions["legalActions"] if item["actionType"] == "PlayLand")
        changed = first.act(land, actions["revision"])
        assert changed["revision"] > actions["revision"]
        with pytest.raises(ValueError, match="Stale"):
            first.act(land, actions["revision"])
        with pytest.raises(ValueError, match="playerId"):
            first.act({"type": "PassPriority", "playerId": second.player_id}, changed["revision"])
        # Eight cards remain; passing to cleanup should demand a real discard choice.
        for _ in range(60):
            for player in (first, second):
                view = player.observe(timeout=1)
                pending = view.get("pendingDecision")
                if pending:
                    assert player is first
                    assert pending["type"] == "SelectCardsDecision"
                    card_ids = pending.get("options") or pending.get("validCards")
                    assert card_ids, pending
                    after = player.resolve_decision({"type": "CardsSelectedResponse",
                        "decisionId": pending["id"], "selectedCards": [card_ids[0]]}, view["revision"])
                    assert not after.get("pendingDecision")
                    return
                passes = [a for a in view.get("legalActions", []) if a["actionType"] == "PassPriority"]
                if passes:
                    player.act(passes[0]["action"], view["revision"])
        pytest.fail("Never reached the discard decision")
    finally:
        first._send({"type": "concede"})
        first.close()
        second.close()


@pytest.mark.skipif(not os.environ.get("ARGENTUM_CODEX"), reason="requires authenticated Codex and game-server")
def test_codex_four_tools():
    request = {"mode": "TWO_PLAYER", "phase": "PRECOMBAT_MAIN", "step": "PRECOMBAT_MAIN",
               "activePlayer": 1, "priorityPlayer": 1,
               "player1": {"hand": ["Mountain"] * 9, "library": ["Mountain"] * 20},
               "player2": {"hand": [], "library": ["Forest"] * 20}}
    with urllib.request.urlopen(urllib.request.Request(
        "http://localhost:8080/api/scenarios", data=json.dumps(request).encode(),
        headers={"Content-Type": "application/json"}
    )) as response:
        scenario = json.load(response)
    opponent = Game(scenario["player2"]["token"])
    root = Path(__file__).resolve().parents[1]
    prompt = (root / ".agents/skills/argentum/SKILL.md").read_text() + "\n" + (
        "Contract smoke: call observe and legal_actions. Play exactly one Mountain through act. "
        "Then pass priority until you reach cleanup and must discard from your eight-card hand. "
        "Use resolve_decision to discard one card. Stop immediately after the decision is resolved "
        "and reply CONTRACT_OK. Use all four argentum tools. Do not use other tools."
    )
    try:
        result = subprocess.run(codex_command(scenario["player1"]["token"], "ws://localhost:8080/game")
                                + [prompt], capture_output=True, text=True, timeout=240, cwd=root)
        output = result.stdout + result.stderr
        assert result.returncode == 0, output[-5000:]
        assert result.stdout.strip() == "CONTRACT_OK", output[-5000:]
        for tool in ("observe", "legal_actions", "act", "resolve_decision"):
            assert f"argentum/{tool}" in output, output[-5000:]
        # Reconnect as the tested seat to verify actual backend changes, not the model's claim.
        player = Game(scenario["player1"]["token"])
        try:
            view = player.observe()
            assert not view.get("pendingDecision")
            seat = next(p for p in view["state"]["players"] if p["playerId"] == player.player_id)
            assert seat["handSize"] == 7
            assert seat["graveyardSize"] == 1
            print("CODEX_CONTRACT_OK", json.dumps({"revision": view["revision"], "state": view.get("state")})[:300])
        finally:
            player._send({"type": "concede"})
            player.close()
    finally:
        opponent.close()
