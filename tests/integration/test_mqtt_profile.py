import asyncio

import pytest

from experiments.mqtt_clients import run_profile

pytestmark = pytest.mark.mqtt


def test_profile_counts_real_connections_and_payloads():
    report = asyncio.run(run_profile(10, 2))
    assert report["connected_clients"] == 10
    assert report["broker_connected_clients"] >= 11  # Includes the metrics observer.
    assert report["verified_deliveries"] == 20
    assert report["new_threads"] == 0
    assert report["transport"] == "plaintext-loopback"
    assert report["sampled_peak_rss_bytes"] > 0
