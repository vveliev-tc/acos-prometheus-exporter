from flask import current_app, Blueprint, request, Response, jsonify
import urllib3
from acos_client.client import ACOSClient
from acos_exporter import getLabelNameFromA10URL, parse_recursion  # Import the functions

metrics_bp = Blueprint('metrics', __name__)

@metrics_bp.route("/")
def default():
    return "Please provide /metrics?query-params!"

@metrics_bp.route("/metrics")
def generic_exporter():
    logger = current_app.logger
    config_file = current_app.config['CONFIG_FILE']
    apis_file = current_app.config['APIS_FILE']
    logger.debug("---------------------------------------------------------------------------------------------------")
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    host_ip = request.args.get("host_ip", "")
    api_endpoints = request.args.getlist("api_endpoint")
    metric_prefix = request.args.get("metric_prefix", current_app.config['METRIC_PREFIX'])
    
    if not api_endpoints:
        try:
            with open(apis_file) as file:
                default_endpoint = [endpoint.strip() for endpoint in file.readlines()]
            api_endpoints = default_endpoint
            logger.error("api_endpoint are of default")
        except FileNotFoundError:
            logger.error("default_api_endpoints.txt file not found and no api_endpoints provided. The api_endpoint field is required to get metrics.")
            return jsonify(error="default_api_endpoints.txt file not found and no api_endpoints provided. The api_endpoint field is required to get metrics."), 400

    api_names = getLabelNameFromA10URL(api_endpoints)
    partition = request.args.get("partition", "shared")
    res = []
    
    if not host_ip:
        logger.error("host_ip is required. Exiting API endpoints - {}".format(api_endpoints))
        return jsonify(error="host_ip is required. Exiting API endpoints - {}".format(api_endpoints)), 400

    logger.info("Host = " + host_ip + "\t" + "API = " + str(api_names))
    logger.info("Endpoint = " + str(api_endpoints))
    
    acos_client = ACOSClient(config_file, logger)
    try:
        token = acos_client.get_valid_token(host_ip)
    except ValueError as e:
        logger.error(str(e))
        return jsonify(error=str(e)), 401
    
    endpoint = "https://{host_ip}/axapi/v3".format(host_ip=host_ip)
    headers = {'content-type': 'application/json', 'Authorization': token}

    logger.debug(acos_client.get_partition(endpoint, headers))
    
    try:
        if "shared" not in partition:
            acos_client.change_partition(partition, endpoint, headers)
        response = acos_client.get(api_endpoints, endpoint, host_ip, headers)
        logger.debug("API response: {}".format(response))
    finally:
        if "shared" not in partition:
            acos_client.change_partition("shared", endpoint, headers)

    if not response:
        logger.error("Empty response received from ACOS client.")
        return jsonify(error="Empty response received from ACOS client."), 500

    api_counter = 0
    batch_list = response.get("batch-get-list", [])
    
    if not batch_list:
        logger.error("No batch-get-list found in the response.")
        return jsonify(error="No batch-get-list found in the response."), 500

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
            logger.debug("Processing event for key: {} with event: {}".format(key, event))
            res = parse_recursion(event, api_name, api_response, partition, host_ip, key, res, logger, metric_prefix=metric_prefix)
        except Exception as ex:
            logger.exception(ex.args[0])
            return jsonify(error="Error processing API endpoint: {}".format(api_endpoint)), 500
    
    if not res:
        logger.error("No metrics generated.")
        return jsonify(error="No metrics generated."), 500

    logger.debug("Final Response - " + str(res))
    return Response(res, mimetype="text/plain")
