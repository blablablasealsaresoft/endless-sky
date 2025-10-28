# Atlantean Sovereignty Production Service

The Atlantean Sovereignty campaign markets live ladders, telemetry, and a
crypto-inspired economy. The original Endless Sky content pack only scripted
those systems locally, so we provide a lightweight companion service that
implements the advertised features using a simple REST API backed by SQLite.

This document explains how to run the service, describes the API, and offers
deployment tips for production environments.

## Quick start

1. Ensure Python 3.9+ is available on the host.
2. From the repository root, run:

   ```bash
   python3 server/atlantean_server.py --db dist/atlantean_prod.sqlite --host 0.0.0.0 --port 8080
   ```

   This creates the SQLite database (if necessary) and starts listening for
   HTTP requests. Use `Ctrl+C` to stop the process.

3. (Optional) Initialize the database schema without starting the server:

   ```bash
   python3 server/atlantean_server.py --db dist/atlantean_prod.sqlite --init-only
   ```

## API reference

All endpoints exchange JSON payloads. Error responses return an `error`
property describing what went wrong. The base URL examples below assume the
server is running at `http://localhost:8080`.

### `GET /healthz`

Returns aggregate counts for ladder, ledger, and telemetry entries.

**Response body**

```json
{
  "ladder_entries": 5,
  "ledger_entries": 3,
  "telemetry_events": 28,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### `POST /api/v1/ladder/submit`

Records a ladder score for a player. Higher scores replace a player's previous
record in leaderboard views.

**Request body**

```json
{
  "player": "PilotName",
  "score": 12345,
  "match_id": "optional-match-identifier"
}
```

`match_id` is optional. The `score` must be a positive integer.

**Response**: `201 Created` with `{ "status": "recorded" }`.

### `GET /api/v1/ladder/top?limit=10`

Returns the top players by their best score. `limit` controls how many records
to return (1–100).

**Response body**

```json
{
  "results": [
    {"player": "PilotName", "best_score": 12345, "first_recorded": "2024-01-01T12:00:00"}
  ]
}
```

### `POST /api/v1/ledger/record`

Stores a faux blockchain ledger entry. Duplicate `tx_id` values are replaced so
the endpoint may be used idempotently.

**Request body**

```json
{
  "player": "PilotName",
  "amount": 10.5,
  "asset": "SOL",
  "tx_id": "unique-transaction-id",
  "metadata": {"note": "quest reward"}
}
```

`metadata` is optional but, when provided, must be a JSON object.

### `GET /api/v1/ledger/{player}`

Returns ledger entries for a player ordered by most recent first.

### `POST /api/v1/telemetry/event`

Ingests a gameplay telemetry event.

**Request body**

```json
{
  "event_type": "match_start",
  "player": "PilotName",
  "metadata": {"map": "aurora-station"}
}
```

The `player` field is optional for system-level events. Metadata defaults to an
empty object.

### `GET /api/v1/telemetry/export?limit=100`

Exports telemetry events (newest first). `limit` is optional; omit it to export
all events.

## Deployment notes

- The service uses SQLite for persistence and accepts concurrent requests.
  Place the database on durable storage for production deployments.
- Run behind a reverse proxy (nginx, Apache, Caddy) to terminate TLS and manage
  authentication or rate limiting if required.
- The service is stateless beyond the SQLite file, making it easy to containerise
  or manage with process supervisors like `systemd`.
- Use standard backup tooling to capture the database file; the schema is small
  and intentionally simple.

## Game integration tips

The Endless Sky engine remains offline, but missions and plugins can interact
with this service via scripting hooks, HTTP requests from auxiliary tools, or
manual imports/exports. The provided API allows tournament organisers or live
ops staff to track player progress, manage rewards, and collect telemetry while
keeping the core game untouched.

