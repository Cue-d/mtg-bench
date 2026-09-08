# Game AI Precedents

## Direct Magic Precedents

MTG-Causal-RL is the closest academic benchmark. Its arXiv abstract describes a Gymnasium benchmark with a 3,077-dimensional partial observation, a 478-action masked action space, five competitive Standard archetypes, three reward schemes, and causal variables/SCM traces. This is immediately relevant for the benchmark shape even if we do not adopt its environment wholesale.

mage-bench is the closest live LLM product. It uses XMage as the rules engine, exposes MCP tools to LLM pilots, tracks game results/Elo/cost/tool failures/latency, records games, exports structured logs, and runs post-game blunder analysis.

Argentum is the closest local implementation fit for agent training. It already has gym/gym-server/gym-trainer modules, fork/snapshot/restore, hidden information masking, MCTS/self-play, OpenAPI, and a tested HTTP adapter.

UrzaGPT is a directly relevant draft-LLM precedent: LoRA fine-tuning of an open-weight LLM on annotated MTG draft logs for real-time card selection. It reinforces that draft should be a first-class benchmark tier, not an afterthought.

ManaBench is a directly relevant deckbuilding benchmark: given a 59-card tournament deck and six candidate cards, pick the real 60th card. This is a useful cheap tier because it tests strategic coherence without requiring an engine.

## Cross-Game Benchmarks

| Project | Lesson For MTGBench |
|---|---|
| BALROG | Use long-horizon game tasks because current LLM/VLM agents can show partial progress while still failing hard on planning, exploration, and state tracking. |
| GameWorld | Score from serialized game state, not screenshots or LLM judges. MTG should compute success/progress from engine state and logs. |
| VideoGameBench | Latency matters. For LLMs, support both real-time and paused/turn-based modes, and report them separately. |
| NetPlay / NetHack LLM work | Text/state agents need strong memory, inventory/state abstraction, and recovery from invalid actions. |
| Voyager / MineDojo-style Minecraft agents | Tool-augmented agents can accumulate skills, but Magic needs a legal-action mask so the tool surface stays grounded. |
| gym-locm / Legends of Code and Magic | CCG benchmarks should expose draft/deckbuilding and battle phases separately, with simple Gymnasium-compatible APIs. |

## Classic Strategic AI Precedents

| System | Why It Matters |
|---|---|
| AlphaZero/MuZero | Self-play + policy/value + search is the right north star for deterministic perfect-information pieces, but MTG needs hidden-information beliefs and huge action masking. |
| Libratus/Pluribus poker | Imperfect-information abstraction and real-time search are relevant to unknown hands/libraries and bluffing. |
| DeepNash Stratego | Imperfect-information game-theoretic self-play is closer to Magic than chess/go. |
| CICERO Diplomacy | Language plus strategic planning matters if Commander politics/chat becomes part of the benchmark. |
| OpenAI Five / AlphaStar | Large action spaces require strong action abstraction, curriculum, self-play infrastructure, and deterministic replay/evaluation. |

## Design Lessons

MTGBench should not be only "win a whole match." Whole games are expensive, high variance, and hard to debug. The benchmark should be tiered:

1. Card lookup and rules QA.
2. Legal-action selection from compact states.
3. Rules micro-puzzles with exact engine outcomes.
4. Draft prediction from 17Lands-like data.
5. Deck completion in the ManaBench style.
6. Combo-line execution from Commander Spellbook.
7. Short-horizon game-state value decisions.
8. Full self-play and model-vs-model ladders.

Every tier needs a ground-truth source: card DB, engine state, human draft logs, combo database, rollout search, or replayed game outcomes.
