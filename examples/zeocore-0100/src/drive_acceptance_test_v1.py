"""Offline behavioral tests of live acceptance classification; no live credentials."""
from __future__ import annotations

import argparse
import hashlib
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import httpx
from zeo_core.integrations.hosted.pairing import InMemorySecureSessionStore
from zeo_core.integrations.hosted.transport import ZEOCONNECT_PRODUCTION_ORIGIN

import drive_live_acceptance_v1 as acceptance
from drive_profiles_v1 import CONTENT, OPERATION


class AcceptanceTest(unittest.TestCase):
    def run_case(self, *, revoke_status: int = 401, expected_digest: str | None = None) -> tuple[dict[str, object], InMemorySecureSessionStore]:
        store = InMemorySecureSessionStore()
        revoked = False
        expires = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
        session = {"device_id": "device-fixture", "access_token": "synthetic-access",
            "refresh_token": "synthetic-refresh", "access_expires_at": expires, "refresh_expires_at": expires}
        statuses: list[int] = []

        def handle(request: httpx.Request) -> httpx.Response:
            nonlocal revoked
            path = request.url.path
            headers = {"ZEOconnect-Protocol-Version": "1"}
            if path == "/v1/device/authorizations":
                document = {"pairing_id": "pair-fixture", "device_code": "synthetic-device",
                    "verification_url": ZEOCONNECT_PRODUCTION_ORIGIN + "/device", "user_code": "TEST1234",
                    "expires_at": expires, "interval_seconds": 1}
            elif path in {"/v1/device/token", "/v1/device/token/refresh"}:
                document = session
            elif path == "/v1/connections":
                document = [{"connection_id": "con_fixture12345678", "provider": "google", "external_identity": "fixture@example.invalid",
                    "status": "active", "operations": [OPERATION], "resources": [{"external_id": "selected", "display_name": "Test CSV", "media_type": "text/csv", "operations": [OPERATION]}]}]
            elif path == "/v1/device/revoke":
                revoked = True
                return httpx.Response(204, headers=headers)
            elif path == "/v1/operations/" + OPERATION + ":invoke":
                if revoked:
                    statuses.append(revoke_status)
                    return httpx.Response(revoke_status, headers=headers, json={"error": "refused"})
                document = {"status": "confirmed", "execution_id": "execution-fixture", "artifact": {
                    "artifact_id": "art_fixture12345678", "content_sha256": "sha256:" + hashlib.sha256(CONTENT).hexdigest(),
                    "size_bytes": len(CONTENT), "media_type": "text/csv", "filename": "selected.csv"}}
            elif path == "/v1/artifacts/art_fixture12345678":
                return httpx.Response(200, headers=headers, content=CONTENT)
            else:
                raise AssertionError("unexpected endpoint")
            return httpx.Response(200, headers=headers, json=document)

        real_client = httpx.Client

        def client(**kwargs: object) -> httpx.Client:
            return real_client(transport=httpx.MockTransport(handle), **kwargs)

        args = argparse.Namespace(connection="con_fixture12345678", file_id="selected",
            expected_sha256=expected_digest or hashlib.sha256(CONTENT).hexdigest(), expected_total=10)
        with patch.object(acceptance, "integration_mode", return_value="test"), patch.object(acceptance, "integration_backend", return_value="live"), patch.object(acceptance, "managed_state_dir", return_value=Path.cwd() / "test"), patch.object(acceptance, "KeychainSecureSessionStore", return_value=store), patch.object(acceptance.httpx, "Client", side_effect=client):
            result = acceptance.execute(args)
        assert statuses == [401]
        return result, store

    def test_full_flow_and_revoked_custody_deleted(self) -> None:
        result, store = self.run_case()
        self.assertEqual(result["total"], 10)
        self.assertIsNone(store.load())
        self.assertNotIn("synthetic-", str(result))

    def test_server_failure_cannot_pass_as_revocation(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "server 401"):
            self.run_case(revoke_status=503)

    def test_independent_digest_mismatch_refuses(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "independently"):
            self.run_case(expected_digest="0" * 64)

    def test_default_environment_never_starts_live_flow(self) -> None:
        with patch.object(acceptance, "integration_mode", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "explicit test/live"):
                acceptance.execute(argparse.Namespace())


if __name__ == "__main__":
    unittest.main()
