# Argentum HTTP Smoke

Repository: `05_evidence/repos/argentum-engine`

## Environment

| Tool | Result |
|---|---|
| Java 25 | Failed Gradle/Kotlin startup with `IllegalArgumentException: 25.0.2` |
| Java 21 | Passed focused gym/gym-server/gym-trainer tests |
| Command | `JAVA_HOME=/opt/homebrew/opt/openjdk@21 ./gradlew :gym:test :gym-server:test :gym-trainer:test --no-daemon` |

## Test Result

```text
BUILD SUCCESSFUL in 1m 52s
32 actionable tasks: 32 executed
```

## Live Server Result

Started with:

```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21 ./gradlew :gym-server:bootRun --no-daemon
```

Health:

```json
{"status":"ok"}
```

Schema hash:

```json
{"schemaHash":"argentum-gym-contract@v1.1-oracle-text"}
```

Create env payload used two explicit decks:

```json
{
  "players": [
    {"name": "Alice", "deck": {"type": "Explicit", "cards": {"Mountain": 17, "Raging Goblin": 3}}},
    {"name": "Bob", "deck": {"type": "Explicit", "cards": {"Mountain": 17, "Raging Goblin": 3}}}
  ],
  "skipMulligans": true,
  "startingPlayerIndex": 0
}
```

Create returned an env id, turn 1, beginning/untap, and one legal action:

```json
{
  "actionId": 0,
  "kind": "PassPriority",
  "description": "Pass priority",
  "affordable": true
}
```

Stepping action `0` changed the state digest from:

```text
7039998b0668c76c939aa1567056c636e89a407d3f04c42f9680fc2dd71f7e4f
```

to:

```text
d18e65ead8545366e472ec5e748f4a907fc90697cebce25468a88af6c6187f31
```

Dispose returned `204`.

## Interpretation

Argentum is testable today as a local benchmark engine adapter. The first reusable Python HTTP client has also been added at `02_prototypes/scripts/argentum_http_client.py` and run successfully, writing `02_prototypes/results/argentum_client_run_20260524T2316Z.json`.

The right next prototype is a Gymnasium-compatible wrapper over this client, with one explicit-deck task and one sealed-deck task.
