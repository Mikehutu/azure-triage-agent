"""Shared fixtures for live end-to-end practical tests.

Spins up a real aimock server and a real FastAPI uvicorn instance in separate
processes communicating over real TCP sockets (zero internal dependency overrides).
"""

import os
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from pathlib import Path

import httpx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _get_free_port() -> int:
    """Acquire an ephemeral port bound to 127.0.0.1."""
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_for_port(port: int, timeout: float = 15.0) -> bool:
    """Wait until a local port accepts TCP connections."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return True
        except OSError:
            time.sleep(0.15)
    return False


@pytest.fixture(scope="session")
def live_services() -> Iterator[dict[str, str | int]]:
    """Start live aimock and uvicorn processes on ephemeral ports."""
    if not shutil.which("aimock"):
        pytest.skip("aimock CLI not found on PATH; skipping live e2e tests")

    aimock_port = _get_free_port()
    api_port = _get_free_port()

    aimock_proc = subprocess.Popen(
        ["aimock", "-c", "aimock/aimock.json", "-p", str(aimock_port)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _wait_for_port(aimock_port, timeout=15.0):
        aimock_proc.terminate()
        pytest.skip(f"aimock server failed to start on port {aimock_port}")

    env = os.environ.copy()
    env["AZURE_TRIAGE_MOCK"] = "1"
    env["AZURE_TRIAGE_AZURE_OPENAI_ENDPOINT"] = f"http://127.0.0.1:{aimock_port}"
    env["AZURE_TRIAGE_REQUEST_TIMEOUT_SECONDS"] = "5.0"

    api_proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "src.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(api_port),
            "--log-level",
            "warning",
        ],
        cwd=PROJECT_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    api_base_url = f"http://127.0.0.1:{api_port}"
    deadline = time.time() + 15.0
    ready = False

    while time.time() < deadline:
        try:
            resp = httpx.get(f"{api_base_url}/healthz", timeout=1.0)
            if resp.status_code == 200:
                ready = True
                break
        except (httpx.ConnectError, httpx.TimeoutException):
            time.sleep(0.2)

    if not ready:
        api_proc.terminate()
        aimock_proc.terminate()
        pytest.skip(f"FastAPI uvicorn server failed to become healthy on port {api_port}")

    yield {
        "api_url": api_base_url,
        "api_port": api_port,
        "aimock_port": aimock_port,
    }

    # Teardown processes gracefully
    for proc in (api_proc, aimock_proc):
        proc.terminate()
        try:
            proc.wait(timeout=3.0)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture(scope="session")
def api_client(live_services: dict[str, str | int]) -> Iterator[httpx.Client]:
    """Provide an HTTP client configured to talk to the live API server."""
    base_url = str(live_services["api_url"])
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        yield client
