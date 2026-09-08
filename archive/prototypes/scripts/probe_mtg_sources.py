#!/usr/bin/env python3
"""Probe live MTG data/API/engine sources and write a reproducible JSON snapshot."""

from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "results"
USER_AGENT = "mtgbench-dataroom-probe/0.1 (+local research)"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def fetch_json(url: str, *, timeout: int = 20) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read()
            return {
                "ok": True,
                "status": resp.status,
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "url": url,
                "bytes": len(body),
                "json": json.loads(body.decode("utf-8")),
            }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "ok": False,
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
            "url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def fetch_head(url: str, *, timeout: int = 20) -> dict[str, Any]:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return {
                "ok": True,
                "status": resp.status,
                "elapsed_ms": round((time.perf_counter() - started) * 1000),
                "url": url,
                "content_type": resp.headers.get("content-type"),
                "content_length": resp.headers.get("content-length"),
            }
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        return {
            "ok": False,
            "elapsed_ms": round((time.perf_counter() - started) * 1000),
            "url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def scryfall_card(name: str) -> dict[str, Any]:
    url = "https://api.scryfall.com/cards/named?" + urllib.parse.urlencode({"exact": name})
    result = fetch_json(url)
    if not result["ok"]:
        return result
    data = result["json"]
    result["summary"] = {
        "name": data.get("name"),
        "oracle_id": data.get("oracle_id"),
        "type_line": data.get("type_line"),
        "legalities": data.get("legalities", {}),
        "edhrec_rank": data.get("edhrec_rank"),
    }
    result.pop("json", None)
    return result


def summarize_bulk(result: dict[str, Any]) -> dict[str, Any]:
    if not result["ok"]:
        return result
    rows = result["json"].get("data", [])
    result["summary"] = [
        {
            "type": row.get("type"),
            "updated_at": row.get("updated_at"),
            "size": row.get("size"),
            "download_uri": row.get("download_uri"),
        }
        for row in rows
        if row.get("type") in {"oracle_cards", "default_cards", "all_cards", "unique_artwork"}
    ]
    result.pop("json", None)
    return result


def summarize_set_list(result: dict[str, Any]) -> dict[str, Any]:
    if not result["ok"]:
        return result
    data = result["json"].get("data", [])
    result["summary"] = {
        "meta": result["json"].get("meta"),
        "set_count": len(data) if isinstance(data, list) else None,
        "latest_sets": data[:5] if isinstance(data, list) else None,
    }
    result.pop("json", None)
    return result


def summarize_spellbook_variants(result: dict[str, Any]) -> dict[str, Any]:
    if not result["ok"]:
        return result
    data = result["json"]
    rows = data.get("results", data if isinstance(data, list) else [])
    result["summary"] = {
        "count": data.get("count") if isinstance(data, dict) else None,
        "first_results": [
            {
                "id": row.get("id"),
                "status": row.get("status"),
                "uses": [item.get("card", {}).get("name") for item in row.get("uses", [])],
                "produces": [item.get("feature", {}).get("name") for item in row.get("produces", [])],
            }
            for row in rows[:3]
            if isinstance(row, dict)
        ],
    }
    result.pop("json", None)
    return result


def summarize_github_repo(repo: str) -> dict[str, Any]:
    result = fetch_json(f"https://api.github.com/repos/{repo}")
    if not result["ok"]:
        result["repo"] = repo
        return result
    data = result["json"]
    result["repo"] = repo
    result["summary"] = {
        "full_name": data.get("full_name"),
        "stars": data.get("stargazers_count"),
        "forks": data.get("forks_count"),
        "license": (data.get("license") or {}).get("spdx_id"),
        "pushed_at": data.get("pushed_at"),
        "default_branch": data.get("default_branch"),
        "language": data.get("language"),
        "open_issues": data.get("open_issues_count"),
    }
    result.pop("json", None)
    return result


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot = {
        "fetched_at": utc_now(),
        "sources": {
            "scryfall_bulk": summarize_bulk(fetch_json("https://api.scryfall.com/bulk-data")),
            "scryfall_named_cards": {
                name: scryfall_card(name)
                for name in ["Sol Ring", "Tivit, Seller of Secrets", "Sythis, Harvest's Hand"]
            },
            "mtgjson_meta": fetch_json("https://mtgjson.com/api/v5/Meta.json"),
            "mtgjson_set_list": summarize_set_list(fetch_json("https://mtgjson.com/api/v5/SetList.json")),
            "commander_spellbook_root": fetch_json("https://backend.commanderspellbook.com/"),
            "commander_spellbook_schema_head": fetch_head("https://backend.commanderspellbook.com/schema/"),
            "commander_spellbook_variants": summarize_spellbook_variants(
                fetch_json("https://backend.commanderspellbook.com/variants/?limit=3")
            ),
            "seventeen_lands_public_datasets_head": fetch_head("https://www.17lands.com/public_datasets"),
            "seventeen_lands_usage_guidelines_head": fetch_head("https://www.17lands.com/usage_guidelines"),
            "github_repos": {
                repo: summarize_github_repo(repo)
                for repo in [
                    "Card-Forge/forge",
                    "magefree/mage",
                    "GregorStocks/mage-bench",
                    "Cockatrice/Cockatrice",
                    "Senryoku/Draftmancer",
                    "dekkerglen/CubeCobra",
                    "wingedsheep/argentum-engine",
                    "magarena/magarena",
                    "WagicProject/wagic",
                    "mtgjson/mtgjson",
                    "SpaceCowMedia/commander-spellbook-backend",
                ]
            },
        },
    }
    out_path = OUT_DIR / f"source_probe_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(snapshot, indent=2, sort_keys=True) + "\n")
    print(out_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
