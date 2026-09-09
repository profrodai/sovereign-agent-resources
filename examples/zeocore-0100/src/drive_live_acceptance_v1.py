"""Explicit live pair/read/digest/rotate/revoke/refuse acceptance; never a smoke."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import httpx
from zeo_core.integrations.environment import integration_backend, integration_mode, managed_state_dir
from zeo_core.integrations.hosted import HostedConnectionClient, HostedOperationRequest, HostedOperationStatus
from zeo_core.integrations.hosted.client import HostedClientError
from zeo_core.integrations.hosted.pairing import HostedConnectionManager, KeychainSecureSessionStore, PairingPendingError
from zeo_core.integrations.hosted.profile import HostedConnectionStatus
from zeo_core.integrations.hosted.transport import (
    ZEOCONNECT_PRODUCTION_ORIGIN, ZEOCONNECT_PROTOCOL_HEADER, ZEOconnectHTTPTransport,
)
from drive_profiles_v1 import OPERATION, REQUIREMENT


def execute(args: argparse.Namespace) -> dict[str, object]:
    if integration_mode() != "test" or integration_backend() != "live" or managed_state_dir() is None:
        raise RuntimeError("requires explicit test/live integration environment and private test state directory")
    if re.fullmatch(r"[0-9a-f]{64}", args.expected_sha256) is None:
        raise RuntimeError("expected digest must be independent SHA256 of the designated CSV")
    store = KeychainSecureSessionStore()
    if store.load() is not None:
        raise RuntimeError("use an unused test state namespace; existing paired authority is preserved")
    observations: list[tuple[str, str, int, str | None]] = []

    def observed(response: httpx.Response) -> None:
        observations.append((response.request.method, response.request.url.path,
            response.status_code, response.headers.get(ZEOCONNECT_PROTOCOL_HEADER)))

    with httpx.Client(base_url=ZEOCONNECT_PRODUCTION_ORIGIN, timeout=30, follow_redirects=False,
        event_hooks={"response": [observed]}) as http:
        transport = ZEOconnectHTTPTransport(session_store=store, http_client=http)
        manager = HostedConnectionManager(transport=transport, session_store=store)
        challenge = manager.begin_pairing(REQUIREMENT, device_name="designated-drive-acceptance")
        print("Complete designated test pairing:", challenge.verification_url, challenge.user_code, flush=True)
        deadline = min(challenge.expires_at.timestamp(), time.time() + 600)
        while True:
            if time.time() >= deadline:
                raise RuntimeError("pairing expired; no provider operation was requested")
            try:
                catalog = manager.complete_pairing(challenge)
                break
            except PairingPendingError:
                time.sleep(challenge.polling_interval_seconds)
        matches = [item for item in catalog if item.handle.value == args.connection]
        if len(matches) != 1:
            raise RuntimeError("designated connection was not paired")
        selected = matches[0]
        if selected.status != HostedConnectionStatus.ACTIVE or not selected.satisfies(REQUIREMENT):
            raise RuntimeError("designated connection is not active for Drive read")
        if not any(resource.external_id == args.file_id and OPERATION in resource.operations for resource in selected.resources):
            raise RuntimeError("designated CSV was not selected in the browser")
        client = HostedConnectionClient(transport=transport)
        request = HostedOperationRequest(connection_id=args.connection, operation_id=OPERATION,
            arguments={"file_id": args.file_id}, idempotency_key="acceptance-" + uuid.uuid4().hex)
        answer = client.invoke(request)
        if answer.status != HostedOperationStatus.CONFIRMED or answer.artifact is None:
            raise RuntimeError("designated read was not confirmed with an artifact")
        content = client.download_artifact(answer.artifact)
        digest = hashlib.sha256(content).hexdigest()
        if digest != args.expected_sha256:
            raise RuntimeError("download differs from independently supplied expected digest")
        # Validate the same business input without persisting provider content in evidence.
        with TemporaryDirectory(prefix="drive-acceptance-", dir=Path.cwd()) as directory:
            target = Path(directory) / "selected.csv"
            target.write_bytes(content)
            import csv
            with target.open(newline="") as stream:
                total = sum(int(row["amount"]) for row in csv.DictReader(stream))
            if total != args.expected_total:
                raise RuntimeError("designated CSV total differs from expectation")
        manager.refresh_session()
        session = store.load()
        if session is None:
            raise RuntimeError("rotated session was not stored securely")
        # Keep revoked authority confined to Keychain until the real server refusal probe.
        transport.revoke_device(session)
        before = len(observations)
        try:
            probe = request.model_copy(update={"idempotency_key": "revoked-" + uuid.uuid4().hex})
            client.invoke(probe)
        except HostedClientError:
            observed_probe = observations[before:]
            if not observed_probe or observed_probe[-1] != (
                "POST", "/v1/operations/" + OPERATION + ":invoke", 401, "1",
            ):
                raise RuntimeError("revocation not proved by authenticated server 401") from None
        else:
            raise RuntimeError("revoked device operation was not refused")
        finally:
            # Deletion follows confirmed revoke; pre-revoke failures retain custody for repair.
            store.delete()
        return {"observed_at": datetime.now(UTC).isoformat(), "status": "LIVE_ACCEPTANCE_PASSED",
            "artifact_sha256": digest, "artifact_bytes": len(content), "total": total,
            "pairing": "completed", "selection": "exact connection and file",
            "rotation": "completed", "revocation": "server 401 with protocol 1",
            "production_readiness": "not established beyond this designated test"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-live", action="store_true", required=True,
        help="explicitly authorize a new test pairing, selected CSV read and device revocation")
    parser.add_argument("--connection", required=True, help="designated opaque con_ handle")
    parser.add_argument("--file-id", required=True, help="designated browser-selected test CSV")
    parser.add_argument("--expected-sha256", required=True, help="digest obtained independently before the run")
    parser.add_argument("--expected-total", required=True, type=int)
    args = parser.parse_args()
    try:
        receipt = execute(args)
    except Exception:
        raise SystemExit("ACCEPTANCE_INCOMPLETE: no live pass claimed; inspect pairing or deployment state") from None
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    main()
