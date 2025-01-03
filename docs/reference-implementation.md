# Reference Implementation of Monitoring Stack

The ACOS Prometheus Exporter module collects ACOS device statistics and creates gauge metrics for each stats field, exposing them on port 9734.

Users can:

- Configure the Exporter to communicate with multiple ACOS devices.
- Query any API stats configured in the Prometheus server’s YAML file.

## Architecture of the Prometheus setup

![picture](img/prometheus.png)

## Components of the solution

### 1) Exporter

- Custom exporter is a python script/container which:
  - Invokes ACOS axAPIs to fetch the stats fields.
  - Exposes the queried stats in the form of Prometheus metrics.
  - It follows the principle of URL intercepting. The URLs need to be specified in the Prometheus server’s configuration file. The specified axAPI is invoked as per the URL name.
  - Exporter creates a Gauge metrics for each stats field and exposes the same on the port 9734.

Sample config.yml snippet:

```yaml
---
hosts:
  <host_ip goes here>:
    username: <uname goes here>
    password: <pwd goes here>
log:
  log_file: logs.log
  log_level: INFO
```

- `host_ip`: ACOS instance IP which is to be monitored.
- `log_level`: Set log_level to DEBUG for debugging purposes. The default log_level is INFO.

### 2) Prometheus Server

Prometheus server is responsible for monitoring and continuous polling the stats filed that are exposed by the exporter.
It refers to the prometheus.yml configuration file for polling.
Prometheus server runs on port 9090 by default.
It can also send out the alerts to ITSM systems such as PagerDuty, ServiceNow, Slack, etc.

Sample prometheus.yml config snippet:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'acos-scraper-job'
    static_configs:
      - targets: ['localhost:9734']
    metrics_path: '/metrics'
    params:
      host_ip: ["10.43.12.122"]
      api_endpoint: ["/slb/dns", "/slb/virtual-server/10.10.10.2/port/80+tcp", "/slb/fix"]
      api_name: ["_slb_dns", "_slb_virtual_server_10.10.10.2_port_80_tcp", "_slb_fix"]
      partition: ["P1"]
```

- `scrape_interval`: Time interval for querying stats fields.
- `target`: Hostname and port that exporter is running on.
- `api_endpoint`: URI endpoint that exporter will intercept and invoke the appropriate axAPI. A comma-separated list of APIs can be provided here for a single host.
- `api_name`: API name is used to identify the API endpoint. Comma-separated list of api_name should be in sync with api_endpoint list.
- `partition`: Name of the partition. This is an optional parameter. If not specified, the shared partition will be used.

In this scenario, once the Prometheus server is started, it invokes a custom exporter after each 15 seconds, as specified in the scraping interval.
api_endpoint and api_name (unique identifier for a job) are passed to the exporter as parameters.
Exporter invokes axAPI for port and fetches the stats fields, creates gauge metrics for each stats field and exposes the metrics to the Prometheus server.

Sample prometheus.yml config snippet for automatic service discovery in Kubernetes:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'acos-scraper-job'
    kubernetes_sd_configs:
      - role: endpoints
        namespaces:
          names:
            - default
    relabel_configs:
      - source_labels: [__meta_kubernetes_service_name]
        action: keep
        regex: prometheus-exporter-svc
      - source_labels: [__meta_kubernetes_pod_host_ip]
        target_label: __address__
        replacement: ${1}:30101
    metrics_path: '/metrics'
    params:
      host_ip: ["10.43.12.122"]
      api_endpoint: ["/slb/dns"]
      api_name: ["_slb_dns"]
```

### 3) Visualization tool

- Prometheus UI runs on port 9090 by default.
  - It has an in-built visualization functionality that displays the metrics information exposed by the exporter.
  - User can select the targets and get all metrics for an endpoint or can search for a specific metric by querying using Prometheus query language expression.
- The same metrics can be visualized in a graphical form by using visualization tools like Grafana.
  - A data source needs to be added as Prometheus in order to display metrics in graphical form in Grafana.
  - A metric can be queried by entering the stats field name in the query box (either in Prometheus query page or Grafana). e.g., "curr_proxy", "total_fwd_bytes" etc.
  - Refer to [Prometheus Querying](https://prometheus.io/docs/prometheus/latest/querying/basics/) for more information.

### 4) Alerting

- Prometheus server can send out alerts to ITSM systems like PagerDuty, ServiceNow, Slack, etc.
- Alerts can be configured in the Prometheus server configuration file.

Sample alerting rule in prometheus.yml:

```yaml

groups:
  - name: example
    rules:
      - alert: HighRequestRate
        expr: sum(rate(http_requests_total{job="myjob"}[5m])) > 100
        for: 10m
        labels:
          severity: page
        annotations:
          summary: High request rate
```

## Supported Endpoints

Refer to the `docs/supported_endpoint_list/5.2.1-P6/rate_endpoint_list.txt` file for a list of supported endpoints.
