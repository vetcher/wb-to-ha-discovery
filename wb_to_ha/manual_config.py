import json
import logging
import re
from typing import Any
import yaml

logger = logging.getLogger(__name__)

# A lot of strange hacks to make yaml output expected.
# https://stackoverflow.com/questions/47542343/how-to-print-a-value-with-double-quotes-and-spaces-in-yaml

# Hack for double quotes for values in yaml.
_yaml_cached_dict_keys: set[str] = set()

def mk_double_quote(dumper, data):
    if data in _yaml_cached_dict_keys:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='')
    else:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')

yaml.add_representer(str, mk_double_quote)

def update_yaml_cached_dict_keys(msg: dict[str, Any]):
    _yaml_cached_dict_keys.update(msg.keys())
    for v in msg.values():
        if isinstance(v, dict):
            update_yaml_cached_dict_keys(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, dict):
                    update_yaml_cached_dict_keys(item)

# Hack to increase indent for lists.
class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        return super(IndentDumper, self).increase_indent(flow, False)

class ManualConfigService:
    _config_topic_re = re.compile(r'^homeassistant/([^/]+)/([^/]+)/([^/]+)/config$')
    _availability_topic_re = re.compile(r'^(.+)/controls/([^/]+)/availability$')

    def convert_mqtt_topics_messages_to_manual_config(
        self,
        topics_messages: dict[str, str],
    ) -> dict[str, Any]:
        device_types = {}
        for topic, message in topics_messages.items():
            match = self._config_topic_re.match(topic)
            if not match:
                continue
            device_type = match.group(1)
            if device_type not in device_types:
                device_types[device_type] = []
            msg = json.loads(message)
            msg = self._preprocess_for_manual_config(device_type, msg)

            update_yaml_cached_dict_keys(msg)
            # sort by unique_id to make output deterministic
            prev_entities = device_types[device_type]
            prev_entities.append(msg)
            prev_entities.sort(key=lambda x: x['unique_id'])
            device_types[device_type] = prev_entities
        result = {
            "mqtt": device_types,
        }
        update_yaml_cached_dict_keys(result)
        return result

    def _preprocess_for_manual_config(self, device_type: str, msg: dict[str, Any]) -> dict[str, Any]:
        if device_type in ['button', 'switch']:
            # Force retain because when config sets up via yaml availability topic not used.
            msg['retain'] = True
        del msg['availability_topic']
        del msg['payload_available']
        del msg['payload_not_available']
        return msg

def dict_to_yaml(d: dict[str, Any]) -> str:
    update_yaml_cached_dict_keys(d)
    return yaml.dump(d, allow_unicode=True, Dumper=IndentDumper)