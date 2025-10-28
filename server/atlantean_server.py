"""Minimal production service for the Atlantean Sovereignty data pack.

The Endless Sky engine ships as an offline, single-player experience. This
module introduces a lightweight companion service that implements the "live"
features marketed by the Atlantean Sovereignty documentation: ladders,
telemetry ingestion, and a faux blockchain ledger. While intentionally
minimalist, the implementation is fully functional and safe to deploy in a
traditional production environment.

The server exposes a small JSON REST API backed by a SQLite database. Data is
persisted across restarts and the process can be supervised by any traditional
process manager (systemd, supervisord, container orchestrators, etc.).

Example usage from the repository root::

    python3 server/atlantean_server.py --db dist/atlantean_prod.sqlite \
        --host 0.0.0.0 --port 8080

This will create the SQLite database if it does not exist and start listening
for HTTP requests. See ``docs/atlantean/production.md`` for the full API
reference and deployment guidance.
"""

from __future__ import annotations

import argparse
import json
import logging
import sqlite3
import threading
import time
from datetime import UTC, datetime
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Iterable, Optional, Set, Tuple
from urllib.parse import parse_qs, urlparse


LOG = logging.getLogger(__name__)


class AtlanteanDatabase:
    """SQLite persistence helper for ladder, ledger, and telemetry data."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._lock = threading.Lock()
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self._ensure_schema()

    # ------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        with self._connection:  # type: ignore[call-arg]
            # Use WAL for improved concurrency and durability under multi-process
            # deployments while keeping the schema intentionally lightweight.
            self._connection.execute("PRAGMA journal_mode=WAL;")
            self._connection.execute("PRAGMA foreign_keys=ON;")
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS ladder_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player TEXT NOT NULL,
                    score INTEGER NOT NULL,
                    match_id TEXT,
                    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS ledger_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player TEXT NOT NULL,
                    amount REAL NOT NULL,
                    asset TEXT NOT NULL,
                    tx_id TEXT NOT NULL UNIQUE,
                    metadata TEXT,
                    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS telemetry_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    player TEXT,
                    metadata TEXT,
                    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )

    # ------------------------------------------------------------------
    def record_ladder_score(self, player: str, score: int, match_id: str | None) -> None:
        LOG.debug("Recording ladder score", extra={"player": player, "score": score})
        with self._lock, self._connection:  # type: ignore[call-arg]
            self._connection.execute(
                "INSERT INTO ladder_scores(player, score, match_id) VALUES (?, ?, ?)",
                (player, score, match_id),
            )

    # ------------------------------------------------------------------
    def top_ladder(self, limit: int) -> list[dict[str, Any]]:
        query = """
            SELECT player, MAX(score) AS best_score,
                   MIN(recorded_at) AS first_recorded
              FROM ladder_scores
             GROUP BY player
             ORDER BY best_score DESC, first_recorded ASC
             LIMIT ?
        """
        with self._lock:
            rows = self._connection.execute(query, (limit,)).fetchall()

        results: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            if isinstance(payload.get("first_recorded"), datetime):
                payload["first_recorded"] = payload["first_recorded"].isoformat()
            results.append(payload)
        return results

    # ------------------------------------------------------------------
    def record_ledger_entry(
        self,
        player: str,
        amount: float,
        asset: str,
        tx_id: str,
        metadata: dict[str, Any] | None,
    ) -> None:
        payload = json.dumps(metadata or {}, sort_keys=True)
        with self._lock, self._connection:  # type: ignore[call-arg]
            self._connection.execute(
                """
                INSERT OR REPLACE INTO ledger_entries(player, amount, asset, tx_id, metadata)
                VALUES (?, ?, ?, ?, ?)
                """,
                (player, amount, asset, tx_id, payload),
            )

    # ------------------------------------------------------------------
    def ledger_for_player(self, player: str) -> list[dict[str, Any]]:
        query = (
            "SELECT player, amount, asset, tx_id, metadata, recorded_at "
            "FROM ledger_entries WHERE player = ? ORDER BY recorded_at DESC"
        )
        with self._lock:
            rows = self._connection.execute(query, (player,)).fetchall()
        results = []
        for row in rows:
            parsed = dict(row)
            try:
                parsed["metadata"] = json.loads(parsed.get("metadata") or "{}")
            except json.JSONDecodeError:
                parsed["metadata"] = {}
            recorded = parsed.get("recorded_at")
            if isinstance(recorded, datetime):
                parsed["recorded_at"] = recorded.isoformat()
            else:
                parsed["recorded_at"] = str(recorded)
            results.append(parsed)
        return results

    # ------------------------------------------------------------------
    def record_telemetry(self, event_type: str, player: str | None, metadata: dict[str, Any]) -> None:
        payload = json.dumps(metadata or {}, sort_keys=True)
        with self._lock, self._connection:  # type: ignore[call-arg]
            self._connection.execute(
                "INSERT INTO telemetry_events(event_type, player, metadata) VALUES (?, ?, ?)",
                (event_type, player, payload),
            )

    # ------------------------------------------------------------------
    def telemetry_events(self, limit: int | None = None) -> list[dict[str, Any]]:
        query = "SELECT event_type, player, metadata, recorded_at FROM telemetry_events"
        params: Tuple[Any, ...] = ()
        if limit is not None:
            query += " ORDER BY recorded_at DESC LIMIT ?"
            params = (limit,)
        else:
            query += " ORDER BY recorded_at DESC"

        with self._lock:
            rows = self._connection.execute(query, params).fetchall()

        events: list[dict[str, Any]] = []
        for row in rows:
            payload = dict(row)
            try:
                payload["metadata"] = json.loads(payload.get("metadata") or "{}")
            except json.JSONDecodeError:
                payload["metadata"] = {}
            recorded = payload.get("recorded_at")
            if isinstance(recorded, datetime):
                payload["recorded_at"] = recorded.isoformat()
            else:
                payload["recorded_at"] = str(recorded)
            events.append(payload)
        return events

    # ------------------------------------------------------------------
    def health_summary(self) -> dict[str, Any]:
        with self._lock:
            ladder_count = self._connection.execute("SELECT COUNT(*) FROM ladder_scores").fetchone()[
                0
            ]
            ledger_count = self._connection.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[
                0
            ]
            telemetry_count = self._connection.execute(
                "SELECT COUNT(*) FROM telemetry_events"
            ).fetchone()[0]

        return {
            "ladder_entries": ladder_count,
            "ledger_entries": ledger_count,
            "telemetry_events": telemetry_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    # ------------------------------------------------------------------
    def stats_summary(self, ladder_limit: int = 10) -> dict[str, Any]:
        """Return aggregate production statistics for dashboards."""

        top_players = self.top_ladder(ladder_limit)

        with self._lock:
            ladder_entries = self._connection.execute("SELECT COUNT(*) FROM ladder_scores").fetchone()[
                0
            ]
            ladder_players = self._connection.execute(
                "SELECT COUNT(DISTINCT player) FROM ladder_scores"
            ).fetchone()[0]

            ledger_entries = self._connection.execute("SELECT COUNT(*) FROM ledger_entries").fetchone()[
                0
            ]
            ledger_assets = self._connection.execute(
                "SELECT asset, SUM(amount) AS total_amount FROM ledger_entries GROUP BY asset"
            ).fetchall()

            telemetry_events = self._connection.execute(
                "SELECT COUNT(*) FROM telemetry_events"
            ).fetchone()[0]
            telemetry_types = self._connection.execute(
                "SELECT event_type, COUNT(*) AS count FROM telemetry_events GROUP BY event_type"
            ).fetchall()

        asset_totals = [
            {"asset": row["asset"], "total": float(row["total_amount"] or 0.0)}
            for row in ledger_assets
        ]
        telemetry_breakdown = [
            {"event_type": row["event_type"], "count": int(row["count"])} for row in telemetry_types
        ]

        return {
            "generated_at": datetime.now(UTC).isoformat(),
            "ladder": {
                "entries": int(ladder_entries),
                "players": int(ladder_players),
                "top": top_players,
            },
            "ledger": {
                "entries": int(ledger_entries),
                "assets": asset_totals,
            },
            "telemetry": {
                "events": int(telemetry_events),
                "types": telemetry_breakdown,
            },
        }


class AtlanteanRequestHandler(BaseHTTPRequestHandler):
    """Serve REST API endpoints using :class:`AtlanteanDatabase`."""

    server_version = "AtlanteanProdServer/1.0"
    db: AtlanteanDatabase
    api_key_header = "X-Atlantean-Key"

    def log_message(self, format: str, *args: Any) -> None:  # pragma: no cover - noisy in tests
        LOG.info("%s - %s", self.address_string(), format % args)

    # ------------------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 - inherited name
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/") and not self._require_api_key():
            return
        if parsed.path == "/healthz":
            return self._send_json(HTTPStatus.OK, self.db.health_summary())
        if parsed.path == "/api/v1/ladder/top":
            params = parse_qs(parsed.query or "")
            limit = self._positive_int(params.get("limit", ["10"])[0], 1, 100)
            if limit is None:
                return
            payload = {"results": self.db.top_ladder(limit)}
            return self._send_json(HTTPStatus.OK, payload)
        if parsed.path.startswith("/api/v1/ledger/"):
            _, _, player = parsed.path.partition("/api/v1/ledger/")
            if not player:
                return self._send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"error": "Player identifier is required in the URL."},
                )
            data = self.db.ledger_for_player(player)
            return self._send_json(HTTPStatus.OK, {"player": player, "entries": data})
        if parsed.path == "/api/v1/telemetry/export":
            params = parse_qs(parsed.query or "")
            limit_param = params.get("limit", [None])[0]
            limit = None
            if limit_param is not None:
                limit = self._positive_int(limit_param, 1, 1000)
                if limit is None:
                    return
            events = self.db.telemetry_events(limit)
            return self._send_json(HTTPStatus.OK, {"events": events})
        if parsed.path == "/api/v1/stats/summary":
            params = parse_qs(parsed.query or "")
            limit_param = params.get("top_limit", ["10"])[0]
            top_limit = self._positive_int(limit_param, 1, 100)
            if top_limit is None:
                return
            payload = self.db.stats_summary(top_limit)
            return self._send_json(HTTPStatus.OK, payload)

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown endpoint."})

    # ------------------------------------------------------------------
    def do_POST(self) -> None:  # noqa: N802 - inherited name
        parsed = urlparse(self.path)
        if parsed.path.startswith("/api/") and not self._require_api_key():
            return
        if parsed.path == "/api/v1/ladder/submit":
            return self._handle_ladder_submit()
        if parsed.path == "/api/v1/ledger/record":
            return self._handle_ledger_record()
        if parsed.path == "/api/v1/telemetry/event":
            return self._handle_telemetry_event()

        self._send_json(HTTPStatus.NOT_FOUND, {"error": "Unknown endpoint."})

    # ------------------------------------------------------------------
    def _require_api_key(self) -> bool:
        server = getattr(self, "server")
        if not getattr(server, "require_auth", False):
            return True
        provided = (self.headers.get(self.api_key_header) or "").strip()
        if provided and provided in getattr(server, "api_keys", frozenset()):
            return True
        self._send_json(
            HTTPStatus.UNAUTHORIZED,
            {"error": "Missing or invalid Atlantean API key."},
        )
        return False

    # ------------------------------------------------------------------
    def _handle_ladder_submit(self) -> None:
        body = self._require_json_body({"player", "score"})
        if body is None:
            return
        player = str(body["player"]).strip()
        score = self._positive_int(body["score"], 0, 10_000_000)
        if score is None:
            return
        match_id = str(body.get("match_id")).strip() or None
        if not player:
            return self._send_json(HTTPStatus.BAD_REQUEST, {"error": "player cannot be empty"})
        self.db.record_ladder_score(player, score, match_id)
        self._send_json(HTTPStatus.CREATED, {"status": "recorded"})

    # ------------------------------------------------------------------
    def _handle_ledger_record(self) -> None:
        body = self._require_json_body({"player", "amount", "asset", "tx_id"})
        if body is None:
            return
        player = str(body["player"]).strip()
        asset = str(body["asset"]).strip()
        tx_id = str(body["tx_id"]).strip()
        if not player or not asset or not tx_id:
            return self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "player, asset, and tx_id must be non-empty strings"},
            )
        try:
            amount = float(body["amount"])
        except (TypeError, ValueError):
            return self._send_json(HTTPStatus.BAD_REQUEST, {"error": "amount must be numeric"})
        metadata = body.get("metadata")
        if metadata is not None and not isinstance(metadata, dict):
            return self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "metadata must be an object if provided"},
            )
        self.db.record_ledger_entry(player, amount, asset, tx_id, metadata)
        self._send_json(HTTPStatus.CREATED, {"status": "recorded"})

    # ------------------------------------------------------------------
    def _handle_telemetry_event(self) -> None:
        body = self._require_json_body({"event_type"})
        if body is None:
            return
        event_type = str(body["event_type"]).strip()
        if not event_type:
            return self._send_json(
                HTTPStatus.BAD_REQUEST, {"error": "event_type must be a non-empty string"}
            )
        player = body.get("player")
        player_id = str(player).strip() if player is not None else None
        metadata = body.get("metadata") or {}
        if metadata and not isinstance(metadata, dict):
            return self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": "metadata must be an object if provided"},
            )
        self.db.record_telemetry(event_type, player_id or None, metadata)
        self._send_json(HTTPStatus.CREATED, {"status": "recorded"})

    # ------------------------------------------------------------------
    def _require_json_body(self, required: set[str]) -> Optional[Dict[str, Any]]:
        length_header = self.headers.get("Content-Length")
        if length_header is None:
            self._send_json(HTTPStatus.LENGTH_REQUIRED, {"error": "Content-Length is required"})
            return None
        try:
            length = int(length_header)
        except ValueError:
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Invalid Content-Length"})
            return None
        body_raw = self.rfile.read(length)
        try:
            payload = json.loads(body_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Request body must be valid JSON"})
            return None

        if not isinstance(payload, dict):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "JSON body must be an object"})
            return None
        missing = required - payload.keys()
        if missing:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": f"Missing required fields: {', '.join(sorted(missing))}"},
            )
            return None
        return payload

    # ------------------------------------------------------------------
    def _positive_int(self, value: Any, minimum: int, maximum: int) -> int | None:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            self._send_json(HTTPStatus.BAD_REQUEST, {"error": "Expected integer value"})
            return None
        if parsed < minimum or parsed > maximum:
            self._send_json(
                HTTPStatus.BAD_REQUEST,
                {"error": f"Value must be between {minimum} and {maximum}"},
            )
            return None
        return parsed

    # ------------------------------------------------------------------
    def _send_json(self, status: HTTPStatus, payload: Dict[str, Any]) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


class AtlanteanProdServer(ThreadingHTTPServer):
    """HTTP server that exposes :class:`AtlanteanRequestHandler`."""

    def __init__(
        self,
        address: Tuple[str, int],
        db_path: Path,
        api_keys: Iterable[str] | None = None,
        require_auth: Optional[bool] = None,
    ) -> None:
        self.database = AtlanteanDatabase(db_path)
        keys: Set[str] = {key.strip() for key in api_keys or [] if key and key.strip()}
        self.api_keys = frozenset(keys)
        self.require_auth = bool(self.api_keys) if require_auth is None else bool(require_auth)

        class Handler(AtlanteanRequestHandler):
            db = self.database

        super().__init__(address, Handler)


def parse_args(argv: Iterable[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Atlantean Sovereignty prod server")
    parser.add_argument("--host", default="127.0.0.1", help="Host interface to bind")
    parser.add_argument("--port", type=int, default=8080, help="Port to listen on")
    parser.add_argument(
        "--db",
        type=Path,
        default=Path("dist/atlantean_prod.sqlite"),
        help="Path to the SQLite database for persisting state.",
    )
    parser.add_argument(
        "--api-key",
        action="append",
        dest="api_keys",
        default=[],
        help="API key allowed to access the REST endpoints. Can be repeated.",
    )
    parser.add_argument(
        "--api-key-file",
        type=Path,
        help="File containing newline-delimited API keys to trust.",
    )
    parser.add_argument(
        "--require-auth",
        choices=("auto", "yes", "no"),
        default="auto",
        help=(
            "Authentication policy: 'auto' requires keys when provided, 'yes' always "
            "requires a key, 'no' disables key enforcement."
        ),
    )
    parser.add_argument(
        "--init-only",
        action="store_true",
        help="Create the database schema then exit without serving.",
    )
    return parser.parse_args(argv)


def resolve_api_keys(args: argparse.Namespace) -> tuple[Set[str], bool]:
    """Load API keys from CLI args and decide whether authentication is required."""

    keys: Set[str] = {key.strip() for key in args.api_keys if key and key.strip()}
    if args.api_key_file:
        try:
            for line in args.api_key_file.read_text().splitlines():
                key = line.strip()
                if key and not key.startswith("#"):
                    keys.add(key)
        except FileNotFoundError as exc:  # pragma: no cover - exercised via CLI
            exc.add_note(f"API key file not found: {args.api_key_file}")
            raise

    if args.require_auth == "yes":
        enforce = True
    elif args.require_auth == "no":
        enforce = False
    else:
        enforce = bool(keys)
    return keys, enforce


def run_server(args: argparse.Namespace) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    db_path = args.db
    db_path.parent.mkdir(parents=True, exist_ok=True)
    api_keys, enforce_auth = resolve_api_keys(args)
    server = AtlanteanProdServer((args.host, args.port), db_path, api_keys=api_keys, require_auth=enforce_auth)

    if args.init_only:
        LOG.info(
            "Database initialised at %s (auth=%s, api_keys=%s)",
            db_path,
            "enabled" if enforce_auth else "disabled",
            len(api_keys),
        )
        return

    LOG.info(
        "Starting Atlantean production service on %s:%s (auth=%s, api_keys=%s)",
        args.host,
        args.port,
        "enabled" if enforce_auth else "disabled",
        len(api_keys),
    )
    try:
        server.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual shutdown
        LOG.info("Shutting down due to keyboard interrupt")
    finally:
        server.shutdown()
        time.sleep(0.1)  # allow worker threads to drain


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv or [])
    try:
        run_server(args)
        return 0
    except (FileNotFoundError, OSError, ValueError) as exc:
        LOG.error("Failed to start server: %s", exc)
        return 1


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    raise SystemExit(main())

