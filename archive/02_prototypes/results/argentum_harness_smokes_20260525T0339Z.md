# Argentum Harness Smokes

Date: 2026-05-25T03:39Z

## Commands

Server:

```bash
JAVA_HOME=/opt/homebrew/opt/openjdk@21 ./gradlew :gym-server:bootRun --no-daemon
```

Harness tests:

```bash
uv run pytest -q
```

Live smokes:

```bash
uv run python 02_prototypes/scripts/run_argentum_smokes.py --max-steps 64 --output 02_prototypes/results/argentum_smokes_20260525T0339Z.json
```

## Results

| Check | Result |
|---|---|
| Pure harness tests | `5 passed in 0.03s` |
| Live smoke count | `12 passed, 0 failed` |
| Max agent steps | `64` |
| Engine schema | `argentum-gym-contract@v1.1-oracle-text` |
| First-legal loop | 64 validated steps, reached turn 3 draw |
| Codex-heuristic loop | 64 validated steps, selected action IDs `[0, 1, 2]` across the run |
| Local illegal action validation | Rejected `999999` before server step |
| Server illegal action validation | Server returned HTTP `400` |
| Snapshot/restore | Restored digest matched starting digest |
| Fork | Source digest stayed unchanged while fork diverged |
| Batch step | Two envs stepped in one request |
| Hidden-info toggle | Revealed observation was larger than hidden observation |
| Codex prompt/tool surface | Prompt included legal actions and `choose_action`/`simulate_action` tools |

## Artifacts

- Raw JSON: `02_prototypes/results/argentum_smokes_20260525T0339Z.json`
- Harness package: `mtgbench_harness/`
- Entrypoint: `02_prototypes/scripts/run_argentum_smokes.py`

## Interpretation

The dataroom now has a uv-backed harness that can:

1. Start from an Argentum observation.
2. Render a Codex-facing state/action/tool surface.
3. Validate proposed action IDs against the current legal-action mask.
4. Step the real rules engine.
5. Exercise fork/snapshot/restore, batch stepping, and hidden-information modes.

This is not a strong Magic-playing agent yet. It is the minimal verified loop needed before swapping the deterministic heuristic for a real Codex/LLM tool caller.
