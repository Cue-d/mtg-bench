# Research Status

## Objective

Go deep on open Magic: The Gathering APIs, products, game engines, datasets, LLM/game-agent precedents, and convert the findings into an implementation-ready dataroom.

## Open Requirements

- Identify open and quasi-open MTG data sources.
- Identify open play, simulation, and rules-enforcement engines.
- Test practical implementation paths, not just describe them.
- Research LLM/agent precedents in other games and extract useful design patterns.
- Produce a concrete implementation detail for MTGBench.
- Keep evidence and source links in the dataroom.

## Current State

- Dataroom initialized.
- Live API/source probe written and run.
- Argentum cloned, tested under JDK 21, smoke-tested over HTTP, and exercised through a reusable Python client prototype.
- mage-bench cloned, Python smoke-tested, Maven-built, and run through a local CPU game that reached `GAME_OVER`; clean unattended exit/export still needs investigation.
- Landscape, dataset plan, architecture detail, and first decision record drafted.
- uv project initialized in the dataroom.
- `mtgbench_harness/` now contains an Argentum client, Gym-style adapter, Codex prompt/tool surface, placeholder agents, and live smokes.
- Latest live Argentum harness run passed 12/12 smokes with 64-step first-legal and Codex-heuristic episodes.
- `CodexCliAgent` now calls local `codex exec` with `schemas/codex_action.schema.json`.
- Real Codex episodes passed: 1 step, 16 steps, and 8 steps with Scryfall oracle context.
- The public repo shape is cleaned: large engine repos are ignored/reproducible, scripts are minimal, and dependencies are documented.
- Published public GitHub repo: https://github.com/snbafana/mtgbench-dataroom

## Next Checks

- Compress trivial priority windows so Codex is called only on strategic choices.
- Add card lookup tools backed by a local Scryfall/MTGJSON cache instead of live Scryfall requests.
- Expand task configs beyond the Mountain/Raging Goblin explicit deck smoke.
- Investigate why mage-bench CPU smoke requires manual interrupt after `GAME_OVER`.
