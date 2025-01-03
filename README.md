# ACOS Prometheus Exporter (vThunder)

The ACOS Prometheus Exporter module collects ACOS device statistics and creates gauge metrics for each stats field, exposing them on port 9734.

## Table of Contents

- [ACOS Prometheus Exporter (vThunder)](#acos-prometheus-exporter-vthunder)
  - [Table of Contents](#table-of-contents)
  - [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
      - [Running as a standalone script](#running-as-a-standalone-script)
      - [Running as a Docker container](#running-as-a-docker-container)
  - [Configuration](#configuration)
  - [Prometheus Configuration](#prometheus-configuration)
  - [Visualization with Grafana](#visualization-with-grafana)
  - [Additional Information](#additional-information)

## Getting Started

### Prerequisites

- Python 3.12
- Docker
- Prometheus (optional for scraping, alternatively otel-collector can be used)
- Grafana (optional for visualization)

### Installation

#### Running as a standalone script

1. Install the required Python packages using Pipenv:

    ```bash
    pipenv install --deploy
    ```

2. Run the exporter:

    ```bash
    pipenv run python src/acos_exporter.py
    ```

#### Running as a Docker container

1. Build and run the Docker container using Makefile:

    ```bash
    make sandbox
    ```

2. To inspect the logs:

    ```bash
    docker logs -f acos-prometheus-exporter
    ```

## Configuration

Refer to the example configuration file at `examples/config.yml` for setting up the exporter.

Configuration options:

- `hosts`: Dictionary of ACOS instances to be monitored with `host_ip`, `username`, and `password`.
- `log`: Logging configuration with `log_output`, `log_level`, and `log_filename`.

Application parameters that can overwrite the configuration file options:

- `LOG_LEVEL`: Set the logging level.
- `CONFIG_FILE`: Path to the configuration file.
- `METRIC_PREFIX`: Prefix for the metric names.
- `APIS_FILE`: Path to the file containing API endpoints.

## Prometheus Configuration

Refer to the example Prometheus configuration file at `examples/prometheus.yml` for setting up Prometheus to scrape metrics from the exporter.

## Visualization with Grafana

1. Add Prometheus as a data source in Grafana.
2. Create dashboards to visualize the metrics exposed by the exporter.

## Additional Information

Refer to the [Prometheus Querying](https://prometheus.io/docs/prometheus/latest/querying/basics/) documentation for more information on querying metrics.

For detailed documentation, refer to the [docs](docs/reference-implementation.md) folder.
