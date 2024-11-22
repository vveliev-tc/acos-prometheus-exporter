ARG PYTHON_VERSION=3.12
ARG BASE_IMAGE=slim-bookworm

FROM python:${PYTHON_VERSION}-${BASE_IMAGE}

RUN pip install --upgrade pip

WORKDIR /app

COPY src/acos_exporter.py /app/acos_exporter.py
COPY src/requirements.txt /app/requirements.txt
COPY build/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh

RUN pip3 install -r requirements.txt

EXPOSE 9734

LABEL service="a10-exporter"
LABEL org.opencontainers.image.source=https://github.com/vveliev-tc/acos-prometheus-exporter
LABEL org.opencontainers.image.description="A10 Networks Prometheus Exporter"

ENTRYPOINT ["/entrypoint.sh"]
