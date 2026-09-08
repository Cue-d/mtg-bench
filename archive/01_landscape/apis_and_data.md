# APIs And Data

## What Is Open Enough To Build On

| Source | Use | Access | Fit |
|---|---|---:|---|
| Scryfall | Card search, oracle text, rulings, images, identifiers, legalities, bulk card snapshots | No auth | Primary card-knowledge source |
| MTGJSON | Normalized bulk files for sets, decks, identifiers, prices, products | No auth | Primary warehouse source |
| Commander Spellbook | Structured Commander combo database with cards/features/variants/OpenAPI | No auth | Best deterministic combo/task source |
| 17Lands public datasets | Draft, game, and replay datasets released by set | Public dumps | Best supervised limited/draft source |
| magicthegathering.io | Older REST card API | No auth | Legacy/reference only |
| CubeCobra | Cube lists and cube-product workflows | Open-source app, exports | Product/dataset lead, not first API dependency |
| Draftmancer | Draft/sealed simulation and bot UX | Open-source app | Product/draft-flow lead |

## Live Probe Notes

The live probe is saved at `02_prototypes/results/source_probe_20260524T230431Z.json`.

Scryfall bulk data returned current download files on 2026-05-24:

| Bulk type | Updated | Size |
|---|---:|---:|
| `oracle_cards` | `2026-05-24T09:03:15.152+00:00` | 173,117,830 bytes |
| `default_cards` | `2026-05-24T21:42:01.852+00:00` | 538,993,060 bytes |
| `all_cards` | `2026-05-24T09:25:14.522+00:00` | 2,509,975,991 bytes |
| `unique_artwork` | `2026-05-24T21:12:18.828+00:00` | 252,993,581 bytes |

MTGJSON `Meta.json` returned `5.3.0+20260524`, so its daily snapshot was current for the run.

Commander Spellbook returned working combo variants, including:

| Combo | Produced |
|---|---|
| Hullbreaker Horror + Sol Ring | Infinite colorless mana, infinite storm count |
| Demonic Consultation + Thassa's Oracle | Exile library, win the game |
| Exquisite Blood + Sanguine Bond | Infinite lifegain/lifeloss loop |

## Practical Data Stack

Use Scryfall and MTGJSON together, not one or the other.

Scryfall should be the user-facing card layer because its query syntax, image URIs, oracle grouping, rulings, and search behavior are excellent. MTGJSON should be the warehouse layer because it normalizes printings, sets, products, decks, identifiers, and price files into predictable bulk artifacts.

Suggested local tables:

| Table | Source | Key |
|---|---|---|
| `cards_oracle` | Scryfall `oracle_cards` | `oracle_id` |
| `cards_printings` | Scryfall `default_cards` + MTGJSON printings | `scryfall_id`, MTGJSON UUID |
| `sets` | Scryfall sets + MTGJSON SetList | set code |
| `rulings` | Scryfall rulings endpoint | `oracle_id`, source date |
| `combos` | Commander Spellbook variants | Spellbook variant id |
| `limited_events` | 17Lands public dumps | set, event id, draft id |
| `decklists` | MTGJSON decks, user imports, cube exports | normalized deck id |

## Licensing And Usage Constraints

Scryfall and MTGJSON are suitable for a local research/benchmark cache. Still treat card text/images as Wizards IP and avoid redistributing raw card/image bundles as a product asset.

For 17Lands, prefer the public datasets page and cite 17Lands clearly. The site's usage guidance explicitly distinguishes public dumps from curated site data and discourages automated scraping of the live UI/API. That makes public dumps the right ingestion path for repeatable training.

Commander Spellbook's backend is open source and exposes an OpenAPI schema, making it the cleanest source for structured combo reasoning tasks.

## Gaps

There is no public, complete, official Wizards gameplay log corpus. Arena logs, MTGO data, and SpellTable/video games are possible but operationally messy.

There is no universal open "legal action for arbitrary Magic state" API. That has to come from an engine adapter.

17Lands is heavily limited-format biased and tracker-user biased. Treat it as expert-ish draft/game behavior, not whole-Magic truth.
