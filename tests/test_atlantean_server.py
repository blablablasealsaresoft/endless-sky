"""Integration tests for the Atlantean production service."""

from __future__ import annotations

import json
import socket
import threading
import time
import unittest
from pathlib import Path
from typing import Tuple
from urllib.request import Request, urlopen

from server.atlantean_server import AtlanteanProdServer


class AtlanteanServerTestCase(unittest.TestCase):
    """Start the HTTP service on a background thread and exercise the API."""

    @classmethod
    def setUpClass(cls) -> None:  # noqa: D401 - unittest API
        cls.tmp_db = Path("tests/.tmp_atlantean.sqlite")
        cls.tmp_db.parent.mkdir(parents=True, exist_ok=True)
        cls.address = cls._free_port()
        cls.server = AtlanteanProdServer(cls.address, cls.tmp_db)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        # Wait for server to be ready
        time.sleep(0.2)

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
    def _request(self, method: str, path: str, payload: dict | None = None) -> tuple[int, dict]:
        data = None
        headers = {"Content-Type": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
        req = Request(
            f"http://{self.address[0]}:{self.address[1]}{path}",
            data=data,
            method=method,
            headers=headers,
        )
        with urlopen(req) as response:  # noqa: S310 - test utility
            body = response.read().decode("utf-8")
            return response.status, json.loads(body)

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
            )
            self.assertEqual(status, 201)
            self.assertEqual(payload["status"], "recorded")

        status, payload = self._request("GET", "/api/v1/ladder/top?limit=5")
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
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["status"], "recorded")

        status, payload = self._request("GET", "/api/v1/ledger/TestPilot")
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
        )
        self.assertEqual(status, 201)
        self.assertEqual(payload["status"], "recorded")

        status, payload = self._request("GET", "/api/v1/telemetry/export?limit=10")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(payload["events"]), 1)
        self.assertEqual(payload["events"][0]["event_type"], "match_start")


if __name__ == "__main__":  # pragma: no cover
    unittest.main()

