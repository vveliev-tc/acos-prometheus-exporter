import json
import yaml
import sys
import argparse
from threading import Lock

import prometheus_client
import requests
import urllib3
from flask import Response, Flask, request
from prometheus_client import Gauge

from config_loader import load_configuration
from acos_client.client import ACOSClient


UNDERSCORE = "_"
SLASH = "/"
HYPHEN = "-"
PLUS = "+"

API_TIMEOUT = 5

global_api_collection = dict()
global_stats = dict()

app = Flask(__name__)

_INF = float("inf")

lock1 = Lock()
tokens = dict()

def parse_arguments():
    parser = argparse.ArgumentParser(description='ACOS Prometheus Exporter')
    parser.add_argument('-c', '--config', type=str, default='config.yml', help='Path to the configuration file')
    parser.add_argument('-l', '--log', type=str, default='INFO', help='Log level, this will override the log level in the config file')
    return parser.parse_args()


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


@app.route("/")
def default():
    return "Please provide /metrics?query-params!"


def generate_metrics(resp_data, api_name, partition, host_ip, key, res):
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
        if key not in global_stats:
            current_api_stats[key] = Gauge(key, "api-" + api + "key-" + key,
                                           labelnames=(["api_name", "partition", "host"]), )
            current_api_stats[key].labels(api_name=api, partition=partition, host=host_ip).set(resp_data[org_key])
            global_stats[key] = current_api_stats[key]
        elif key in global_stats:
            global_stats[key].labels(api_name=api, partition=partition, host=host_ip).set(resp_data[org_key])

    global_api_collection[api] = current_api_stats

    for name in global_api_collection[api]:
        res.append(prometheus_client.generate_latest(global_api_collection[api][name]))
    return res


def parse_recursion(event, api_name, api_response, partition, host_ip, key, res, recursion=False):
    resp_data = dict()
    if event is None:
        return
    if type(event) == dict and "stats" not in event and "rate" not in event:
        for item in event:
            parse_recursion(event[item], api_name, api_response, partition, host_ip, key, res, recursion=True)

    elif type(event) == dict and "stats" in event:
        resp_data = event.get("stats", {})
        if recursion:
            api_name_slash = event.get("a10-url", "")
            api_name = api_name_slash.replace("/axapi/v3", "")
            api_name = getLabelNameFromA10URL(api_name)
        res = generate_metrics(resp_data, api_name, partition, host_ip, key, res)

    elif type(event) == dict and "rate" in event:
        resp_data = event.get("rate", {})
        if recursion:
            api_name_slash = event.get("a10-url", "")
            api_name = api_name_slash.replace("/axapi/v3", "")
            api_name = getLabelNameFromA10URL(api_name)
        res = generate_metrics(resp_data, api_name, partition, host_ip, key, res)

    else:
        logger.error("Stats not found for API name '{}' with response {}.".format(api_name, api_response))
        # return "Stats not found for API name '{}' with response {}.".format(api_name, api_response)

    return res


@app.route("/metrics")
def generic_exporter():
    logger.debug("---------------------------------------------------------------------------------------------------")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    host_ip = request.args.get("host_ip", "")
    api_endpoints = request.args.getlist("api_endpoint")
    if not api_endpoints:
        with open("apis.txt") as file:
            default_endpoint = file.readlines()
            default_endpoint = [endpoint.strip() for endpoint in default_endpoint]
        api_endpoints = default_endpoint
        logger.error("api_endpoint are of default")

    api_names = getLabelNameFromA10URL(api_endpoints)
    partition = request.args.get("partition", "shared")
    res = []
    if not host_ip:
        logger.error("host_ip is required. Exiting API endpoints - {}".format(api_endpoints))
        return "host_ip is required. Exiting API endpoints - {}".format(api_endpoints)

    logger.info("Host = " + host_ip + "\t" +
                "API = " + str(api_names))
    logger.info("Endpoint = " + str(api_endpoints))
    
    acos_client = ACOSClient(config_file, logger)
    token = acos_client.get_valid_token(host_ip)
    if not token:
        return "Authentication token not received."
    endpoint = "https://{host_ip}/axapi/v3".format(host_ip=host_ip)
    headers = {'content-type': 'application/json', 'Authorization': token}

    logger.debug(acos_client.get_partition(endpoint, headers))
    if "shared" not in partition:
        try:
            acos_client.change_partition(partition, endpoint, headers)
            response = acos_client.get(api_endpoints, endpoint, host_ip, headers)
        finally:
            acos_client.change_partition("shared", endpoint, headers)
    else:
        response = acos_client.get(api_endpoints, endpoint, host_ip, headers)

    api_counter = 0
    batch_list = response.get("batch-get-list", [])
    for response in batch_list:
        api_endpoint = api_endpoints[api_counter]
        api_name = api_names[api_counter]
        logger.debug("name = " + api_name)
        api_response = response.get("resp", {})
        logger.debug("API \"{}\" Response - {}".format(api_name, str(api_response)))
        api_counter += 1
        try:
            key = list(api_response.keys())[0]
            event = api_response.get(key, {})
            res = parse_recursion(event, api_name, api_response, partition, host_ip, key, res)

        except Exception as ex:
            logger.exception(ex.args[0])
            return api_endpoint + " has something missing."
    logger.debug("Final Response - " + str(res))
    return Response(res, mimetype="text/plain")


def main():
    app.run(debug=True, port=9734, host='0.0.0.0')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ACOS Prometheus Exporter')
    parser.add_argument('-c', '--config', type=str, default='config.yml', help='Path to the configuration file')
    parser.add_argument('-l', '--log', type=str, default='INFO', help='Log level, this will override the log level in the config file')
    args = parser.parse_args()
    config_file = args.config

    try:
        args = parse_arguments()
        config_file = args.config
        log_level_override = args.log

        logger = load_configuration(app, config_file, log_level_override)
        main()
    except Exception as e:
        print(e)
        sys.exit()
