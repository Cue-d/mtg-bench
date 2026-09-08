---
name: argentum
description: Play a live Argentum Magic game through its four player-scoped MCP tools.
---

# Argentum player protocol

For nontrivial moves, include an optional `explanation` in `act` or
`resolve_decision`: one short public sentence describing the move's purpose or
tradeoff. This is a spectator-facing decision summary, not private internal
reasoning. It is logged but never sent to the game engine. Forced passes do not
need explanations. The trace is for debugging and may reveal your visible hand.

You control one player in an existing game. The engine enforces rules and supplies
your masked view. Memory and strategy are yours; the tools do neither.

- `observe(wait_for_action=false, timeout=30)` returns the current complete masked
  server state, legal actions, pending decision, and a local `revision`. Set
  `wait_for_action=true` to wait for your next choice (up to 60 seconds). A timeout
  while the opponent thinks is normal; wait again. No polling shell commands.
- `legal_actions()` returns the full backend action templates and their constraints.
- `act(action, revision)` submits a completed template from the latest observation.
  This is the game-server protocol: there are no gym action IDs. Preserve `type`,
  `playerId`, card/ability IDs, and other template fields; supply the choices needed.
- `resolve_decision(response, revision)` answers `pendingDecision`, or an opening
  hand decision. Mutations return the next state; use its new revision.

Read the returned state rather than assuming a successful call resolved a spell.
Casting usually puts a spell on the stack. Passing yields priority; responses and
resolution follow the engine. Do not choose unaffordable actions. Use the target,
attacker, blocker, mode, X, and additional-cost constraints supplied with each action.
Never reuse a revision after a state change. An error does not mean success; inspect
again. A timeout after submission is uncertain: observe before retrying.

## Common action shapes

Copy the backend's `action` object; these are examples of choices added to it:

```json
{"type":"PassPriority","playerId":"YOUR_ID"}
{"type":"PlayLand","playerId":"YOUR_ID","cardId":"LAND_ID"}
{"type":"CastSpell","playerId":"YOUR_ID","cardId":"SPELL_ID","targets":[{"type":"Player","playerId":"TARGET_ID"}]}
{"type":"DeclareAttackers","playerId":"YOUR_ID","attackers":{"CREATURE_ID":"DEFENDER_ID"}}
{"type":"DeclareBlockers","playerId":"YOUR_ID","blockers":{"BLOCKER_ID":["ATTACKER_ID"]}}
```

Cast/ability `targets` are typed: `Player` uses `playerId`; `Permanent` uses
`entityId`; `Spell` uses `spellEntityId`; `Card` uses `cardId`, `ownerId`, and `zone`.
Use `xValue` for X. Mana auto-payment is the default; manual tapping is not normally
needed before casting. Empty attacker/blocker maps declare none, so choose deliberately.

## Decisions

Every engine response includes `decisionId` equal to `pendingDecision.id`, plus its
`type` discriminator and choice fields. Common responses:

| Response type | Choice fields |
|---|---|
| CardsSelectedResponse | selectedCards: array of card IDs |
| TargetsResponse | selectedTargets: requirement-index to array of IDs |
| YesNoResponse | choice: boolean |
| BatchYesNoResponse | choice: boolean, applyToAll: boolean |
| ModesChosenResponse | selectedModes: array of mode indices |
| ColorChosenResponse | color: color enum |
| NumberChosenResponse | number: integer |
| DistributionResponse | distribution: ID to integer |
| OrderedResponse | orderedObjects: ordered array of IDs |
| PilesSplitResponse | piles: array of arrays of IDs |
| OptionChosenResponse | optionIndex: integer |
| ReplacementChosenResponse | fromIndex: integer, toIndex: integer |

Opening hands use the same tool with protocol messages instead:
`{"type":"keepHand"}`, `{"type":"mulligan"}`, or
`{"type":"chooseBottomCards","cardIds":[...]}`. Follow `openingDecision`.

## Complete enum and parameter references

The exact, versioned source contracts live in the bundled upstream checkout
`05_evidence/repos/argentum-engine/`. Read these on demand for uncommon parameters;
they are the canonical definitions, not a second handwritten schema:

- `web-client/src/types/actions.ts`: action union, costs, targets, decision responses.
- `web-client/src/types/enums.ts`: phase, step, zone, color and other game enums.
- `rules-engine/src/main/kotlin/com/wingedsheep/engine/core/GameAction.kt`: full backend action fields.
- `rules-engine/src/main/kotlin/com/wingedsheep/engine/core/PendingDecision.kt`: pending choices and every response subtype.
- `rules-engine/src/main/kotlin/com/wingedsheep/engine/view/LegalActionPresentation.kt`: legal-action constraints.

Read only your player-scoped tools for live game information. Do not inspect
opponent sessions, reconnect tokens, logs, or server internals to discover hidden cards.
