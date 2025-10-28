"""Integration tests for the Atlantean production service."""

from __future__ import annotations

import json
import socket
import threading
import time
import unittest
from pathlib import Path
from typing import Tuple
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from server.atlantean_server import AtlanteanProdServer


class AtlanteanServerTestCase(unittest.TestCase):
    """Start the HTTP service on a background thread and exercise the API."""

    @classmethod
    def setUpClass(cls) -> None:  # noqa: D401 - unittest API
        cls.tmp_db = Path("tests/.tmp_atlantean.sqlite")
        cls.tmp_db.parent.mkdir(parents=True, exist_ok=True)
        cls.address = cls._free_port()
        cls.api_key = "test-api-key"
        cls.server = AtlanteanProdServer(
            cls.address,
            cls.tmp_db,
            api_keys={cls.api_key},
            require_auth=True,
        )
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        # Wait for server to be ready
        time.sleep(0.2)
        cls.auth_headers = {"X-Atlantean-Key": cls.api_key}

    @classmethod
    def tearDownClass(cls) -> None:  # noqa: D401 - unittest API
        cls.server.shutdown()
        cls.thread.join(timeout=2)
        cls.server.server_close()
        if cls.tmp_db.exists():
            cls.tmp_db.unlink()

    # ------------------------------------------------------------------
    @staticmethod
    def _free_port() -> Tuple[str, int]:
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        addr = sock.getsockname()
        sock.close()
        return addr[0], addr[1]

    # ------------------------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> tuple[int, dict]:
        data = None
        request_headers = {"Content-Type": "application/json"}
        request_headers.update(headers or {})
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = Request(
            f"http://{self.address[0]}:{self.address[1]}{path}",
            data=data,
            method=method,
            headers=request_headers,
        )
        try:
            with urlopen(req) as response:  # noqa: S310 - test utility
                body = response.read().decode("utf-8")
                return response.status, json.loads(body)
        except HTTPError as exc:  # noqa: PERF203 - small helper
            body = exc.read().decode("utf-8")
            return exc.code, json.loads(body)

    # ------------------------------------------------------------------
    def test_health_endpoint_initialises_cleanly(self) -> None:
        status, payload = self._request("GET", "/healthz")
        self.assertEqual(status, 200)
        self.assertEqual(payload["ladder_entries"], 0)
        self.assertEqual(payload["ledger_entries"], 0)
        self.assertEqual(payload["telemetry_events"], 0)

    # ------------------------------------------------------------------
    def test_ladder_submission_and_top_scores(self) -> None:
        for score in (123, 456):
            status, payload = self._request(
                "POST",
                "/api/v1/ladder/submit",
                {"player": "TestPilot", "score": score},
                headers=self.auth_headers,
            )
            self.assertEqual(status, 201)
            self.assertEqual(payload["status"], "recorded")

        status, payload = self._request(
            "GET",
            "/api/v1/ladder/top?limit=5",
            headers=self.auth_headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(len(payload["results"]), 1)
        self.assertEqual(payload["results"][0]["player"], "TestPilot")
        self.assertEqual(payload["results"][0]["best_score"], 456)

    # ------------------------------------------------------------------
    def test_ledger_record_and_lookup(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/v1/ledger/record",
            {
                "player": "TestPilot",
                "amount": 12.5,
                "asset": "SOL",
                "tx_id": "tx-1",
                "metadata": {"note": "reward"},
            },
            headers=self.auth_headers,
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["status"], "recorded")

        status, payload = self._request(
            "GET",
            "/api/v1/ledger/TestPilot",
            headers=self.auth_headers,
        )
        self.assertEqual(status, 200)
        self.assertEqual(payload["player"], "TestPilot")
        self.assertEqual(len(payload["entries"]), 1)
        self.assertEqual(payload["entries"][0]["tx_id"], "tx-1")
        self.assertEqual(payload["entries"][0]["metadata"], {"note": "reward"})

    # ------------------------------------------------------------------
    def test_telemetry_event_recording(self) -> None:
        status, payload = self._request(
            "POST",
            "/api/v1/telemetry/event",
            {
                "event_type": "match_start",
                "player": "TestPilot",
                "metadata": {"map": "arena"},
            },
            headers=self.auth_headers,
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["status"], "recorded")

        status, payload = self._request(
            "GET",
            "/api/v1/telemetry/export?limit=10",
            headers=self.auth_headers,
        )
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(payload["events"]), 1)
        self.assertTrue(
            any(event["event_type"] == "match_start" for event in payload["events"]),
            msg="Expected at least one match_start event in export",
        )

    # ------------------------------------------------------------------
    def test_missing_api_key_rejected(self) -> None:
        status, payload = self._request("GET", "/api/v1/ladder/top?limit=5")
        self.assertEqual(status, 401)
        self.assertIn("error", payload)

    # ------------------------------------------------------------------
    def test_stats_summary_endpoint(self) -> None:
        # Populate representative data
        self._request(
            "POST",
            "/api/v1/ladder/submit",
            {"player": "TestPilot", "score": 789},
            headers=self.auth_headers,
        )
        self._request(
            "POST",
            "/api/v1/ledger/record",
            {
                "player": "TestPilot",
                "amount": 7.5,
                "asset": "SOL",
                "tx_id": "tx-2",
            },
            headers=self.auth_headers,
        )
        for event_type, metadata in (
            ("match_start", {"map": "arena"}),
            ("match_end", {"result": "win"}),
        ):
            self._request(
                "POST",
                "/api/v1/telemetry/event",
                {
                    "event_type": event_type,
                    "player": "TestPilot",
                    "metadata": metadata,
                },
                headers=self.auth_headers,
            )

        status, payload = self._request(
            "GET",
            "/api/v1/stats/summary?top_limit=5",
            headers=self.auth_headers,
        )
        self.assertEqual(status, 200)

        ladder = payload["ladder"]
        self.assertGreaterEqual(ladder["entries"], 3)
        self.assertGreaterEqual(ladder["players"], 1)
        self.assertTrue(ladder["top"])
        self.assertEqual(ladder["top"][0]["player"], "TestPilot")

        ledger = payload["ledger"]
        self.assertGreaterEqual(ledger["entries"], 2)
        asset_totals = {entry["asset"]: entry["total"] for entry in ledger["assets"]}
        self.assertAlmostEqual(asset_totals.get("SOL", 0.0), 20.0)

        telemetry = payload["telemetry"]
        self.assertGreaterEqual(telemetry["events"], 2)
        type_counts = {entry["event_type"]: entry["count"] for entry in telemetry["types"]}
        self.assertGreaterEqual(type_counts.get("match_start", 0), 1)
        self.assertGreaterEqual(type_counts.get("match_end", 0), 1)


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

