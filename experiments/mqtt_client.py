"""Small localhost-only Paho adapter driven by one asyncio event loop.

This is feasibility code, not the production reconnect/buffering implementation.
Paho socket callbacks register readiness with asyncio; loop_start is never used.
"""

import asyncio

import paho.mqtt.client as mqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.properties import Properties


class LocalClient:
    def __init__(self, client_id: str, *, port: int = 18883, manual_ack: bool = False):
        if port != 18883:
            raise ValueError("Stage 3 permits only the dedicated loopback port 18883")
        self.loop = asyncio.get_running_loop()
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=client_id,
            protocol=mqtt.MQTTv5,
            manual_ack=manual_ack,
            reconnect_on_failure=False,
        )
        self.client.on_socket_open = self._socket_open
        self.client.on_socket_close = self._socket_close
        self.client.on_socket_register_write = self._register_write
        self.client.on_socket_unregister_write = self._unregister_write
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_subscribe = self._on_subscribe
        self.client.on_publish = self._on_publish
        self.client.max_queued_messages_set(20)
        self.client.max_inflight_messages_set(20)
        self.client.connect_timeout = 2.0
        self.connected = False
        self._connected = self.loop.create_future()
        self._disconnected = self.loop.create_future()
        self._subscriptions = {}
        self._publications = {}
        self._messages = asyncio.Queue(maxsize=100)
        self._overflow = False
        self._timer = None
        self._closed = False
        self._started = False
        self.port = port

    def _socket_open(self, client, userdata, sock):
        self.loop.add_reader(sock.fileno(), client.loop_read)

    def _socket_close(self, client, userdata, sock):
        self.loop.remove_reader(sock.fileno())
        self.loop.remove_writer(sock.fileno())

    def _register_write(self, client, userdata, sock):
        self.loop.add_writer(sock.fileno(), client.loop_write)

    def _unregister_write(self, client, userdata, sock):
        self.loop.remove_writer(sock.fileno())

    def _on_connect(self, client, userdata, flags, reason_code, properties):
        if self._connected.done():
            return
        if reason_code.is_failure:
            self._connected.set_exception(ConnectionError(str(reason_code)))
        else:
            self.connected = True
            self._connected.set_result(flags.session_present)

    def _on_disconnect(self, client, userdata, flags, reason_code, properties):
        self.connected = False
        if not self._disconnected.done():
            self._disconnected.set_result(None)

    def _on_message(self, client, userdata, message):
        try:
            self._messages.put_nowait(message)
        except asyncio.QueueFull:
            self._overflow = True
            client.disconnect()  # Abort the experiment visibly rather than grow memory.

    def _on_subscribe(self, client, userdata, mid, reason_codes, properties):
        future = self._subscriptions.pop(mid, None)
        if future is not None and not future.done():
            if any(code.is_failure for code in reason_codes):
                future.set_exception(ConnectionError("Subscription rejected"))
            else:
                future.set_result(None)

    def _on_publish(self, client, userdata, mid, reason_code, properties):
        future = self._publications.pop(mid, None)
        if future is not None and not future.done():
            if reason_code.is_failure:
                future.set_exception(ConnectionError("Publish rejected"))
            else:
                future.set_result(None)

    def _misc(self):
        self.client.loop_misc()
        if not self._closed:
            self._timer = self.loop.call_later(1.0, self._misc)

    async def connect(self, *, clean_start: bool = True) -> bool:
        if self._started:
            raise RuntimeError("Use a new adapter to resume a broker session")
        self._started = True
        properties = Properties(PacketTypes.CONNECT)
        properties.SessionExpiryInterval = 60
        # Synchronous TCP establishment is bounded to localhost and a 2-second timeout.
        # All subsequent socket I/O and keepalive use the shared event loop.
        self.client.connect(
            "127.0.0.1",
            self.port,
            keepalive=30,
            clean_start=clean_start,
            properties=properties,
        )
        self._timer = self.loop.call_later(1.0, self._misc)
        return await asyncio.wait_for(self._connected, timeout=5)

    async def subscribe(self, topic: str) -> None:
        result, mid = self.client.subscribe(topic, qos=1)
        if result != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(mqtt.error_string(result))
        future = self.loop.create_future()
        self._subscriptions[mid] = future
        try:
            await asyncio.wait_for(future, timeout=5)
        finally:
            self._subscriptions.pop(mid, None)

    async def publish(self, topic: str, payload: bytes) -> None:
        info = self.client.publish(topic, payload, qos=1)
        if info.rc != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(mqtt.error_string(info.rc))
        future = self.loop.create_future()
        self._publications[info.mid] = future
        try:
            await asyncio.wait_for(future, timeout=5)
        finally:
            self._publications.pop(info.mid, None)

    async def receive(self):
        if self._overflow:
            raise RuntimeError("Experiment receive queue overflowed")
        return await asyncio.wait_for(self._messages.get(), timeout=5)

    def ack(self, message) -> None:
        result = self.client.ack(message.mid, message.qos)
        if result != mqtt.MQTT_ERR_SUCCESS:
            raise ConnectionError(mqtt.error_string(result))

    async def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._timer is not None:
            self._timer.cancel()
        if self.client.socket() is not None:
            self.client.disconnect()
            await asyncio.wait_for(self._disconnected, timeout=3)
