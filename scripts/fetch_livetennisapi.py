#!/usr/bin/env python3
"""
Optional source: point-by-point match tape from the Live Tennis API.

This is an ADDITIVE, OPT-IN source. It is not part of the default pipeline and
nothing else in this repo depends on it. Without a `LIVETENNISAPI_KEY` in the
environment the script prints a notice and exits 0 without writing anything, so
the repo behaves exactly as it did before.

WHY IT IS HERE
--------------
The TML/Sackmann layer this repo is built on is MATCH-level: one row per match
with a parsed final score. Several aggregations here (NBI in particular) infer
"drama" from that final score, because the final score is all there is.

This source adds a different grain: the point-by-point tape of a match — every
recorded score state, who was serving, whether the game was a tiebreak, and the
provider's per-point win-probability. That is the raw material for in-match
volatility work (how a match actually swung) rather than end-state inference.

Coverage: January 2023 onward. Everything older stays TML-only.

DELIBERATELY NOT JOINED TO TML
------------------------------
The output lives in its own directory and keeps the provider's own match and
player ids. It is NOT merged into `data/base/*.parquet` and no attempt is made
to map provider players onto TML player names. Fuzzy name matching across two
tennis data providers is silently wrong often enough that a name-joined dataset
would quietly corrupt the aggregations that consume `data/base/`. If a join is
ever wanted it should be a reviewed, explicit crosswalk (like the existing
`mcp_player_crosswalk.parquet`), not a side effect of a fetch script.

TRUTHFULNESS
------------
Nothing here is synthesised. A completed match can legitimately carry an empty
`games` array and null in-game points; those stay empty rather than being filled
in. Every match row carries the provider's own `coverage` value and every tape
carries `point_source`, which say whether the rows were watched live or expanded
after the fact. `reconstructed_partial` in particular means the tape is known
NOT to cover the whole match — filter on these before using a tape as if it were
complete. The script does not compute a "complete" flag, because the provider
does not publish one and inventing it would be a claim we cannot support.

USAGE
-----
    export LIVETENNISAPI_KEY=...            # from https://livetennisapi.com
    python scripts/fetch_livetennisapi.py --from 2026-07-01 --to 2026-07-31
    python scripts/fetch_livetennisapi.py --from 2026-07-01 --to 2026-07-31 --tapes 200

    python scripts/fetch_livetennisapi.py --selftest    # offline, no key needed

OUTPUT (under data/livetennisapi/)
    history_matches.parquet       one row per completed match + its tape coverage
    tape_points.parquet           one row per tape row, only with --tapes
    metadata.json                 provenance: range, counts, coverage histogram

TIERS: listing completed matches and reading a tape need BASIC. The pre-built
monthly bulk packages (`/history/packages`) need PRO and are not used here — a
date range keeps this script useful on the lower tier.

API reference: https://docs.livetennisapi.com
OpenAPI spec:  https://github.com/livetennisapi/openapi  (v1.1.0)
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd
import requests

# ── Configuration ─────────────────────────────────────────────────────────────

DEFAULT_BASE_URL = "https://api.livetennisapi.com/api/public/v1"
OUTPUT_DIR = "data/livetennisapi"

# Documented page size ceiling for this API.
PAGE_LIMIT = 200

# Refuse to loop forever if a server ever reports has_more without advancing.
MAX_PAGES = 500

REQUEST_TIMEOUT = 30
MAX_RETRIES = 4

# Values of the provider's `coverage` enum, used to validate --coverage locally
# so a typo fails before it costs a request.
COVERAGE_VALUES = (
    "from_start",
    "partial",
    "reconstructed",
    "reconstructed_partial",
    "none",
)


class ApiError(RuntimeError):
    """A request failed in a way that should stop the fetch."""


# ── HTTP ──────────────────────────────────────────────────────────────────────

def _api_key():
    """Return the configured key, or None when the source is not enabled."""
    key = os.environ.get("LIVETENNISAPI_KEY", "").strip()
    return key or None


def _base_url():
    return os.environ.get("LIVETENNISAPI_BASE_URL", DEFAULT_BASE_URL).rstrip("/")


def _get(session, path, params=None):
    """
    GET one endpoint and return the decoded JSON body.

    Retries on 429 and 5xx, honouring Retry-After when the server sends it.
    401/403 are terminal and are reported in the operator's terms rather than as
    a bare status code.
    """
    url = f"{_base_url()}{path}"
    delay = 2

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        except requests.RequestException as exc:
            if attempt == MAX_RETRIES:
                raise ApiError(f"network error calling {path}: {exc}") from exc
            time.sleep(delay)
            delay *= 2
            continue

        if response.status_code == 200:
            try:
                return response.json()
            except ValueError as exc:
                raise ApiError(f"{path} returned a non-JSON body") from exc

        if response.status_code == 401:
            raise ApiError(
                "401 from the API: LIVETENNISAPI_KEY is missing, expired or wrong."
            )

        if response.status_code == 403:
            raise ApiError(
                f"403 from {path}: this key's plan does not include that data. "
                "Listing completed matches and reading a tape require BASIC."
            )

        if response.status_code == 404:
            return None

        if response.status_code == 429 or response.status_code >= 500:
            if attempt == MAX_RETRIES:
                raise ApiError(f"{path} still failing with HTTP {response.status_code}")
            wait = delay
            retry_after = response.headers.get("Retry-After")
            if retry_after:
                try:
                    wait = max(wait, int(float(retry_after)))
                except (TypeError, ValueError):
                    pass
            time.sleep(wait)
            delay *= 2
            continue

        # 400 and anything else unexpected: surface the server's own message.
        detail = ""
        try:
            body = response.json()
            if isinstance(body, dict):
                detail = f" — {body.get('message') or body.get('error') or body}"
        except ValueError:
            pass
        raise ApiError(f"{path} returned HTTP {response.status_code}{detail}")

    raise ApiError(f"{path} exhausted retries")


def _session(key):
    session = requests.Session()
    session.headers.update(
        {
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
            "User-Agent": "tml-data/livetennisapi-fetch",
        }
    )
    return session


# ── Flattening ────────────────────────────────────────────────────────────────

def _as_dict(value):
    return value if isinstance(value, dict) else {}


def _sets_pair(score):
    """
    Return (sets_p1, sets_p2) from a score object.

    `sets` is documented as a list of integers; only a clean two-entry list is
    decoded. Anything else yields (None, None) rather than a guess. A completed
    match with no score object is normal and must not be back-filled.
    """
    sets = _as_dict(score).get("sets")
    if isinstance(sets, list) and len(sets) == 2:
        first, second = sets[0], sets[1]
        if isinstance(first, int) and isinstance(second, int):
            return first, second
    return None, None


def _points_pair(points):
    """
    Return (points_p1, points_p2) from an in-game points list.

    Entries are nullable by design — a completed match observed live can carry
    nulls here — so a None entry is preserved as None, not turned into "0".
    """
    if isinstance(points, list) and len(points) == 2:
        return points[0], points[1]
    return None, None


def _json_or_none(value):
    """Preserve a nested structure verbatim as JSON text for Parquet."""
    if value is None:
        return None
    try:
        return json.dumps(value, separators=(",", ":"))
    except (TypeError, ValueError):
        return None


def flatten_match(match):
    """Flatten one HistoryMatch into a single flat record."""
    players = _as_dict(match.get("players"))
    p1 = _as_dict(players.get("p1"))
    p2 = _as_dict(players.get("p2"))
    tape = _as_dict(match.get("tape"))
    sets_p1, sets_p2 = _sets_pair(match.get("score"))

    return {
        "match_id": match.get("id"),
        "tournament": match.get("tournament"),
        "surface": match.get("surface"),
        "indoor": match.get("indoor"),
        "match_format": match.get("format"),
        "round": match.get("round"),
        "status": match.get("status"),
        "event_status": match.get("event_status"),
        "is_doubles": match.get("is_doubles"),
        "scheduled_time": match.get("scheduled_time"),
        "p1_id": p1.get("id"),
        "p1_name": p1.get("name"),
        "p1_country": p1.get("country"),
        "p2_id": p2.get("id"),
        "p2_name": p2.get("name"),
        "p2_country": p2.get("country"),
        # `winner` is 1, 2 or null — null is a real answer (e.g. a walkover),
        # never an invitation to derive one from the sets.
        "winner": match.get("winner"),
        "sets_p1": sets_p1,
        "sets_p2": sets_p2,
        # Provenance of the point data. Carried verbatim; see module docstring.
        "tape_coverage": tape.get("coverage"),
        "tape_observed_rows": tape.get("rows"),
        "tape_reconstructed_rows": tape.get("reconstructed_rows"),
    }


def flatten_tape(match_id, payload):
    """
    Flatten a HistoryTape payload into (rows, meta).

    `sets`, `games` and `points` are kept verbatim as JSON text alongside the
    decoded scalars: their nesting is provider-defined and re-shaping it here
    would bake an assumption into the stored data.
    """
    meta = _as_dict(payload.get("meta"))
    tape = payload.get("tape")
    if not isinstance(tape, list):
        tape = []

    rows = []
    for index, row in enumerate(tape):
        row = _as_dict(row)
        sets = row.get("sets")
        sets_p1, sets_p2 = (None, None)
        if isinstance(sets, list) and len(sets) == 2:
            sets_p1, sets_p2 = sets[0], sets[1]
        points_p1, points_p2 = _points_pair(row.get("points"))

        rows.append(
            {
                "match_id": match_id,
                "row_index": index,
                "sets_p1": sets_p1,
                "sets_p2": sets_p2,
                "games_json": _json_or_none(row.get("games")),
                "points_p1": points_p1,
                "points_p2": points_p2,
                "points_json": _json_or_none(row.get("points")),
                "server": row.get("server"),
                "is_tiebreak": row.get("is_tiebreak"),
                "win_probability_p1": row.get("win_probability_p1"),
                "danger": row.get("danger"),
                # Null timestamp is the row-level marker of a reconstructed row.
                "timestamp": row.get("timestamp"),
                # Tape-level provenance, repeated so a points-only reader cannot
                # lose it. Reported once by the API and never per row.
                "point_source": meta.get("point_source"),
                "coverage": meta.get("coverage"),
            }
        )

    return rows, meta


# ── Fetching ──────────────────────────────────────────────────────────────────

def fetch_history_matches(session, date_from, date_to, coverage=None, max_matches=None):
    """
    Page through completed matches for a date range.

    Paging stops on `meta.has_more`, not on a short page. When `?coverage=` is
    used the API applies the filter after the page is cut, so a filtered page is
    routinely shorter than the limit — and may be empty — while later pages
    still hold matching matches. Treating a short page as the end would silently
    truncate the fetch.
    """
    collected = []
    offset = 0

    for page in range(MAX_PAGES):
        params = {"limit": PAGE_LIMIT, "offset": offset}
        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to
        if coverage:
            params["coverage"] = coverage

        payload = _get(session, "/history/matches", params) or {}
        data = payload.get("data") or []
        meta = _as_dict(payload.get("meta"))

        collected.extend(flatten_match(m) for m in data if isinstance(m, dict))
        print(f"  page {page + 1}: +{len(data)} matches (total {len(collected):,})")

        if max_matches is not None and len(collected) >= max_matches:
            return collected[:max_matches]

        if not meta.get("has_more"):
            return collected

        # Advance by the page window, not by the number of rows survived the
        # coverage filter, or a filtered fetch would re-read the same page.
        offset += PAGE_LIMIT

    print(f"⚠️ Warning: stopped at the {MAX_PAGES}-page safety limit; range may be partial.")
    return collected


def fetch_tapes(session, match_ids, sequence="clean", pause=0.2):
    """Fetch per-match tapes. One match per request, so this is the slow path."""
    all_rows = []
    missing = 0

    for position, match_id in enumerate(match_ids, start=1):
        payload = _get(
            session, f"/history/matches/{match_id}", {"sequence": sequence}
        )
        if payload is None:
            missing += 1
            continue

        rows, meta = flatten_tape(match_id, payload)
        all_rows.extend(rows)

        if position % 25 == 0 or position == len(match_ids):
            print(f"  tapes {position}/{len(match_ids)} ({len(all_rows):,} rows)")
        if meta.get("coverage") is None and rows:
            print(f"  ⚠️ match {match_id}: tape rows without coverage metadata")

        if pause:
            time.sleep(pause)

    if missing:
        print(f"  {missing} match(es) had no tape available (404)")
    return all_rows


# ── Output ────────────────────────────────────────────────────────────────────

def _coverage_histogram(matches):
    counts = {}
    for row in matches:
        key = row.get("tape_coverage") or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


def write_outputs(matches, tape_rows, output_dir, date_from, date_to):
    """Write the Parquet files and the provenance metadata."""
    os.makedirs(output_dir, exist_ok=True)

    matches_path = os.path.join(output_dir, "history_matches.parquet")
    df_matches = pd.DataFrame(matches)
    # Nullable integers: a missing id must stay missing, not become 0.0.
    for column in ("match_id", "p1_id", "p2_id", "winner", "sets_p1", "sets_p2",
                   "tape_observed_rows", "tape_reconstructed_rows"):
        if column in df_matches.columns:
            df_matches[column] = pd.to_numeric(
                df_matches[column], errors="coerce"
            ).astype("Int64")
    df_matches.to_parquet(matches_path, index=False, compression="zstd")
    print(f"✅ Wrote {matches_path} ({len(df_matches):,} matches)")

    tape_path = None
    if tape_rows:
        tape_path = os.path.join(output_dir, "tape_points.parquet")
        df_tape = pd.DataFrame(tape_rows)
        for column in ("match_id", "row_index", "sets_p1", "sets_p2", "server"):
            if column in df_tape.columns:
                df_tape[column] = pd.to_numeric(
                    df_tape[column], errors="coerce"
                ).astype("Int64")
        df_tape.to_parquet(tape_path, index=False, compression="zstd")
        print(f"✅ Wrote {tape_path} ({len(df_tape):,} tape rows)")

    metadata = {
        "source": "livetennisapi",
        "source_url": "https://livetennisapi.com",
        "api_version": "v1",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "range": {"from": date_from, "to": date_to},
        "match_count": len(matches),
        "tape_row_count": len(tape_rows),
        "coverage_histogram": _coverage_histogram(matches),
        "joined_to_tml": False,
        "notes": (
            "Provider match/player ids are their own id space and are not "
            "mapped to TML players. `tape_coverage` / `point_source` state "
            "whether rows were watched live or expanded after the fact; "
            "'reconstructed_partial' is known not to cover the whole match."
        ),
    }
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
    print(f"✅ Wrote {metadata_path}")

    return matches_path, tape_path, metadata_path


# ── Self-test (offline) ───────────────────────────────────────────────────────

def _selftest():
    """
    Offline checks against spec-shaped payloads. No network, no key.

    These cover the parsing decisions that would otherwise only be exercised in
    production: nullable score fields, empty games arrays on a completed match,
    reconstructed rows, and the coverage-filtered paging rule.
    """
    # A completed match with an EMPTY games array and null in-game points. This
    # is documented as normal and must not be turned into a score.
    match = {
        "id": 900001,
        "tournament": "Example Open",
        "surface": "hard",
        "indoor": False,
        "format": "BO3",
        "round": "QF",
        "status": "completed",
        "event_status": None,
        "is_doubles": False,
        "scheduled_time": "2026-07-04T11:00:00Z",
        "players": {
            "p1": {"id": 11, "name": "Player One", "country": "ESP"},
            "p2": {"id": 22, "name": "Player Two", "country": None},
        },
        "score": {"sets": [2, 1], "games": [], "points": [None, None],
                  "server": None, "is_tiebreak": False},
        "winner": 1,
        "tape": {"coverage": "reconstructed_partial", "rows": 0,
                 "reconstructed_rows": 118},
    }
    flat = flatten_match(match)
    assert flat["match_id"] == 900001
    assert (flat["sets_p1"], flat["sets_p2"]) == (2, 1)
    assert flat["p1_name"] == "Player One" and flat["p2_country"] is None
    assert flat["tape_coverage"] == "reconstructed_partial"
    assert flat["tape_observed_rows"] == 0
    print("  ✓ completed match with empty games / null points")

    # No score object at all — must stay missing.
    flat_none = flatten_match({"id": 2, "players": {}, "score": None})
    assert (flat_none["sets_p1"], flat_none["sets_p2"]) == (None, None)
    assert flat_none["winner"] is None
    print("  ✓ absent score is not synthesised")

    # A malformed sets array must not be half-decoded.
    assert _sets_pair({"sets": [2]}) == (None, None)
    assert _sets_pair({"sets": [2, 1, 0]}) == (None, None)
    assert _sets_pair({}) == (None, None)
    print("  ✓ malformed sets rejected")

    # Tape: an observed row and a reconstructed row (null timestamp + null model
    # fields) in one mixed tape.
    payload = {
        "match": match,
        "tape": [
            {"sets": [0, 0], "games": [[0], [0]], "points": ["15", "0"],
             "server": 1, "is_tiebreak": False, "win_probability_p1": None,
             "danger": None, "timestamp": None},
            {"sets": [1, 0], "games": [[6, 1], [4, 0]], "points": ["40", "AD"],
             "server": 2, "is_tiebreak": False, "win_probability_p1": 0.61,
             "danger": 0.2, "timestamp": "2026-07-04T12:10:00Z"},
        ],
        "profiles": [],
        "meta": {"match_id": 900001, "rows": 2, "coverage": "reconstructed_partial",
                 "point_source": "mixed", "raw_rows": 5, "unique_states": 2,
                 "sequence": "clean", "from_archive": True,
                 "generated_at": "2026-08-03T00:00:00Z"},
    }
    rows, meta = flatten_tape(900001, payload)
    assert len(rows) == 2 and meta["point_source"] == "mixed"
    assert rows[0]["timestamp"] is None and rows[0]["win_probability_p1"] is None
    assert rows[0]["points_p1"] == "15" and rows[0]["points_p2"] == "0"
    assert rows[1]["server"] == 2 and rows[1]["danger"] == 0.2
    assert rows[1]["point_source"] == "mixed"
    assert json.loads(rows[1]["games_json"]) == [[6, 1], [4, 0]]
    print("  ✓ mixed tape keeps reconstructed rows null and nesting verbatim")

    # An empty tape is a valid answer, not an error.
    empty_rows, empty_meta = flatten_tape(3, {"tape": [], "meta": {"coverage": "none",
                                                                  "point_source": None}})
    assert empty_rows == [] and empty_meta["coverage"] == "none"
    print("  ✓ empty tape handled")

    # Paging: a coverage-filtered page can be EMPTY while more pages remain.
    pages = [
        {"data": [], "meta": {"has_more": True, "limit": PAGE_LIMIT, "offset": 0}},
        {"data": [match], "meta": {"has_more": True, "limit": PAGE_LIMIT,
                                   "offset": PAGE_LIMIT}},
        {"data": [match], "meta": {"has_more": False, "limit": PAGE_LIMIT,
                                   "offset": PAGE_LIMIT * 2}},
    ]
    seen_offsets = []

    class _StubSession:
        pass

    original_get = globals()["_get"]

    def fake_get(session, path, params=None):
        seen_offsets.append((params or {}).get("offset"))
        return pages[len(seen_offsets) - 1]

    globals()["_get"] = fake_get
    try:
        result = fetch_history_matches(
            _StubSession(), "2026-07-01", "2026-07-31", coverage="from_start"
        )
    finally:
        globals()["_get"] = original_get

    assert len(result) == 2, f"expected 2 matches across pages, got {len(result)}"
    assert seen_offsets == [0, PAGE_LIMIT, PAGE_LIMIT * 2], seen_offsets
    print("  ✓ empty filtered page is not treated as end-of-data")

    # The coverage histogram counts what is there and labels the rest honestly.
    histogram = _coverage_histogram(
        [{"tape_coverage": "from_start"}, {"tape_coverage": "from_start"},
         {"tape_coverage": None}]
    )
    assert histogram == {"from_start": 2, "unknown": 1}, histogram
    print("  ✓ coverage histogram")

    print("✅ Self-test passed (offline, spec-shaped payloads).")
    return True


# ── Entry point ───────────────────────────────────────────────────────────────

def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Optional: fetch point-by-point tape from the Live Tennis API."
    )
    parser.add_argument("--from", dest="date_from",
                        help="Earliest play date, YYYY-MM-DD.")
    parser.add_argument("--to", dest="date_to",
                        help="Latest play date, YYYY-MM-DD.")
    parser.add_argument("--coverage", choices=COVERAGE_VALUES,
                        help="Keep only matches whose tape has this coverage.")
    parser.add_argument("--max-matches", type=int, default=None,
                        help="Stop after this many matches.")
    parser.add_argument("--tapes", type=int, nargs="?", const=100, default=0,
                        metavar="N",
                        help="Also fetch the tape for the first N matches "
                             "(one request each; default 100 when given bare).")
    parser.add_argument("--sequence", choices=("raw", "clean"), default="clean",
                        help="'clean' collapses repeated score states (default).")
    parser.add_argument("--output-dir", default=OUTPUT_DIR)
    parser.add_argument("--selftest", action="store_true",
                        help="Run offline parsing checks and exit.")
    args = parser.parse_args(argv)

    if args.selftest:
        print("Running offline self-test (no network, no API key)...")
        return _selftest()

    print("-" * 60)
    print("OPTIONAL SOURCE: Live Tennis API (point-by-point tape)")
    print("-" * 60)

    key = _api_key()
    if not key:
        # The whole point of the opt-in: no key, no work, no files, no failure.
        print("ℹ️  LIVETENNISAPI_KEY not set — optional source disabled, skipping.")
        print("   Set it to enable; see scripts/fetch_livetennisapi.py for details.")
        return True

    if args.date_from and args.date_to and args.date_from > args.date_to:
        print("❌ Error: --from is after --to")
        return False

    session = _session(key)

    try:
        print(f"Fetching completed matches "
              f"[{args.date_from or 'earliest'} → {args.date_to or 'latest'}]"
              + (f", coverage={args.coverage}" if args.coverage else ""))
        matches = fetch_history_matches(
            session,
            args.date_from,
            args.date_to,
            coverage=args.coverage,
            max_matches=args.max_matches,
        )

        if not matches:
            print("⚠️ Warning: no matches returned for that range; nothing written.")
            return True

        tape_rows = []
        if args.tapes:
            ids = [m["match_id"] for m in matches[: args.tapes] if m.get("match_id")]
            print(f"Fetching tapes for {len(ids)} match(es), sequence={args.sequence}")
            tape_rows = fetch_tapes(session, ids, sequence=args.sequence)

    except ApiError as exc:
        print(f"❌ Error: {exc}")
        return False

    write_outputs(matches, tape_rows, args.output_dir, args.date_from, args.date_to)

    histogram = _coverage_histogram(matches)
    print("Tape coverage: " + ", ".join(f"{k}={v}" for k, v in histogram.items()))
    print("Reminder: 'reconstructed_partial' does not cover the whole match.")
    return True


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
