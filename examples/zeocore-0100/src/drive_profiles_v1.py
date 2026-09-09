"""One unchanged business function over fake, injected-local and hosted profiles."""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Protocol

from pydantic import SecretStr
from zeo_core.integrations.core import IntegrationResult
from zeo_core.integrations.hosted import (
    ExecutionProfile, FakeGoogleDriveService, HostedConnectionClient,
    HostedOperationRequest, HostedOperationResponse, HostedOperationStatus,
    Ready, ServiceRequirement, ServiceResolver,
)
from zeo_core.integrations.hosted.client import HostedArtifactDescriptor
from zeo_core.integrations.hosted.pairing import DeviceSession, InMemorySecureSessionStore
from zeo_core.integrations.hosted.profile import (
    ConnectionRequired, ConnectionSelectionRequired, HostedConnectionStatus,
    HostedConnectionSummary, HostedResourceSummary, OpaqueConnectionHandle,
    ResourceSelectionRequired,
)

CONTENT = b"amount\n2\n3\n5\n"
OPERATION = "google.drive.file.download"
REQUIREMENT = ServiceRequirement(service="google.drive", operations=(OPERATION,))


class DrivePort(Protocol):
    def initialize(self) -> IntegrationResult[None]: ...
    def download_file(self, remote_id: str, local_path: str | None = None) -> IntegrationResult[str]: ...


def read_selected_total(service: DrivePort, destination: Path, file_id: str = "selected") -> int:
    """Business logic has no profile, pairing, token or provider configuration."""
    if not service.initialize().success:
        raise RuntimeError("Drive initialization refused")
    result = service.download_file(file_id, str(destination))
    if not result.success:
        raise RuntimeError("Selected Drive read refused")
    import csv
    with destination.open(newline="") as stream:
        return sum(int(row["amount"]) for row in csv.DictReader(stream))


class FixtureTransport:
    """Injected hosted boundary; implements no network and accepts one selected file."""
    def __init__(self) -> None:
        self.calls: list[HostedOperationRequest] = []

    def invoke(self, request: HostedOperationRequest) -> HostedOperationResponse:
        if request.operation_id != OPERATION or request.arguments != {"file_id": "selected"}:
            raise RuntimeError("unselected operation or resource")
        if request.connector_revision is not None:
            raise RuntimeError("revision must remain server-owned")
        self.calls.append(request)
        return HostedOperationResponse(
            status=HostedOperationStatus.CONFIRMED, execution_id="observation-fixture",
            artifact=HostedArtifactDescriptor(
                artifact_id="art_fixture12345678", content_sha256="sha256:" + hashlib.sha256(CONTENT).hexdigest(),
                size_bytes=len(CONTENT), media_type="text/csv", filename="selected.csv",
            ),
        )

    def fetch_artifact(self, *, artifact_id: str, max_bytes: int) -> bytes:
        if artifact_id != "art_fixture12345678" or max_bytes != len(CONTENT):
            raise RuntimeError("artifact binding mismatch")
        return CONTENT


def main() -> None:
    store = InMemorySecureSessionStore()
    boundary = FixtureTransport()
    hosted = ServiceResolver(profile=ExecutionProfile.HOSTED,
        hosted_client=HostedConnectionClient(transport=boundary), session_store=store,
        hosted_connections=())
    assert isinstance(hosted.resolve(REQUIREMENT), ConnectionRequired)
    now = datetime.now(UTC)
    store.save(DeviceSession(device_id="fixture-device", access_token=SecretStr("synthetic-access"),
        refresh_token=SecretStr("synthetic-refresh"), access_expires_at=now+timedelta(minutes=5),
        refresh_expires_at=now+timedelta(minutes=10)))
    assert isinstance(hosted.resolve(REQUIREMENT), ConnectionRequired)
    connection = HostedConnectionSummary(handle=OpaqueConnectionHandle(value="con_fixture12345678"),
        service="google.drive", external_identity="fixture@example.invalid",
        status=HostedConnectionStatus.ACTIVE, operations=(OPERATION,), resources=())
    hosted.replace_hosted_connections((connection,))
    assert isinstance(hosted.resolve(REQUIREMENT), ResourceSelectionRequired)
    selected = connection.model_copy(update={"resources": (HostedResourceSummary(
        external_id="selected", display_name="Selected CSV", media_type="text/csv", operations=(OPERATION,),
    ),)})
    other = selected.model_copy(update={"handle": OpaqueConnectionHandle(value="con_other12345678")})
    hosted.replace_hosted_connections((selected, other))
    assert isinstance(hosted.resolve(REQUIREMENT), ConnectionSelectionRequired)
    assert boundary.calls == []
    profiles = (
        ("fake", ServiceResolver(profile=ExecutionProfile.FAKE, fake_services={"google.drive": FakeGoogleDriveService({"selected": CONTENT})})),
        ("local", ServiceResolver(profile=ExecutionProfile.LOCAL, local_services={"google.drive": FakeGoogleDriveService({"selected": CONTENT})})),
        ("hosted", hosted),
    )
    with TemporaryDirectory(prefix="drive-profiles-", dir=Path.cwd()) as temporary:
        for name, resolver in profiles:
            resolved = resolver.resolve(REQUIREMENT, connection=selected.handle)
            if not isinstance(resolved, Ready):
                raise RuntimeError(f"{name} did not resolve")
            destination = Path(temporary)/f"{name}.csv"
            if read_selected_total(resolved.service, destination) != 10 or destination.read_bytes() != CONTENT:
                raise RuntimeError(f"{name} produced incorrect data")
            print(f"PASS {name}: unchanged business function total=10")
        assert len(boundary.calls) == 1
        assert str(temporary) not in boundary.calls[0].model_dump_json()
    print("PASS empty catalog, multiple connections and missing resource refuse without dispatch")
    print("OFFLINE: local service and hosted transport injected; no account or network")


if __name__ == "__main__":
    main()
