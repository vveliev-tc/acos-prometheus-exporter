import json
from threading import Lock

import prometheus_client
from prometheus_client import Gauge

from src.acos_client.client import ACOSClient

UNDERSCORE = "_"
SLASH = "/"
HYPHEN = "-"
PLUS = "+"

API_TIMEOUT = 5

global_api_collection = dict()
global_stats = dict()

_INF = float("inf")

lock1 = Lock()
tokens = dict()

def getLabelNameFromA10URL(api_list):
    if type(api_list) == list:
        empty_list = list()
        for api in api_list:
            labelName = api.replace(SLASH, UNDERSCORE)
            labelName = labelName.replace(HYPHEN, UNDERSCORE)
            labelName = labelName.replace(PLUS, UNDERSCORE)
            empty_list.append(labelName)
        return empty_list
    else:
        labelName = api_list.replace(SLASH, UNDERSCORE)
        labelName = labelName.replace(HYPHEN, UNDERSCORE)
        labelName = labelName.replace(PLUS, UNDERSCORE)
        return labelName

def generate_metrics(resp_data, api_name, partition, host_ip, key, res, metric_prefix=""):
    api = str(api_name)
    if api.startswith("_"):
        api = api[1:]

    current_api_stats = dict()
    if api in global_api_collection:
        current_api_stats = global_api_collection[api]
        # This section maintains local dictionary  of stats or rate fields against Gauge objects.
        # Code handles the duplication of key_name in time series database
        # by referring the global dictionary of key_name and Gauge objects.
    for key in resp_data:
        org_key = key
        if HYPHEN in key:
            key = key.replace(HYPHEN, UNDERSCORE)
        metric_name = metric_prefix + "_" + key
        if metric_name not in global_stats:
            current_api_stats[metric_name] = Gauge(metric_name, "api-" + api + " key-" + key,
                                                   labelnames=(["api_name", "partition", "host"]), )
            current_api_stats[metric_name].labels(api_name=api, partition=partition, host=host_ip).set(resp_data[org_key])
            global_stats[metric_name] = current_api_stats[metric_name]
        elif metric_name in global_stats:
            global_stats[metric_name].labels(api_name=api, partition=partition, host=host_ip).set(resp_data[org_key])

    global_api_collection[api] = current_api_stats

    for name in global_api_collection[api]:
        res.append(prometheus_client.generate_latest(global_api_collection[api][name]))
    return res

def parse_recursion(event, api_name, api_response, partition, host_ip, key, res, logger, recursion=False, metric_prefix=""):
    resp_data = dict()
    if event is None:
        logger.debug("Event is None for API name '{}', key '{}', host '{}', partition '{}'. Skipping.".format(api_name, key, host_ip, partition))
        return
    if isinstance(event, dict) and "stats" not in event and "rate" not in event:
        for item in event:
            parse_recursion(event[item], api_name, api_response, partition, host_ip, key, res, logger, recursion=True, metric_prefix=metric_prefix)

    elif isinstance(event, dict) and "stats" in event:
        resp_data = event.get("stats", {})
        logger.debug("Stats found for API name '{}': {}".format(api_name, resp_data))
        if recursion:
            api_name_slash = event.get("a10-url", "")
            api_name = api_name_slash.replace("/axapi/v3", "")
            api_name = getLabelNameFromA10URL(api_name)
        res = generate_metrics(resp_data, api_name, partition, host_ip, key, res, metric_prefix=metric_prefix)

    elif isinstance(event, dict) and "rate" in event:
        resp_data = event.get("rate", {})
        logger.debug("Rate found for API name '{}': {}".format(api_name, resp_data))
        if recursion:
            api_name_slash = event.get("a10-url", "")
            api_name = api_name_slash.replace("/axapi/v3", "")
            api_name = getLabelNameFromA10URL(api_name)
        res = generate_metrics(resp_data, api_name, partition, host_ip, key, res, metric_prefix=metric_prefix)

    elif isinstance(event, list):
        for item in event:
            parse_recursion(item, api_name, api_response, partition, host_ip, key, res, logger, recursion=True, metric_prefix=metric_prefix)

    else:
        a10_url = event.get("a10-url", "unknown") if isinstance(event, dict) else "unknown"
        logger.error("Stats not found for API name '{}' with response {}. URL: {}".format(api_name, api_response, a10_url))
        logger.debug("Event structure: {}".format(json.dumps(event, indent=2)))
        # return "Stats not found for API name '{}' with response {}.".format(api_name, api_response)

    return res
