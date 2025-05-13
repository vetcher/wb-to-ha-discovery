import asyncio
import json
import optparse
import logging
import signal
import yaml
from voluptuous import MultipleInvalid
from aiohttp import web

from wb_to_ha import handlers
from wb_to_ha.config import config_schema_builder, LOGLEVEL_MAPPER
from wb_to_ha.homeassistant import HomeAssistantDiscoveryCustomizer
from gmqtt.client import Client as MQTTClient
from wb_to_ha.app import App
from wb_to_ha.manual_config import ManualConfigService
from wb_to_ha.mqtt.conn.inmem_mqtt import InmemMQTTClient

logging.getLogger().setLevel(logging.INFO)  # root

logger = logging.getLogger(__name__)

def main(cfg):
    logging.basicConfig(
        level=LOGLEVEL_MAPPER[cfg["general.loglevel"]],
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("gmqtt").setLevel(LOGLEVEL_MAPPER[cfg["mqtt.loglevel"]])

    wb_cfg = cfg["wirenboard"]
    ha_cfg = cfg["homeassistant"] if "homeassistant" in cfg else {}

    logger.info("Starting")
    wb_mqtt_client = MQTTClient(client_id=wb_cfg["mqtt_client_id"])
    if wb_cfg.get('username') and wb_cfg.get('password'):
        wb_mqtt_client.set_auth_credentials(
            wb_cfg["username"],
            wb_cfg["password"]
        )
    ha_mqtt_client = InmemMQTTClient()
    ha_customizer = HomeAssistantDiscoveryCustomizer(
        splitted_device_ids=cfg["homeassistant.splitted_device_ids"],
        combined_devices=cfg["homeassistant.combined_devices"],
        ignored_device_ids=cfg["homeassistant.ignored_device_ids"],
        ignored_device_control_ids=cfg["homeassistant.ignored_device_control_ids"],
        enable_default_combined_devices=cfg["homeassistant.enable_default_combined_devices"],
    )

    manual_config_service = ManualConfigService()
    handlers_service = handlers.HTTPService(manual_config_service, ha_mqtt_client)
    app = App(ha_cfg, wb_cfg, ha_mqtt_client, wb_mqtt_client, ha_customizer)

    loop = asyncio.get_event_loop()

    async def stop_app(*arg):
        asyncio.create_task(app.stop())

    async def run_app(*arg):
        asyncio.create_task(app.run())

    wapp = web.Application()
    wapp.on_startup.append(run_app)
    wapp.on_shutdown.append(stop_app)
    wapp.add_routes([
        web.get('/api/wb_to_ha.yaml', handlers_service.wb_to_ha_yaml),
        web.get('/', handlers_service.index),
        web.static('/', 'frontend')
    ])
    web.run_app(wapp, host='0.0.0.0', port=8099, loop=loop)

if __name__ == "__main__":
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config", default="/data/options.json", dest="config_file", help="Path to config file. In YAML or JSON format")
    opts, args = parser.parse_args()

    config_file = opts.config_file
    logger.info(f"Initializing with config file: {config_file}")
    if not config_file:
        parser.print_help()
        exit(1)

    try:
        with open(config_file) as f:
            config_file_content = f.read()
    except OSError as e:
        logger.error(f'Could not open config file "{config_file}: {e}"')
        exit(1)

    config = None
    if config_file.endswith(".json"):
        config = json.loads(config_file_content)
    elif config_file.endswith(".yaml") or config_file.endswith(".yml"):
        config = yaml.load(config_file_content, Loader=yaml.FullLoader)
    else:
        logger.error(f'Unsupported config file extension: "{config_file}"')
        exit(1)
    if not config:
        logger.error(f'Empty config "{config_file}"')
        exit(1)

    try:
        config = config_schema_builder(vars(opts))(config)
    except MultipleInvalid as e:
        logger.error(f"Config validation error: {e}")
        exit(1)

    main(config)