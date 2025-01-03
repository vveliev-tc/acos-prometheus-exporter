import unittest
from unittest.mock import patch, MagicMock
from flask import Flask
from src import create_app
import os

class TestACOSExporter(unittest.TestCase):

    def setUp(self):
        os.environ['CONFIG_FILE'] = '/app/tests/config.yml'
        os.environ['APIS_FILE'] = '/app/tests/default_api_endpoints.txt'
        self.app = create_app('development').test_client()
        self.app.testing = True

    def test_default_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data.decode(), "Please provide /metrics?query-params!")

    def test_metrics_route_no_params(self):
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 400)
        self.assertIn("default_api_endpoints.txt file not found and no api_endpoints provided. The api_endpoint field is required to get metrics.", response.data.decode())

    def test_metrics_route_no_params_with_src_apis_file(self):
        os.environ['APIS_FILE'] = '/app/src/default_api_endpoints.txt'
        self.app = create_app('development').test_client()  # Recreate the app with the new environment variable
        response = self.app.get('/metrics')
        self.assertEqual(response.status_code, 400)
        self.assertIn("host_ip is required. Default API endpoints", response.data.decode())

    @patch('src.views.metrics.ACOSClient')
    def test_metrics_route_with_host_ip(self, MockACOSClient):
        mock_client_instance = MockACOSClient.return_value
        mock_client_instance.get_valid_token.return_value = 'mock_token'
        mock_client_instance.get.return_value = {
            "batch-get-list": [{"resp": {"stats": {"key": "value"}}}]
        }

        os.environ['APIS_FILE'] = '/app/src/default_api_endpoints.txt'
        self.app = create_app('development').test_client()  # Recreate the app with the new environment variable
        response = self.app.get('/metrics?host_ip=127.0.0.1')
        self.assertEqual(response.status_code, 200)
        self.assertIn("key", response.data.decode())  # Add additional assertions based on the expected response

if __name__ == '__main__':
    unittest.main()