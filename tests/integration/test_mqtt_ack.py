"""Real broker tests: missing broker is a failure, never an automatic skip."""

import asyncio
from uuid import uuid4

import pytest

from experiments.mqtt_client import LocalClient

pytestmark = pytest.mark.mqtt


def test_unacknowledged_delivery_replays_on_persistent_session_reconnect():
    async def scenario():
        suffix = uuid4().hex
        topic = f"stage3/{suffix}"
        subscriber = LocalClient(f"sub-{suffix}", manual_ack=True)
        publisher = LocalClient(f"pub-{suffix}")
        replay = None
        acknowledged = None
        try:
            assert await subscriber.connect() is False
            await subscriber.subscribe(topic)
            await publisher.connect()
            await publisher.publish(topic, b"same-event-id")
            first = await subscriber.receive()
            assert first.payload == b"same-event-id"
            assert first.qos == 1
            # Close without application ACK: the broker must preserve this pending delivery.
            await subscriber.close()
            replay = LocalClient(f"sub-{suffix}", manual_ack=True)
            assert await replay.connect(clean_start=False) is True
            second = await replay.receive()
            assert second.payload == first.payload
            assert second.mid == first.mid
            assert second.dup is True
            replay.ack(second)
            # A subsequent delivered marker proves the connection remains usable after ACK.
            await publisher.publish(topic, b"barrier")
            barrier = await replay.receive()
            replay.ack(barrier)
            await replay.close()
            acknowledged = LocalClient(f"sub-{suffix}", manual_ack=True)
            assert await acknowledged.connect(clean_start=False) is True
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(acknowledged.receive(), timeout=0.3)
        finally:
            for client in [subscriber, publisher, replay, acknowledged]:
                if client is not None:
                    await client.close()

    asyncio.run(scenario())


def test_acknowledged_delivery_is_not_replayed():
    async def scenario():
        suffix = uuid4().hex
        topic = f"stage3/{suffix}"
        subscriber = LocalClient(f"sub-{suffix}", manual_ack=True)
        publisher = LocalClient(f"pub-{suffix}")
        resumed = None
        try:
            await subscriber.connect()
            await subscriber.subscribe(topic)
            await publisher.connect()
            await publisher.publish(topic, b"committed")
            subscriber.ack(await subscriber.receive())
            await subscriber.close()
            resumed = LocalClient(f"sub-{suffix}", manual_ack=True)
            assert await resumed.connect(clean_start=False) is True
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(resumed.receive(), timeout=0.3)
        finally:
            for client in [subscriber, publisher, resumed]:
                if client is not None:
                    await client.close()

    asyncio.run(scenario())
