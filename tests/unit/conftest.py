"""Shared test fixtures: one aimock server per session (offline, keyless)."""

import shutil
import socket
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def aimock_port() -> Iterator[int]:
    """Start aimock on an ephemeral port; skip cleanly when not installed."""
    if not shutil.which("aimock"):
        pytest.skip("aimock not installed")
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
    proc = subprocess.Popen(
        ["aimock", "-c", "aimock/aimock.json", "-p", str(port)],
        cwd=PROJECT_ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                break
        except OSError:
            time.sleep(0.2)
    else:
        proc.terminate()
        pytest.skip("aimock server did not become ready")
    yield port
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
