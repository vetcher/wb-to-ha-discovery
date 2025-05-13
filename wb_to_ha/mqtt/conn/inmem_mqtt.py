import asyncio
import json
import os
from typing import Callable
import re
import logging

logger = logging.getLogger(__name__)

class InmemMQTTClient:
    on_message: Callable | None
    on_disconnect: Callable | None
    on_connect: Callable | None

    _last_messages: dict[str, str]

    def __init__(self):
        self._last_messages = {}
        self.on_disconnect = None
        self.on_connect = None
        self.on_message = None

    def subscribe(self, topic: str, qos: int = 0):
        # do noop because this implementation is't supposed to subscribe to anything
        pass

    def publish(self, topic: str, payload: str, qos: int = 0, retain: bool = False):
        self._last_messages[topic] = payload
        if self.on_message is not None:
            self.on_message(self, topic, payload, qos, retain)

    async def connect(self, *args, **kwargs):
        if self.on_connect is not None:
            self.on_connect(self)

    async def disconnect(self):
        if self.on_disconnect is not None:
            await self.on_disconnect(None, None)

    @property
    def last_messages(self) -> dict[str, str]:
        return self._last_messages
