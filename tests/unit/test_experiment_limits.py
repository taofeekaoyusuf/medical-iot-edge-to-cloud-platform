import asyncio

import pytest

from experiments.mqtt_clients import run_profile


@pytest.mark.parametrize("count", [0, -1, 1001, True, 1.5])
def test_connection_profile_rejects_unsafe_counts_before_network_access(count):
    with pytest.raises(ValueError, match="clients"):
        asyncio.run(run_profile(count))


@pytest.mark.parametrize("rounds", [0, -1, 21, True, 1.5])
def test_connection_profile_rejects_unbounded_rounds(rounds):
    with pytest.raises(ValueError, match="rounds"):
        asyncio.run(run_profile(1, rounds))
