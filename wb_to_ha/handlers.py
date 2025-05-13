import asyncio
from typing import Coroutine
import uuid
from aiohttp import web

from wb_to_ha import manual_config
from wb_to_ha.manual_config import ManualConfigService
from wb_to_ha.mqtt.conn.inmem_mqtt import InmemMQTTClient

class HTTPService(web.View):
    cfg_service: ManualConfigService
    mqtt_client: InmemMQTTClient

    def __init__(self, cfg_service: ManualConfigService, mqtt_client: InmemMQTTClient):
        self.cfg_service = cfg_service
        self.mqtt_client = mqtt_client

    async def index(self, request: web.Request):
        raise web.HTTPFound('/index.html')

    async def wb_to_ha_yaml(self, request: web.Request):
        d = self.cfg_service.convert_mqtt_topics_messages_to_manual_config(self.mqtt_client.last_messages)
        resp = manual_config.dict_to_yaml(d)
        return web.Response(text=resp)
