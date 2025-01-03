import json
import requests
from threading import Lock
from src.config import load_auth_config

API_TIMEOUT = 5

class ACOSClient:
    def __init__(self, config_file, logger):
        self.lock = Lock()
        self.tokens = dict()
        self.hosts_data = load_auth_config(config_file)
        self.logger = logger

    def get_valid_token(self, host_ip, to_call=False):
        self.lock.acquire()
        try:
            if host_ip not in self.hosts_data:
                self.logger.error("Host authentication configuration missing for host: {}".format(host_ip))
                raise ValueError("Host authentication configuration missing for host: {}".format(host_ip))
            
            if host_ip in self.tokens and not to_call:
                return self.tokens[host_ip]
            else:
                token = ""
                if host_ip not in self.tokens or to_call:
                    token = self.getauth(host_ip)
                if not token:
                    self.logger.error("Auth token not received.")
                    raise ValueError("Authentication token not received.")
                self.tokens[host_ip] = token
            return self.tokens[host_ip]
        finally:
            self.lock.release()

    def getauth(self, host):
        if host not in self.hosts_data:
            self.logger.error("Host credentials not found in creds config")
            return ''
        else:
            uname = self.hosts_data[host].get('username', '')
            pwd = self.hosts_data[host].get('password', '')
            if not uname:
                self.logger.error("username not provided.")
            if not pwd:
                self.logger.error("password not provided.")

            payload = {'Credentials': {'username': uname, 'password': pwd}}
            try:
                self.logger.debug("Sending authentication request to host: {}".format(host))
                auth_response = requests.post("https://{host}/axapi/v3/auth".format(host=host), json=payload,
                                              verify=False, timeout=API_TIMEOUT)
                self.logger.debug("Authentication response: {}".format(auth_response.content.decode('UTF-8')))
                auth = json.loads(auth_response.content.decode('UTF-8'))
            except requests.exceptions.Timeout:
                self.logger.error("Connection to {host} timed out. (connect timeout={timeout} secs)".format(host=host,
                                                                                                       timeout=API_TIMEOUT))
                return ''
            except requests.exceptions.RequestException as e:
                self.logger.error("Request exception: {}".format(str(e)))
                return ''

            if 'authresponse' not in auth:
                self.logger.error("Host credentials are not correct or authentication failed")
                return ''
            return 'A10 ' + auth['authresponse']['signature']

    def get(self, api_endpoints, endpoint, host_ip, headers):
        try:
            body = {
                "batch-get-list": list()
            }
            for api_endpoint in api_endpoints:
                body["batch-get-list"].append({"uri": "/axapi/v3" + api_endpoint})

            batch_endpoint = "/batch-get"
            self.logger.info("Uri - " + endpoint + batch_endpoint)
            response = json.loads(
                requests.post(endpoint + batch_endpoint, data=json.dumps(body), headers=headers, verify=False).content.decode('UTF-8'))
            self.logger.debug("AXAPI batch response - " + str(response))

            if 'response' in response and 'err' in response['response']:
                msg = response['response']['err']['msg']
                if str(msg).lower().__contains__("uri not found"):
                    self.logger.error("Request for api failed - batch-get" + ", response - " + msg)

                elif str(msg).lower().__contains__("unauthorized"):
                    token = self.get_valid_token(host_ip, True)
                    if token:
                        self.logger.info("Re-executing an api -", endpoint + batch_endpoint, " with the new token")
                        headers = {'content-type': 'application/json', 'Authorization': token}
                        response = json.loads(
                            requests.post(endpoint + batch_endpoint, data=json.dumps(body), headers=headers, verify=False).content.decode('UTF-8'))
                else:
                    self.logger.error("Unknown error message - ", msg)
        except Exception as e:
            self.logger.error("Exception caught - ", e)
            response = ""
        return response

    def get_partition(self, endpoint, headers):
        partition_endpoint = "/active-partition"
        response = json.loads(requests.get(endpoint + partition_endpoint, headers=headers, verify=False).content.decode('UTF-8'))
        return "partition - " + str(response)

    def change_partition(self, partition, endpoint, headers):
        partition_endpoint = "/active-partition/" + str(partition)
        self.logger.info("Uri - " + endpoint + partition_endpoint)
        try:
            requests.post(endpoint + partition_endpoint, headers=headers, verify=False)
        except Exception as e:
            self.logger.exception(e)
        self.logger.info("Partition changed to " + partition)
